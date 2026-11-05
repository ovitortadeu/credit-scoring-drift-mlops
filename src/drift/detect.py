"""Detecta data drift comparando a base de referencia com producao usando Evidently."""

from __future__ import annotations

import json
from pathlib import Path

import mlflow
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

from src.data.schema import FEATURE_COLUMNS
from src.observability.alerts import check_drift_alerts, save_alerts
from src.observability.logging_config import setup_logging
from src.observability.tracking import configure_mlflow

logger = setup_logging(__name__)

# 1. Caminhos do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PATH = PROJECT_ROOT / "data" / "reference" / "reference.csv"
CURRENT_PATH = PROJECT_ROOT / "data" / "production" / "production_drifted.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"
MLFLOW_EXPERIMENT = "credit-scoring-drift"
DRIFTED_COLUMNS_COUNT_METRIC_TYPE = "evidently:metric_v2:DriftedColumnsCount"


def load_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carrega as bases de referencia e producao selecionando apenas as features."""
    reference_df = pd.read_csv(REFERENCE_PATH)[FEATURE_COLUMNS]
    current_df = pd.read_csv(CURRENT_PATH)[FEATURE_COLUMNS]
    return reference_df, current_df


def run_drift_report(reference_df: pd.DataFrame, current_df: pd.DataFrame):
    """Executa o calculo de drift comparando as duas distribuicoes."""
    report = Report(metrics=[DataDriftPreset()])
    return report.run(reference_data=reference_df, current_data=current_df)


def save_reports(report_result) -> None:
    """Salva os relatorios em formato HTML (visual) e JSON (automacao)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    html_path = REPORTS_DIR / "data_drift_report.html"
    json_path = REPORTS_DIR / "data_drift_report.json"

    # Salva o dashboard interativo em HTML
    report_result.save_html(str(html_path))

    # Salva o JSON estruturado
    report_result.save_json(str(json_path))

    print(f"Relatório visual salvo em: {html_path}")
    print(f"Relatório JSON salvo em: {json_path}")


def main() -> None:
    logger.info("Iniciando deteccao de drift", extra={"event": "drift_detection_started"})
    configure_mlflow(MLFLOW_EXPERIMENT)

    print("1. Carregando datasets...")
    reference_df, current_df = load_datasets()

    print("2. Calculando testes estatisticos de drift...")
    report = run_drift_report(reference_df, current_df)

    print("3. Salvando artefatos...")
    save_reports(report)
    print("\nDetecção concluída com sucesso!")

    logger.info(
        "Deteccao de drift concluida",
        extra={
            "event": "drift_detection_completed",
            "data": {
                "reference_rows": len(reference_df),
                "current_rows": len(current_df),
                "report_path": str(REPORTS_DIR / "data_drift_report.json"),
            },
        },
    )

    print("4. Avaliando regras de alerta...")
    report_dict = json.loads((REPORTS_DIR / "data_drift_report.json").read_text(encoding="utf-8"))
    alerts = check_drift_alerts(report_dict)
    save_alerts(alerts)
    print(f"Alertas de drift gerados: {len(alerts)}")

    with mlflow.start_run(run_name="drift-detection"):
        mlflow.log_param("reference_rows", len(reference_df))
        mlflow.log_param("current_rows", len(current_df))

        for metric in report_dict.get("metrics", []):
            if metric.get("config", {}).get("type") == DRIFTED_COLUMNS_COUNT_METRIC_TYPE:
                value = metric.get("value", {})
                mlflow.log_metric("drifted_columns_count", value.get("count", 0))
                mlflow.log_metric("drifted_columns_share", value.get("share", 0))

        mlflow.log_metric("alerts_raised", len(alerts))
        mlflow.log_artifact(str(REPORTS_DIR / "data_drift_report.json"))
        if (REPORTS_DIR / "data_drift_report.html").exists():
            mlflow.log_artifact(str(REPORTS_DIR / "data_drift_report.html"))


if __name__ == "__main__":
    main()
