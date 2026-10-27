"""Simula drift realista no dataset de producao para deteccao com Evidently.

Estrategia: degrada progressivamente o historico de pagamentos (pay_0..pay_6),
simulando um cenario macroeconomico adverso onde os clientes atrasam mais.

Cada valor de pay_X tem uma probabilidade controlada de ser "empurrado para cima"
(mais atraso), respeitando os limites do contrato Pandera [-2, 9].

Referencia semântica dos valores de pay_X:
    -2  sem consumo no periodo
    -1  pagou integralmente
     0  credito rotativo (revolving)
     1  atraso de 1 mes
     2  atraso de 2 meses
     ...
     9  atraso de 9+ meses
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.schema import TARGET_COLUMN

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_BASE_PATH = PROJECT_ROOT / "data" / "production" / "production_base.csv"
DRIFTED_OUTPUT_PATH = PROJECT_ROOT / "data" / "production" / "production_drifted.csv"
DRIFT_REPORT_PATH = PROJECT_ROOT / "reports" / "drift_simulation.json"

PAY_COLUMNS = ["pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6"]
PAY_MIN = -2
PAY_MAX = 9


def degrade_payment_status(
    series: pd.Series,
    probability: float,
    max_increment: int,
    rng: np.random.Generator,
) -> pd.Series:
    """Empurra valores de atraso para cima com probabilidade controlada.

    Args:
        series: Coluna pay_X original.
        probability: Chance de cada registro ser degradado (0.0 a 1.0).
        max_increment: Maximo de meses de atraso a adicionar por registro.
        rng: Gerador de numeros aleatorios para reproducibilidade.

    Returns:
        Serie com os valores degradados, respeitando [PAY_MIN, PAY_MAX].
    """
    mask = rng.random(len(series)) < probability
    increments = rng.integers(1, max_increment + 1, size=len(series))
    degraded = series.copy()
    degraded.loc[mask] = (series.loc[mask] + increments[mask]).clip(PAY_MIN, PAY_MAX)
    return degraded.astype(series.dtype)


def reduce_payment_amounts(
    dataframe: pd.DataFrame,
    probability: float,
    reduction_factor: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Reduz valores pagos (pay_amt1..pay_amt6) para simular inadimplencia.

    Args:
        dataframe: DataFrame com as colunas pay_amt1 a pay_amt6.
        probability: Chance de cada registro ter o pagamento reduzido.
        reduction_factor: Fator multiplicador (ex: 0.3 = paga 30% do que pagava).
        rng: Gerador de numeros aleatorios.

    Returns:
        DataFrame com pay_amts reduzidos, mantendo >= 0 (contrato Pandera).
    """
    pay_amt_columns = [f"pay_amt{i}" for i in range(1, 7)]
    result = dataframe.copy()
    mask = rng.random(len(result)) < probability

    for column in pay_amt_columns:
        reduced = (result.loc[mask, column] * reduction_factor).astype(int)
        result.loc[mask, column] = reduced.clip(lower=0)

    return result


