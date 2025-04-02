"""
该模块计算gamma分布
"""

import math
import random


def gamma_distribution(shape: float, scale: float, times: int) -> int:
    """
    生成gamma分布的随机数

    Args:
        shape (float): 形状参数
        scale (float): 尺度参数
        times (int): 乘数

    Returns:
        int: 生成的随机数
    """
    # random.seed(None)
    return math.ceil(random.gammavariate(shape, 1 / scale) * times) + 1
