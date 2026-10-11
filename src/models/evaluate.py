"""Avalia os pipelines salvos usando exclusivamente o conjunto de teste."""

import hashlib
import json
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.data.schema import COLUMN_MAPPING, FEATURE_COLUMNS, TARGET_COLUMN

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "reports"
TEST_PATH = PROJECT_ROOT / "data/test/test.csv"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_markdown(report: dict) -> None:
    lines = [
        "# Avaliacao inicial dos modelos",
        "",
        f"Conjunto: teste. Registros: {report['test_rows']}.",
        "",
        "Classe positiva: 1 (inadimplencia).",
        "Previsoes obtidas com predict, sem ajuste de limiar no teste.",
        "Precision sem previsoes positivas e registrada como zero por convencao.",
        "",
        "| Modelo | Acuracia | Precision | Recall | F1 | ROC AUC |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for name, result in report["models"].items():
        metrics = result["metrics"]
        lines.append(
            f"| {name} | {metrics['accuracy']:.4f} "
            f"| {metrics['precision']:.4f} | {metrics['recall']:.4f} "
            f"| {metrics['f1']:.4f} | {metrics['roc_auc']:.4f} |"
        )

    for name, result in report["models"].items():
        matrix = result["confusion_matrix"]
        lines.extend(
            [
                "",
                f"## Matriz de confusao de {name}",
                "",
                "| Classe real | Previsto 0 | Previsto 1 |",
                "|---|---:|---:|",
                f"| Real 0 | {matrix[0][0]} | {matrix[0][1]} |",
                f"| Real 1 | {matrix[1][0]} | {matrix[1][1]} |",
            ]
        )

    lines.extend(
        [
            "",
            "## Limites da avaliacao",
            "",
            "Esta avaliacao usa dados historicos separados por grupos de perfis.",
            "Nao representa validacao temporal nem autorizacao para uso real.",
            "O conjunto de producao simulada nao foi utilizado.",
            "",
        ]
    )

    (REPORTS_DIR / "baseline_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    training = json.loads((REPORTS_DIR / "training_summary.json").read_text(encoding="utf-8"))
    split = json.loads((REPORTS_DIR / "split_summary.json").read_text(encoding="utf-8"))

    if version("scikit-learn") != training["versions"]["scikit-learn"]:
        raise ValueError("Use a mesma versao de scikit-learn do treinamento.")

    if training["reference_sha256"] != split["splits"]["reference"]["sha256"]:
        raise ValueError("O treinamento e a separacao usam referencias diferentes.")

    test_hash = file_hash(TEST_PATH)

    if test_hash != split["splits"]["test"]["sha256"]:
        raise ValueError("O conjunto de teste difere do manifesto da separacao.")

    data = pd.read_csv(TEST_PATH)

    if data.columns.tolist() != list(COLUMN_MAPPING.values()):
        raise ValueError("As colunas do teste diferem do schema.")

    if len(data) != split["splits"]["test"]["rows"]:
        raise ValueError("Quantidade inesperada de registros no teste.")

    if data.isna().any().any():
        raise ValueError("O teste possui valores nulos.")

    if set(data[TARGET_COLUMN].unique()) != {0, 1}:
        raise ValueError("O teste deve conter as classes 0 e 1.")

    x_test = data[FEATURE_COLUMNS]
    y_test = data[TARGET_COLUMN]

    report = {
        "evaluated_at_utc": datetime.now(UTC).isoformat(),
        "test_rows": len(data),
        "test_sha256": test_hash,
        "training_summary_sha256": file_hash(REPORTS_DIR / "training_summary.json"),
        "positive_class": 1,
        "prediction_rule": "pipeline.predict; no threshold tuning",
        "zero_division": 0,
        "models": {},
    }

    for name in ("logistic_regression", "dummy"):
        info = training["models"][name]
        model_path = PROJECT_ROOT / info["artifact"]

        if file_hash(model_path) != info["artifact_sha256"]:
            raise ValueError(f"O artefato de {name} difere do treinamento.")

        # Carrega somente o artefato local gerado pelo nosso treinamento.
        pipeline = joblib.load(model_path)

        if list(pipeline.classes_) != [0, 1]:
            raise ValueError(f"Classes inesperadas no modelo {name}.")

        predictions = pipeline.predict(x_test)
        probabilities = pipeline.predict_proba(x_test)[:, 1]

        if not np.isfinite(probabilities).all():
            raise ValueError(f"Probabilidades nao finitas em {name}.")

        if ((probabilities < 0) | (probabilities > 1)).any():
            raise ValueError(f"Probabilidades fora de [0, 1] em {name}.")

        metrics = {
            "accuracy": float(accuracy_score(y_test, predictions)),
            "precision": float(precision_score(y_test, predictions, pos_label=1, zero_division=0)),
            "recall": float(recall_score(y_test, predictions, pos_label=1, zero_division=0)),
            "f1": float(f1_score(y_test, predictions, pos_label=1, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, probabilities)),
        }

        matrix = confusion_matrix(y_test, predictions, labels=[0, 1])

        report["models"][name] = {
            "artifact": info["artifact"],
            "artifact_sha256": info["artifact_sha256"],
            "metrics": metrics,
            "confusion_matrix": matrix.tolist(),
            "confusion_matrix_labels": [0, 1],
            "predicted_positive_count": int((predictions == 1).sum()),
        }

        print(f"\nMODELO: {name}")
        for metric, value in metrics.items():
            print(f"{metric}: {value:.4f}")

        print("Matriz: linhas = classe real; colunas = classe prevista [0, 1]")
        print(matrix)

    (REPORTS_DIR / "baseline_metrics.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    write_markdown(report)

    print("\nRelatorios gerados:")
    print(REPORTS_DIR / "baseline_metrics.json")
    print(REPORTS_DIR / "baseline_report.md")


if __name__ == "__main__":
    main()
