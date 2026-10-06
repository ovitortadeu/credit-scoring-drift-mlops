import hashlib
import json
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

from ucimlrepo import fetch_ucirepo

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATASET_PATH = RAW_DIR / "credit_default.csv"
MANIFEST_PATH = RAW_DIR / "manifest.json"
DICTIONARY_PATH = RAW_DIR / "variables.csv"


def main() -> None:
    """Baixa a base da UCI e registra sua origem e integridade."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    
    if any(
        path.exists()
        for path in (DATASET_PATH, MANIFEST_PATH, DICTIONARY_PATH)
    ):
        raise FileExistsError(
            "Ja existem arquivos da base em data/raw. "
            "Confira-os antes de realizar um novo download."
        )

    print("Baixando o dataset 350 da UCI...")
    dataset = fetch_ucirepo(id=350)
    data = dataset.data.original.copy()

    expected_columns = ["ID", *[f"X{i}" for i in range(1, 24)], "Y"]

    if data.columns.tolist() != expected_columns:
        raise ValueError(
            f"Colunas diferentes das esperadas: {data.columns.tolist()}"
        )

    if len(data) != 30_000:
        raise ValueError(f"Quantidade inesperada de registros: {len(data)}")

    if data["ID"].isna().any() or data["ID"].duplicated().any():
        raise ValueError("A coluna ID possui valores nulos ou repetidos.")

    if data["Y"].isna().any() or set(data["Y"].unique()) != {0, 1}:
        raise ValueError("O alvo Y deve conter apenas as classes 0 e 1.")

    # Preserva nomes, valores e ordem recebidos; não realiza limpeza.
    data.to_csv(DATASET_PATH, index=False, encoding="utf-8", lineterminator="\n")
    dataset.variables.to_csv(
        DICTIONARY_PATH, index=False, encoding="utf-8", lineterminator="\n"
    )

    checksum = hashlib.sha256(DATASET_PATH.read_bytes()).hexdigest()

    manifest = {
        "dataset": "Default of Credit Card Clients",
        "uci_id": 350,
        "source_url": dataset.metadata.repository_url,
        "data_url": dataset.metadata.data_url,
        "doi": "10.24432/C55S3H",
        "citation": (
            "Yeh, I. (2009). Default of Credit Card Clients [Dataset]. "
            "UCI Machine Learning Repository."
        ),
        "license": "CC BY 4.0",
        "downloaded_at_utc": datetime.now(UTC).isoformat(),
        "ucimlrepo_version": version("ucimlrepo"),
        "pandas_version": version("pandas"),
        "rows": len(data),
        "columns": data.columns.tolist(),
        "target": "Y",
        "id_column": "ID",
        "target_counts": {
            str(label): int(count)
            for label, count in data["Y"].value_counts().sort_index().items()
        },
        "csv_sha256": checksum,
    }

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Base salva em: {DATASET_PATH}")
    print(f"Dimensoes: {data.shape}")
    print(f"Dicionario salvo em: {DICTIONARY_PATH}")
    print(f"Manifesto salvo em: {MANIFEST_PATH}")
    print(f"SHA-256: {checksum}")


if __name__ == "__main__":
    main()