"""CLI para validar qualquer CSV contra o contrato Pandera."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pandera.errors

from src.validation.schema import validate


def run(path: Path) -> int:
    if not path.exists():
        print(f"Arquivo nao encontrado: {path}", file=sys.stderr)
        return 2

    data = pd.read_csv(path)

    try:
        validate(data)
    except pandera.errors.SchemaErrors as err:
        print(f"VALIDACAO FALHOU em {path}")
        print(f"Linhas: {len(data)}  Violacoes: {len(err.failure_cases)}")
        print()
        print(err.failure_cases.to_string(index=False))
        return 1

    print(f"OK — {len(data)} linhas aprovadas pelo contrato ({path.name}).")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "Uso: python -m src.validation.cli <caminho/para/arquivo.csv>",
            file=sys.stderr,
        )
        return 2
    return run(Path(sys.argv[1]))


if __name__ == "__main__":
    raise SystemExit(main())
