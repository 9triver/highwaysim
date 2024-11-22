"""
distribution calculate util classes
"""

import math

import random


def gamma_distribution(shape: float, scale: float, times: int) -> int:
    return math.ceil(random.gammavariate(shape, 1 / scale) * times) + 1
