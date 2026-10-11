"""Verifica que salvar e recarregar preserva a inferencia dos pipelines."""

import joblib
import numpy as np
import pandas as pd
import pytest

from src.data.schema import FEATURE_COLUMNS
from src.models.train import build_models


@pytest.mark.parametrize("model_name", ["logistic_regression", "dummy"])
def test_serialization_preserves_predictions(tmp_path, model_name):
    # Pequena base ficticia: nao depende dos CSVs nem da internet.
    data = pd.DataFrame({column: [0, 1, 2, 3, 4, 5, 6, 7] for column in FEATURE_COLUMNS})
    data["sex"] = [1, 2, 1, 2, 1, 2, 1, 2]
    data["education"] = [1, 2, 3, 4, 1, 2, 3, 4]
    data["marriage"] = [1, 2, 3, 1, 2, 3, 1, 2]
    data["age"] = [25, 30, 35, 40, 45, 50, 55, 60]
    data["limit_bal"] = [
        10_000,
        20_000,
        30_000,
        40_000,
        50_000,
        60_000,
        70_000,
        80_000,
    ]

    target = pd.Series([0, 0, 1, 0, 1, 0, 1, 0])

    pipeline = build_models()[model_name]
    pipeline.fit(data, target)

    # Entrada de inferencia diferente dos registros usados no ajuste.
    inference_data = data.iloc[[0, 3, 7]].copy()
    inference_data["limit_bal"] = [15_000, 45_000, 90_000]

    predictions_before = pipeline.predict(inference_data)
    probabilities_before = pipeline.predict_proba(inference_data)

    artifact_path = tmp_path / f"{model_name}.joblib"
    joblib.dump(pipeline, artifact_path)
    restored = joblib.load(artifact_path)

    np.testing.assert_array_equal(
        predictions_before,
        restored.predict(inference_data),
    )
    np.testing.assert_allclose(
        probabilities_before,
        restored.predict_proba(inference_data),
        rtol=1e-12,
        atol=1e-12,
    )
    np.testing.assert_array_equal(
        pipeline.classes_,
        restored.classes_,
    )
