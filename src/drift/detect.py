"""Detecta data drift comparando a base de referencia com producao usando Evidently."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset

from src.data.schema import FEATURE_COLUMNS

# 1. Caminhos do projeto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PATH = PROJECT_ROOT / "data" / "reference" / "reference.csv"
CURRENT_PATH = PROJECT_ROOT / "data" / "production" / "production_drifted.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"


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
    print("1. Carregando datasets...")
    reference_df, current_df = load_datasets()

    print("2. Calculando testes estatisticos de drift...")
    report = run_drift_report(reference_df, current_df)

    print("3. Salvando artefatos...")
    save_reports(report)
    print("\nDetecção concluída com sucesso!")


if __name__ == "__main__":
    main()
