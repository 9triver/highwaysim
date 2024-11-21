import pandas as pd


def is_null_cell(cell: object) -> bool:
    return pd.isnull(cell) or cell in ["", "(null)", "null", "nan", "none"]
