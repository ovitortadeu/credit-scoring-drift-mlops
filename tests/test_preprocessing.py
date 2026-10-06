"""Testes de isolamento e estabilidade do pre-processamento."""

import numpy as np
import pandas as pd
import pytest

from src.data.preprocessing import build_preprocessor
from src.data.schema import FEATURE_COLUMNS, ID_COLUMN, NUMERIC_COLUMNS, TARGET_COLUMN


@pytest.fixture
def sample_data() -> pd.DataFrame:
    data = pd.DataFrame({column: [0, 1, 2, 3] for column in FEATURE_COLUMNS})

    data["sex"] = [1, 2, 1, 2]
    data["education"] = [1, 2, 3, 4]
    data["marriage"] = [1, 2, 1, 3]
    data["age"] = [25, 35, 45, 55]
    data["limit_bal"] = [10_000, 20_000, 30_000, 40_000]
    data[ID_COLUMN] = [101, 102, 103, 104]
    data[TARGET_COLUMN] = [0, 1, 0, 1]

    return data


def test_id_and_target_do_not_change_features(sample_data):
    preprocessor = build_preprocessor()
    original = preprocessor.fit_transform(sample_data)

    changed = sample_data.copy()
    changed[ID_COLUMN] = [901, 902, 903, 904]
    changed[TARGET_COLUMN] = 1 - changed[TARGET_COLUMN]

    np.testing.assert_allclose(
        original,
        preprocessor.transform(changed),
    )

    # Na inferencia, o alvo nao estara disponivel.
    features_only = sample_data[FEATURE_COLUMNS]
    np.testing.assert_allclose(
        original,
        preprocessor.transform(features_only),
    )


def test_unseen_category_keeps_output_shape(sample_data):
    preprocessor = build_preprocessor()
    training_output = preprocessor.fit_transform(sample_data)

    new_data = sample_data.iloc[[0]].copy()
    new_data["education"] = 6  # Categoria ausente no treino ficticio.

    result = preprocessor.transform(new_data)

    assert result.shape == (1, training_output.shape[1])
    assert np.isfinite(result).all()

    names = preprocessor.get_feature_names_out()
    education_mask = [name.startswith("categorical__education_") for name in names]

    np.testing.assert_array_equal(result[:, education_mask], 0)


def test_transform_reuses_training_statistics(sample_data):
    preprocessor = build_preprocessor()
    preprocessor.fit(sample_data)

    scaler = preprocessor.named_transformers_["numeric"]
    training_mean = scaler.mean_.copy()
    training_scale = scaler.scale_.copy()

    new_data = sample_data.iloc[[0]].copy()
    new_data["limit_bal"] = 1_000_000

    result = preprocessor.transform(new_data)

    np.testing.assert_array_equal(scaler.mean_, training_mean)
    np.testing.assert_array_equal(scaler.scale_, training_scale)

    limit_index = NUMERIC_COLUMNS.index("limit_bal")
    expected = (1_000_000 - training_mean[limit_index]) / training_scale[limit_index]

    assert result[0, limit_index] == pytest.approx(expected)
