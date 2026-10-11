"""Treina os modelos baseline usando somente o conjunto de referencia."""

import hashlib
import json
import platform
import warnings
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.data.preprocessing import build_preprocessor
from src.data.schema import COLUMN_MAPPING, FEATURE_COLUMNS, ID_COLUMN, TARGET_COLUMN

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_PATH = PROJECT_ROOT / "data/reference/reference.csv"
SPLIT_REPORT_PATH = PROJECT_ROOT / "reports/split_summary.json"
MODELS_DIR = PROJECT_ROOT / "models"
TRAINING_REPORT_PATH = PROJECT_ROOT / "reports/training_summary.json"


def build_models() -> dict[str, Pipeline]:
    """Cria pipelines independentes, ainda nao treinados."""
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                (
                    "classifier",
                    LogisticRegression(
                        solver="lbfgs",
                        C=1.0,
                        max_iter=2000,
                        tol=0.0001,
                        class_weight=None,
                    ),
                ),
            ]
        ),
        "dummy": Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                ("classifier", DummyClassifier(strategy="most_frequent")),
            ]
        ),
    }


def main() -> None:
    split_report = json.loads(SPLIT_REPORT_PATH.read_text(encoding="utf-8"))
    reference_hash = hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest()
    expected = split_report["splits"]["reference"]

    if reference_hash != expected["sha256"]:
        raise ValueError("A referencia foi alterada desde a separacao.")

    data = pd.read_csv(REFERENCE_PATH)

    if data.columns.tolist() != list(COLUMN_MAPPING.values()):
        raise ValueError("As colunas da referencia diferem do schema.")

    if len(data) != expected["rows"]:
        raise ValueError("Quantidade inesperada de registros na referencia.")

    if data.isna().any().any():
        raise ValueError("A referencia possui valores nulos.")

    if data[ID_COLUMN].duplicated().any():
        raise ValueError("A referencia possui IDs repetidos.")

    if set(data[TARGET_COLUMN].unique()) != {0, 1}:
        raise ValueError("O alvo deve conter as classes 0 e 1.")

    # Seleciona explicitamente as features, excluindo ID e alvo.
    x_train = data[FEATURE_COLUMNS]
    y_train = data[TARGET_COLUMN]

    report = {
        "trained_at_utc": datetime.now(UTC).isoformat(),
        "training_dataset": "reference",
        "training_rows": len(data),
        "reference_sha256": reference_hash,
        "features": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
        "positive_class": 1,
        "evaluation_performed": False,
        "versions": {
            "python": platform.python_version(),
            "scikit-learn": version("scikit-learn"),
            "pandas": version("pandas"),
            "numpy": version("numpy"),
            "scipy": version("scipy"),
            "joblib": version("joblib"),
        },
        "models": {},
    }

    models = build_models()

    # Treina ambos antes de gravar os artefatos.
    for name, pipeline in models.items():
        print(f"Treinando: {name}...")
        started = perf_counter()

        # Interrompe se a regressao nao convergir.
        with warnings.catch_warnings():
            warnings.simplefilter("error", ConvergenceWarning)
            pipeline.fit(x_train, y_train)

        elapsed = perf_counter() - started
        classifier = pipeline.named_steps["classifier"]

        report["models"][name] = {
            "training_seconds": elapsed,
            "classifier_params": classifier.get_params(),
            "classes": classifier.classes_.tolist(),
            "transformed_features": (
                pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()
            ),
        }

        if hasattr(classifier, "n_iter_"):
            report["models"][name]["iterations"] = classifier.n_iter_.tolist()

        print(f"Treinamento concluido em {elapsed:.2f} segundos.")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for name, pipeline in models.items():
        model_path = MODELS_DIR / f"{name}.joblib"
        joblib.dump(pipeline, model_path)

        report["models"][name]["artifact"] = model_path.relative_to(PROJECT_ROOT).as_posix()
        report["models"][name]["artifact_sha256"] = hashlib.sha256(
            model_path.read_bytes()
        ).hexdigest()

        print(f"Pipeline salvo em: {model_path}")

    TRAINING_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRAINING_REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"\nRegistros utilizados: {len(data)}")
    print(f"Features de entrada: {len(FEATURE_COLUMNS)}")
    print(f"Resumo salvo em: {TRAINING_REPORT_PATH}")
    print("Treinamento concluido. Avaliacao ainda nao realizada.")


if __name__ == "__main__":
    main()
