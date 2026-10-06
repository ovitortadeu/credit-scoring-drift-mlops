"""Testes do contrato de dados: valida referencia e rejeita violacoes."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pandera.errors
import pytest

from src.validation.invalid_batch import build_invalid_batch
from src.validation.schema import validate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = PROJECT_ROOT / "data" / "reference" / "reference.csv"


@pytest.fixture
def amostra_valida() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "client_id": [1, 2, 3],
            "limit_bal": [50000, 30000, 100000],
            "sex": [1, 2, 2],
            "education": [2, 1, 3],
            "marriage": [1, 2, 1],
            "age": [25, 40, 55],
            "pay_0": [0, 0, -1],
            "pay_2": [0, 0, 0],
            "pay_3": [0, 0, 0],
            "pay_4": [0, 0, 0],
            "pay_5": [0, 0, 0],
            "pay_6": [0, 0, 0],
            "bill_amt1": [1000, 2000, 3000],
            "bill_amt2": [1000, 2000, 3000],
            "bill_amt3": [1000, 2000, 3000],
            "bill_amt4": [1000, 2000, 3000],
            "bill_amt5": [1000, 2000, 3000],
            "bill_amt6": [1000, 2000, 3000],
            "pay_amt1": [500, 500, 500],
            "pay_amt2": [500, 500, 500],
            "pay_amt3": [500, 500, 500],
            "pay_amt4": [500, 500, 500],
            "pay_amt5": [500, 500, 500],
            "pay_amt6": [500, 500, 500],
            "default_next_month": [0, 1, 0],
        }
    )


def test_amostra_valida_passa(amostra_valida: pd.DataFrame) -> None:
    assert validate(amostra_valida) is not None


@pytest.mark.skipif(
    not REFERENCE_PATH.exists(),
    reason="data/reference/reference.csv ainda nao gerado (rodar src/data/split.py)",
)
def test_dataset_de_referencia_passa() -> None:
    data = pd.read_csv(REFERENCE_PATH)
    validate(data)


def test_lote_invalido_eh_bloqueado() -> None:
    with pytest.raises(pandera.errors.SchemaErrors):
        validate(build_invalid_batch())


def test_idade_menor_que_18_falha(amostra_valida: pd.DataFrame) -> None:
    amostra_valida.loc[0, "age"] = 15
    with pytest.raises(pandera.errors.SchemaErrors):
        validate(amostra_valida)


def test_idade_maior_que_100_falha(amostra_valida: pd.DataFrame) -> None:
    amostra_valida.loc[0, "age"] = 150
    with pytest.raises(pandera.errors.SchemaErrors):
        validate(amostra_valida)


def test_sex_invalido_falha(amostra_valida: pd.DataFrame) -> None:
    amostra_valida.loc[0, "sex"] = 3
    with pytest.raises(pandera.errors.SchemaErrors):
        validate(amostra_valida)


def test_duplicata_de_client_id_falha(amostra_valida: pd.DataFrame) -> None:
    amostra_valida.loc[2, "client_id"] = 1
    with pytest.raises(pandera.errors.SchemaErrors):
        validate(amostra_valida)


def test_limit_bal_zero_falha(amostra_valida: pd.DataFrame) -> None:
    amostra_valida.loc[0, "limit_bal"] = 0
    with pytest.raises(pandera.errors.SchemaErrors):
        validate(amostra_valida)


def test_target_fora_de_0_e_1_falha(amostra_valida: pd.DataFrame) -> None:
    amostra_valida.loc[0, "default_next_month"] = 2
    with pytest.raises(pandera.errors.SchemaErrors):
        validate(amostra_valida)


def test_pay_amt_negativo_falha(amostra_valida: pd.DataFrame) -> None:
    amostra_valida.loc[0, "pay_amt1"] = -100
    with pytest.raises(pandera.errors.SchemaErrors):
        validate(amostra_valida)


def test_coluna_extra_falha(amostra_valida: pd.DataFrame) -> None:
    amostra_valida["coluna_extra"] = 1
    with pytest.raises(pandera.errors.SchemaErrors):
        validate(amostra_valida)
