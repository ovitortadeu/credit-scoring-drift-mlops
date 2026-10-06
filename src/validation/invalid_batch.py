"""Gera um lote proposital invalido para demonstrar o bloqueio pelo contrato."""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INVALID_PATH = PROJECT_ROOT / "data" / "production" / "invalid_batch.csv"


def build_invalid_batch() -> pd.DataFrame:
    """Monta um lote com varias violacoes do contrato ao mesmo tempo."""
    return pd.DataFrame(
        {
            # id duplicado (1, 1) e id negativo
            "client_id": [1, 1, -5, 4],
            # limit_bal zero (viola > 0) e negativo
            "limit_bal": [50000, 0, -1000, 20000],
            # sex fora de {1, 2}
            "sex": [1, 2, 3, 1],
            # education fora de [0, 6]
            "education": [2, 7, 1, 2],
            # marriage fora de [0, 3]
            "marriage": [1, 4, 2, 1],
            # age fora de [18, 100]
            "age": [25, 15, 101, 30],
            # pay_0 fora de [-2, 9]
            "pay_0": [0, 10, -3, 0],
            "pay_2": [0, 0, 0, 0],
            "pay_3": [0, 0, 0, 0],
            "pay_4": [0, 0, 0, 0],
            "pay_5": [0, 0, 0, 0],
            "pay_6": [0, 0, 0, 0],
            "bill_amt1": [1000, 2000, 3000, 4000],
            "bill_amt2": [1000, 2000, 3000, 4000],
            "bill_amt3": [1000, 2000, 3000, 4000],
            "bill_amt4": [1000, 2000, 3000, 4000],
            "bill_amt5": [1000, 2000, 3000, 4000],
            "bill_amt6": [1000, 2000, 3000, 4000],
            # pay_amt negativo
            "pay_amt1": [500, 500, -100, 500],
            "pay_amt2": [500, 500, 500, 500],
            "pay_amt3": [500, 500, 500, 500],
            "pay_amt4": [500, 500, 500, 500],
            "pay_amt5": [500, 500, 500, 500],
            "pay_amt6": [500, 500, 500, 500],
            # target fora de {0, 1}
            "default_next_month": [0, 1, 2, 0],
        }
    )


def main() -> None:
    INVALID_PATH.parent.mkdir(parents=True, exist_ok=True)
    batch = build_invalid_batch()
    batch.to_csv(INVALID_PATH, index=False, encoding="utf-8", lineterminator="\n")
    print(f"Lote invalido gerado em: {INVALID_PATH}")
    print(f"Linhas: {len(batch)}")


if __name__ == "__main__":
    main()
