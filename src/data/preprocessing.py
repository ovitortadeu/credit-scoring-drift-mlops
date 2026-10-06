"""Pre-processamento reutilizavel para treino e inferencia."""

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.data.schema import CATEGORICAL_COLUMNS, NUMERIC_COLUMNS


def build_preprocessor() -> ColumnTransformer:
    """Cria um pre-processador novo, ainda sem ajuste aos dados."""
    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                NUMERIC_COLUMNS,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                CATEGORICAL_COLUMNS,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=True,
    )
