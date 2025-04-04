"""
数据处理工具模块
"""

import pandas as pd


def is_null_cell(cell: object) -> bool:
    """
    判断一个单元格是否为空

    Args:
        cell (object): 单元格的值

    Returns:
        bool: 是否为空
    """
    return pd.isnull(cell) or cell in ["", "(null)", "null", "nan", "none"]
