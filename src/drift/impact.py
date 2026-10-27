"""Avalia o impacto do data drift no desempenho e decisoes do modelo em producao."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

from src.data.schema import FEATURE_COLUMNS, TARGET_COLUMN

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "logistic_regression.joblib"
BASE_PATH = PROJECT_ROOT / "data" / "production" / "production_base.csv"
DRIFTED_PATH = PROJECT_ROOT / "data" / "production" / "production_drifted.csv"
REPORT_PATH = PROJECT_ROOT / "reports" / "drift_impact_summary.json"


def evaluate_dataset(pipeline, df: pd.DataFrame) -> dict:
    """Roda a predicao e calcula metricas para um DataFrame."""
    x = df[FEATURE_COLUMNS]
    y_true = df[TARGET_COLUMN]

    # Predicoes de classe (0 ou 1) e probabilidades contínuas
    y_pred = pipeline.predict(x)
    y_prob = pipeline.predict_proba(x)[:, 1]

    return {
        "total_clients": len(df),
        "predicted_defaults": int((y_pred == 1).sum()),
        "predicted_default_rate": float((y_pred == 1).mean()),
        "mean_default_probability": float(np.mean(y_prob)),
        "metrics": {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_true, y_prob)),
        },
    }


def main() -> None:
    print(f"1. Carregando modelo de: {MODEL_PATH.name}...")
    pipeline = joblib.load(MODEL_PATH)

    print("2. Carregando dados de producao (Base vs Drifted)...")
    df_base = pd.read_csv(BASE_PATH)
    df_drifted = pd.read_csv(DRIFTED_PATH)

    print("3. Avaliando impacto do drift...")
    base_res = evaluate_dataset(pipeline, df_base)
    drifted_res = evaluate_dataset(pipeline, df_drifted)

    # Exibe a comparacao no terminal
    print("\n" + "=" * 65)
    print("      COMPARAÇÃO DE IMPACTO: PRODUÇÃO NORMAL vs DRIFT")
    print("=" * 65)
    print(f"{'Métrica':<30} | {'Base (Sem Drift)':<15} | {'Com Drift':<15}")
    print("-" * 65)
    print(
        f"{'Taxa de Inadimplência Prevista':<30} | "
        f"{base_res['predicted_default_rate']:<15.2%} | "
        f"{drifted_res['predicted_default_rate']:<15.2%}"
    )
    print(
        f"{'Probabilidade Média (Score)':<30} | "
        f"{base_res['mean_default_probability']:<15.4f} | "
        f"{drifted_res['mean_default_probability']:<15.4f}"
    )
    print(
        f"{'Acurácia':<30} | "
        f"{base_res['metrics']['accuracy']:<15.4f} | "
        f"{drifted_res['metrics']['accuracy']:<15.4f}"
    )
    print(
        f"{'Precisão':<30} | "
        f"{base_res['metrics']['precision']:<15.4f} | "
        f"{drifted_res['metrics']['precision']:<15.4f}"
    )
    print(
        f"{'Recall':<30} | "
        f"{base_res['metrics']['recall']:<15.4f} | "
        f"{drifted_res['metrics']['recall']:<15.4f}"
    )
    print(
        f"{'F1-Score':<30} | "
        f"{base_res['metrics']['f1']:<15.4f} | "
        f"{drifted_res['metrics']['f1']:<15.4f}"
    )
    print("=" * 65)

    # Salva o relatorio em JSON
    summary = {
        "model": MODEL_PATH.name,
        "base_production": base_res,
        "drifted_production": drifted_res,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nResumo do impacto salvo em: {REPORT_PATH}")


if __name__ == "__main__":
    main()
