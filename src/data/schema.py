"""Nomes das colunas utilizados pelo projeto."""

ID_COLUMN = "client_id"
TARGET_COLUMN = "default_next_month"

COLUMN_MAPPING = {
    "ID": ID_COLUMN,
    "X1": "limit_bal",
    "X2": "sex",
    "X3": "education",
    "X4": "marriage",
    "X5": "age",
    "X6": "pay_0",
    "X7": "pay_2",
    "X8": "pay_3",
    "X9": "pay_4",
    "X10": "pay_5",
    "X11": "pay_6",
    **{f"X{i + 11}": f"bill_amt{i}" for i in range(1, 7)},
    **{f"X{i + 17}": f"pay_amt{i}" for i in range(1, 7)},
    "Y": TARGET_COLUMN,
}

FEATURE_COLUMNS = [
    name
    for name in COLUMN_MAPPING.values()
    if name not in {ID_COLUMN, TARGET_COLUMN}
]