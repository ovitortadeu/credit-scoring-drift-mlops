"""Separa referencia, teste e producao preservando grupos de perfis iguais."""

import hashlib
import json
from importlib.metadata import version
from itertools import combinations
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from src.data.schema import COLUMN_MAPPING, FEATURE_COLUMNS, ID_COLUMN, TARGET_COLUMN

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED = 42

OUTPUT_PATHS = {
    "reference": PROJECT_ROOT / "data/reference/reference.csv",
    "test": PROJECT_ROOT / "data/test/test.csv",
    "production_base": PROJECT_ROOT / "data/production/production_base.csv",
}
REPORT_PATH = PROJECT_ROOT / "reports/split_summary.json"


def main() -> None:
    raw_path = PROJECT_ROOT / "data/raw/credit_default.csv"
    manifest_path = PROJECT_ROOT / "data/raw/manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()

    if raw_hash != manifest["csv_sha256"]:
        raise ValueError("A base original difere do manifesto.")

    raw = pd.read_csv(raw_path)

    if raw.columns.tolist() != list(COLUMN_MAPPING):
        raise ValueError("Colunas diferentes das esperadas.")

    data = raw.rename(columns=COLUMN_MAPPING)

    if data.isna().any().any():
        raise ValueError("A base possui valores nulos.")

    if data[ID_COLUMN].duplicated().any():
        raise ValueError("Existem identificadores repetidos.")

    if set(data[TARGET_COLUMN].unique()) != {0, 1}:
        raise ValueError("O alvo deve conter as classes 0 e 1.")

    # Mesmo perfil recebe o mesmo grupo, independentemente do ID e do alvo.
    groups = data.groupby(FEATURE_COLUMNS, sort=True, dropna=False).ngroup()

    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=SEED,
    )

    fold_assignment = pd.Series(-1, index=data.index, dtype="int64")

    for fold, (_, indices) in enumerate(
        splitter.split(data[FEATURE_COLUMNS], data[TARGET_COLUMN], groups)
    ):
        fold_assignment.iloc[indices] = fold

    if (fold_assignment < 0).any():
        raise ValueError("Existem registros sem conjunto definido.")

    # Dois blocos de aproximadamente 20%; os outros tres formam o treino.
    masks = {
        "reference": fold_assignment >= 2,
        "test": fold_assignment == 0,
        "production_base": fold_assignment == 1,
    }

    splits = {
        name: data.loc[mask].copy()
        for name, mask in masks.items()
    }

    # Verifica separacao tanto por identificador quanto por perfil.
    for left, right in combinations(splits, 2):
        ids_left = set(splits[left][ID_COLUMN])
        ids_right = set(splits[right][ID_COLUMN])

        if ids_left & ids_right:
            raise ValueError(f"IDs compartilhados entre {left} e {right}.")

        groups_left = set(groups.loc[masks[left]])
        groups_right = set(groups.loc[masks[right]])

        if groups_left & groups_right:
            raise ValueError(f"Perfis compartilhados entre {left} e {right}.")

    if sum(len(part) for part in splits.values()) != len(data):
        raise ValueError("A divisao nao preservou todos os registros.")

    summary = {
        "seed": SEED,
        "method": "StratifiedGroupKFold",
        "n_splits": 5,
        "fold_assignment": {
            "reference": [2, 3, 4],
            "test": [0],
            "production_base": [1],
        },
        "group_columns": FEATURE_COLUMNS,
        "raw_sha256": raw_hash,
        "sklearn_version": version("scikit-learn"),
        "pandas_version": version("pandas"),
        "id_overlap": False,
        "feature_group_overlap": False,
        "splits": {},
    }

    for name, part in splits.items():
        if set(part[TARGET_COLUMN].unique()) != {0, 1}:
            raise ValueError(f"O conjunto {name} nao possui ambas as classes.")

    for name, part in splits.items():
        path = OUTPUT_PATHS[name]
        path.parent.mkdir(parents=True, exist_ok=True)

        part.to_csv(
            path,
            index=False,
            encoding="utf-8",
            lineterminator="\n",
        )

        summary["splits"][name] = {
            "path": path.relative_to(PROJECT_ROOT).as_posix(),
            "rows": len(part),
            "fraction": len(part) / len(data),
            "default_rate": float(part[TARGET_COLUMN].mean()),
            "target_counts": {
                str(label): int(count)
                for label, count in part[TARGET_COLUMN].value_counts().items()
            },
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

        print(
            f"{name}: {len(part)} registros | "
            f"inadimplencia: {part[TARGET_COLUMN].mean():.2%}"
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("\nVerificado: nenhum ID ou perfil compartilhado entre conjuntos.")
    print("Todos os registros foram preservados.")
    print(f"Resumo salvo em: {REPORT_PATH}")


if __name__ == "__main__":
    main()