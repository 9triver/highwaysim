"""
distribution calculate util classes
"""

import math

from scipy.stats import gamma


def gamma_distribution(shape: float, scale: float, times: int) -> int:
    return math.ceil(gamma.rvs(shape, scale) * times) + 1
