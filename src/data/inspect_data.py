"""Inspeciona a base original sem modificar seus valores."""

import hashlib
import json
from pathlib import Path

import pandas as pd

from src.data.schema import COLUMN_MAPPING, FEATURE_COLUMNS, ID_COLUMN, TARGET_COLUMN

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def main() -> None:
    csv_path = RAW_DIR / "credit_default.csv"
    manifest_path = RAW_DIR / "manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current_hash = hashlib.sha256(csv_path.read_bytes()).hexdigest()

    if current_hash != manifest["csv_sha256"]:
        raise ValueError("O CSV foi alterado desde a criacao do manifesto.")

    raw = pd.read_csv(csv_path)

    if raw.columns.tolist() != list(COLUMN_MAPPING):
        raise ValueError("As colunas recebidas diferem do schema esperado.")

    data = raw.rename(columns=COLUMN_MAPPING)

    print("INTEGRIDADE: SHA-256 confere com o manifesto.")

    print("\nTIPOS DAS COLUNAS:")
    print(data.dtypes.to_string())

    print("\nVALORES NULOS POR COLUNA:")
    print(data.isna().sum().to_string())

    print("\nIDENTIFICADORES REPETIDOS:")
    print(data[ID_COLUMN].duplicated().sum())

    print("\nREGISTROS REPETIDOS, DESCONSIDERANDO O ID:")
    print(data.drop(columns=ID_COLUMN).duplicated().sum())

    print("\nFEATURES IDENTICAS, DESCONSIDERANDO ID E ALVO:")
    print(data.duplicated(subset=FEATURE_COLUMNS).sum())

    print("\nDISTRIBUICAO DO ALVO:")
    print(data[TARGET_COLUMN].value_counts(dropna=False).sort_index())

    print("\nVALORES DAS VARIAVEIS CATEGORICAS E STATUS DE PAGAMENTO:")
    categorical_columns = [
        "sex",
        "education",
        "marriage",
        "pay_0",
        "pay_2",
        "pay_3",
        "pay_4",
        "pay_5",
        "pay_6",
    ]

    for column in categorical_columns:
        print(f"\n{column}:")
        print(data[column].value_counts(dropna=False).sort_index().to_string())

    print("\nRESUMO DAS VARIAVEIS NUMERICAS:")
    numeric_columns = [
        "limit_bal",
        "age",
        *[f"bill_amt{i}" for i in range(1, 7)],
        *[f"pay_amt{i}" for i in range(1, 7)],
    ]
    print(data[numeric_columns].describe().round(2).to_string())


if __name__ == "__main__":
    main()