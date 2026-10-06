"""Contrato de dados do dataset Default of Credit Card Clients."""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series


class CreditDefaultSchema(pa.DataFrameModel):
    client_id: Series[int] = pa.Field(unique=True, ge=1, nullable=False)
    limit_bal: Series[int] = pa.Field(gt=0, nullable=False)
    sex: Series[int] = pa.Field(isin=[1, 2], nullable=False)
    education: Series[int] = pa.Field(ge=0, le=6, nullable=False)
    marriage: Series[int] = pa.Field(ge=0, le=3, nullable=False)
    age: Series[int] = pa.Field(ge=18, le=100, nullable=False)

    pay_0: Series[int] = pa.Field(ge=-2, le=9, nullable=False)
    pay_2: Series[int] = pa.Field(ge=-2, le=9, nullable=False)
    pay_3: Series[int] = pa.Field(ge=-2, le=9, nullable=False)
    pay_4: Series[int] = pa.Field(ge=-2, le=9, nullable=False)
    pay_5: Series[int] = pa.Field(ge=-2, le=9, nullable=False)
    pay_6: Series[int] = pa.Field(ge=-2, le=9, nullable=False)

    bill_amt1: Series[int] = pa.Field(nullable=False)
    bill_amt2: Series[int] = pa.Field(nullable=False)
    bill_amt3: Series[int] = pa.Field(nullable=False)
    bill_amt4: Series[int] = pa.Field(nullable=False)
    bill_amt5: Series[int] = pa.Field(nullable=False)
    bill_amt6: Series[int] = pa.Field(nullable=False)

    pay_amt1: Series[int] = pa.Field(ge=0, nullable=False)
    pay_amt2: Series[int] = pa.Field(ge=0, nullable=False)
    pay_amt3: Series[int] = pa.Field(ge=0, nullable=False)
    pay_amt4: Series[int] = pa.Field(ge=0, nullable=False)
    pay_amt5: Series[int] = pa.Field(ge=0, nullable=False)
    pay_amt6: Series[int] = pa.Field(ge=0, nullable=False)

    default_next_month: Series[int] = pa.Field(isin=[0, 1], nullable=False)

    class Config:
        strict = True
        coerce = False


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Valida o DataFrame contra o contrato, coletando todos os erros antes de falhar."""
    return CreditDefaultSchema.validate(df, lazy=True)
