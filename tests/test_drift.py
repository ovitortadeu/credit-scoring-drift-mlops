"""Testes unitários para simulação e detecção de data drift."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.drift.simulate import (
    PAY_MAX,
    PAY_MIN,
    degrade_payment_status,
    simulate_drift,
)
from src.validation.schema import validate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_BASE_PATH = PROJECT_ROOT / "data" / "production" / "production_base.csv"


@pytest.fixture
def base_production_data() -> pd.DataFrame:
    """Carrega o dataset base de produção para testes."""
    if not PRODUCTION_BASE_PATH.exists():
        pytest.skip("Base de producao ainda nao gerada (rodar src/data/split.py)")
    return pd.read_csv(PRODUCTION_BASE_PATH)


def test_degrade_payment_status_bounds() -> None:
    """Garante que a degradacao respeita estritamente o intervalo [PAY_MIN, PAY_MAX]."""
    series = pd.Series([-2, -1, 0, 1, 5, 8, 9])
    rng = np.random.default_rng(42)

    # Força degradacao com 100% de probabilidade e incremento alto
    degraded = degrade_payment_status(series, probability=1.0, max_increment=5, rng=rng)

    assert (degraded >= PAY_MIN).all()
    assert (degraded <= PAY_MAX).all()
    assert (degraded >= series).all()


def test_simulate_drift_preserves_shape(base_production_data: pd.DataFrame) -> None:
    """Garante que a simulacao mantem a mesma quantidade de linhas e colunas."""
    drifted = simulate_drift(seed=42)
    assert drifted.shape == base_production_data.shape
    assert list(drifted.columns) == list(base_production_data.columns)


def test_simulate_drift_complies_with_contract() -> None:
    """Garante que os dados com drift continuam validos segundo o contrato Pandera."""
    drifted = simulate_drift(seed=42)
    validated = validate(drifted)
    assert validated is not None
    assert len(validated) == len(drifted)


def test_simulate_drift_increases_payment_delays(base_production_data: pd.DataFrame) -> None:
    """Garante que a distribuicao de atrasos realmente aumentou apos o drift."""
    drifted = simulate_drift(seed=42)
    assert drifted["pay_0"].mean() > base_production_data["pay_0"].mean()
    assert drifted["pay_2"].mean() > base_production_data["pay_2"].mean()


def test_simulate_drift_reproducibility() -> None:
    """Garante determinismo: a mesma seed produz resultados exatamente iguais."""
    run_1 = simulate_drift(seed=99)
    run_2 = simulate_drift(seed=99)
    pd.testing.assert_frame_equal(run_1, run_2)
