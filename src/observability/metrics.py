"""Agregador de metricas de observabilidade do pipeline.

Le os relatorios JSON gerados por cada etapa (treino, avaliacao, simulacao
de drift, deteccao de drift, impacto do drift) e os alertas registrados em
`reports/alerts.json`, compondo uma unica visao de saude do pipeline em
`reports/observability_summary.json`. Essa visao e a fonte de dados do
dashboard (`src/observability/dashboard.py`).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.observability.logging_config import setup_logging

logger = setup_logging(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"
LOG_FILE_PATH = PROJECT_ROOT / "logs" / "pipeline.log"
SUMMARY_PATH = REPORTS_DIR / "observability_summary.json"

TRAINING_SUMMARY_PATH = REPORTS_DIR / "training_summary.json"
BASELINE_METRICS_PATH = REPORTS_DIR / "baseline_metrics.json"
DRIFT_SIMULATION_PATH = REPORTS_DIR / "drift_simulation.json"
DRIFT_REPORT_PATH = REPORTS_DIR / "data_drift_report.json"
DRIFT_IMPACT_PATH = REPORTS_DIR / "drift_impact_summary.json"
ALERTS_PATH = REPORTS_DIR / "alerts.json"

DRIFT_VALUE_METRIC_TYPE = "evidently:metric_v2:ValueDrift"
DRIFTED_COLUMNS_COUNT_METRIC_TYPE = "evidently:metric_v2:DriftedColumnsCount"


def _load_json(path: Path) -> Any | None:
    """Carrega um JSON se o arquivo existir; caso contrario, retorna None."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _stage_status(data: dict | None, key_fields: dict[str, str]) -> dict[str, Any]:
    """Monta o bloco de status de uma etapa a partir dos campos do seu relatorio.

    Args:
        data: Conteudo do relatorio JSON da etapa, ou None se ainda nao foi gerado.
        key_fields: Mapa {nome_no_resumo: nome_no_relatorio} dos campos a copiar.
    """
    if data is None:
        return {"status": "missing"}

    status: dict[str, Any] = {"status": "ok"}
    for label, field in key_fields.items():
        status[label] = data.get(field)
    return status


def summarize_log_counts() -> dict[str, int]:
    """Conta as mensagens de log por nivel em logs/pipeline.log."""
    counts = {"INFO": 0, "WARNING": 0, "ERROR": 0}

    if not LOG_FILE_PATH.exists():
        return counts

    for line in LOG_FILE_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        level = record.get("level")
        if level in counts:
            counts[level] += 1

    return counts


def summarize_drift(drift_report: dict | None) -> dict[str, Any]:
    """Extrai a contagem de colunas degradadas e quais ultrapassaram o limiar."""
    if drift_report is None:
        return {"status": "missing"}

    drifted_columns = []
    drifted_count = None
    drifted_share = None

    for metric in drift_report.get("metrics", []):
        config = metric.get("config", {})
        metric_type = config.get("type")

        if metric_type == DRIFTED_COLUMNS_COUNT_METRIC_TYPE:
            value = metric.get("value", {})
            drifted_count = value.get("count")
            drifted_share = value.get("share")
        elif metric_type == DRIFT_VALUE_METRIC_TYPE:
            value = metric.get("value")
            threshold = config.get("threshold")
            if value is not None and threshold is not None and value > threshold:
                drifted_columns.append(config.get("column"))

    return {
        "status": "ok",
        "drifted_columns_count": drifted_count,
        "drifted_columns_share": drifted_share,
        "columns_above_threshold": drifted_columns,
    }


def summarize_alerts(alerts: list[dict] | None) -> dict[str, Any]:
    """Conta os alertas registrados, agrupados por tipo."""
    if not alerts:
        return {"total": 0, "by_type": {}}

    by_type: dict[str, int] = {}
    for alert in alerts:
        alert_type = alert.get("type", "unknown")
        by_type[alert_type] = by_type.get(alert_type, 0) + 1

    return {"total": len(alerts), "by_type": by_type}


def build_summary() -> dict[str, Any]:
    """Monta o dicionario completo de observabilidade a partir dos relatorios disponiveis."""
    training = _load_json(TRAINING_SUMMARY_PATH)
    evaluation = _load_json(BASELINE_METRICS_PATH)
    drift_simulation = _load_json(DRIFT_SIMULATION_PATH)
    drift_report = _load_json(DRIFT_REPORT_PATH)
    drift_impact = _load_json(DRIFT_IMPACT_PATH)
    alerts = _load_json(ALERTS_PATH) or []

    pipeline_stages = {
        "train": _stage_status(
            training,
            {"trained_at_utc": "trained_at_utc", "training_rows": "training_rows"},
        ),
        "evaluate": _stage_status(
            evaluation,
            {"evaluated_at_utc": "evaluated_at_utc", "test_rows": "test_rows"},
        ),
        "drift_simulation": _stage_status(
            drift_simulation,
            {"generated_at_utc": "generated_at_utc", "rows": "rows"},
        ),
        "drift_detection": summarize_drift(drift_report),
        "drift_impact": _stage_status(drift_impact, {"model": "model"}),
    }

    model_metrics = {}
    if evaluation:
        model_metrics = {
            name: result["metrics"] for name, result in evaluation.get("models", {}).items()
        }

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "pipeline_stages": pipeline_stages,
        "log_counts": summarize_log_counts(),
        "model_metrics": model_metrics,
        "alerts": summarize_alerts(alerts),
    }


def main() -> None:
    logger.info(
        "Agregando metricas de observabilidade",
        extra={"event": "metrics_aggregation_started"},
    )

    summary = build_summary()

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Resumo de observabilidade salvo em: {SUMMARY_PATH}")

    logger.info(
        "Agregacao de metricas concluida",
        extra={
            "event": "metrics_aggregation_completed",
            "data": {
                "report_path": str(SUMMARY_PATH),
                "alerts_total": summary["alerts"]["total"],
            },
        },
    )


if __name__ == "__main__":
    main()