def inflate_bill_amounts(
    dataframe: pd.DataFrame,
    probability: float,
    inflation_factor: float,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Infla faturas (bill_amt1..bill_amt6) simulando aumento de gastos.

    Args:
        dataframe: DataFrame com as colunas bill_amt1 a bill_amt6.
        probability: Chance de cada registro ter a fatura inflada.
        inflation_factor: Fator multiplicador (ex: 1.5 = 50% a mais).
        rng: Gerador de numeros aleatorios.

    Returns:
        DataFrame com bill_amts inflados.
    """
    bill_columns = [f"bill_amt{i}" for i in range(1, 7)]
    result = dataframe.copy()
    mask = rng.random(len(result)) < probability

    for column in bill_columns:
        result.loc[mask, column] = (result.loc[mask, column] * inflation_factor).astype(int)

    return result


def simulate_drift(
    seed: int = 42,
    delay_probability: float = 0.40,
    max_delay_increment: int = 3,
    payment_reduction_probability: float = 0.35,
    payment_reduction_factor: float = 0.30,
    bill_inflation_probability: float = 0.25,
    bill_inflation_factor: float = 1.50,
) -> pd.DataFrame:
    """Aplica drift sintetico controlado ao dataset de producao.

    O cenario simulado representa uma crise economica onde:
    - 40% dos clientes atrasam mais (ate 3 meses a mais de atraso)
    - 35% dos clientes pagam menos (apenas 30% do que pagavam)
    - 25% dos clientes gastam mais (faturas 50% maiores)

    Args:
        seed: Semente para reproducibilidade.
        delay_probability: Fracao de clientes com atraso agravado.
        max_delay_increment: Maximo de meses de atraso adicionais.
        payment_reduction_probability: Fracao com pagamentos reduzidos.
        payment_reduction_factor: Quanto pagam do valor original (0-1).
        bill_inflation_probability: Fracao com faturas infladas.
        bill_inflation_factor: Fator de inflacao das faturas.

    Returns:
        DataFrame com drift aplicado, pronto para deteccao pelo Evidently.
    """
    rng = np.random.default_rng(seed)

    data = pd.read_csv(PRODUCTION_BASE_PATH)
    original_shape = data.shape

    # 1) Degrada status de pagamento (pay_0 .. pay_6)
    for column in PAY_COLUMNS:
        data[column] = degrade_payment_status(
            series=data[column],
            probability=delay_probability,
            max_increment=max_delay_increment,
            rng=rng,
        )

    # 2) Reduz valores pagos (pay_amt1 .. pay_amt6)
    data = reduce_payment_amounts(
        dataframe=data,
        probability=payment_reduction_probability,
        reduction_factor=payment_reduction_factor,
        rng=rng,
    )

    # 3) Infla faturas (bill_amt1 .. bill_amt6)
    data = inflate_bill_amounts(
        dataframe=data,
        probability=bill_inflation_probability,
        inflation_factor=bill_inflation_factor,
        rng=rng,
    )

    if data.shape != original_shape:
        raise ValueError("A simulacao alterou a dimensao do dataset.")

    return data


def save_drifted_dataset(data: pd.DataFrame, parameters: dict) -> None:
    """Salva o dataset com drift e gera manifesto de rastreabilidade.

    Args:
        data: DataFrame com drift aplicado.
        parameters: Parametros usados na simulacao.
    """
    DRIFTED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    data.to_csv(
        DRIFTED_OUTPUT_PATH,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "source": PRODUCTION_BASE_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "output": DRIFTED_OUTPUT_PATH.relative_to(PROJECT_ROOT).as_posix(),
        "rows": len(data),
        "columns": data.columns.tolist(),
        "parameters": parameters,
        "output_sha256": hashlib.sha256(DRIFTED_OUTPUT_PATH.read_bytes()).hexdigest(),
    }

    DRIFT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DRIFT_REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Dataset com drift salvo em: {DRIFTED_OUTPUT_PATH}")
    print(f"Registros: {len(data)}")
    print(f"Manifesto salvo em: {DRIFT_REPORT_PATH}")


def main() -> None:
    """Ponto de entrada: aplica drift e salva os artefatos."""
    parameters = {
        "seed": 42,
        "delay_probability": 0.40,
        "max_delay_increment": 3,
        "payment_reduction_probability": 0.35,
        "payment_reduction_factor": 0.30,
        "bill_inflation_probability": 0.25,
        "bill_inflation_factor": 1.50,
    }

    data = simulate_drift(**parameters)

    # Compara distribuicao de atraso antes vs depois
    original = pd.read_csv(PRODUCTION_BASE_PATH)

    print("\n--- Distribuicao de pay_0 ---")
    print(f"Original:  media={original['pay_0'].mean():.2f}  mediana={original['pay_0'].median()}")
    print(f"Drifted:   media={data['pay_0'].mean():.2f}  mediana={data['pay_0'].median()}")

    print("\n--- Taxa de default ---")
    print(f"Original:  {original[TARGET_COLUMN].mean():.2%}")
    print(f"Drifted:   {data[TARGET_COLUMN].mean():.2%}")

    save_drifted_dataset(data, parameters)


if __name__ == "__main__":
    main()
