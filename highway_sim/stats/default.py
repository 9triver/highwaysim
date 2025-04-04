"""
默认统计信息模块
"""

import logging
from typing import List, Dict

from highway_sim.config import common

gantry_time_used: List[int] = []
total_time_used: List[int] = []
num_gantry_passed: List[int] = []
exit_hex2num: Dict[str, int] = {}
entry_hex2num: Dict[str, int] = {}
hour2entry_num: Dict[int, int] = {a: 0 for a in range(24)}
hour2exit_num: Dict[int, int] = {a: 0 for a in range(24)}


def entry_hour_info(now_ms: float, logger: logging.Logger) -> None:
    """
    记录车辆进入高速公路时的小时信息，并以debug级别输出

    Args:
        now_ms (float): 当前时间（ms）
        logger (logging.Logger): 日志记录器

    Returns:

    """
    hour = int(now_ms / common.HOUR_MILLISECOND) % 24
    hour2entry_num[hour] += 1
    logger.debug("enterHour %d", hour)


def exit_hour_info(now_ms: float, logger: logging.Logger) -> None:
    """
    记录车辆离开高速公路时的小时信息，并以debug级别输出

    Args:
        now_ms (float): 当前时间（ms）
        logger (logging.Logger): 日志记录器

    Returns:

    """
    hour = int(now_ms / common.HOUR_MILLISECOND) % 24
    hour2exit_num[hour] += 1
    logger.debug("exitHour %d", hour)


def num_passed_info(num: int, logger: logging.Logger) -> None:
    """
    记录通过的门架数量，并以debug级别输出

    Args:
        num (int): 通过的门架数量
        logger (logging.Logger): 日志记录器

    Returns:

    """
    num_gantry_passed.append(num)
    logger.debug("passed %d gantry", num)


def total_time_info(now_ms: float, last_ms: float, logger: logging.Logger) -> None:
    """
    记录车辆通过高速公路的总时间，并以debug级别输出

    Args:
        now_ms (float): 当前时间（ms）
        last_ms (float): 进入公路时间（ms）
        logger (logging.Logger): 日志记录器

    Returns:

    """

    duration = int((now_ms - last_ms) / common.SECOND_MILLISECOND)
    total_time_used.append(duration)
    logger.debug("totalTime %d s", duration)


def gantry_time_info(duration: int, logger: logging.Logger) -> None:
    """
    记录车辆通过门架的时间，并以debug级别输出

    Args:
        duration (int): 通过门架的时间（ms）
        logger (logging.Logger): 日志记录器

    Returns:

    """
    d = int(duration / common.SECOND_MILLISECOND)
    gantry_time_used.append(d)
    logger.debug("thisTime %d s", d)


def exit_hex_info(h: str, logger: logging.Logger) -> None:
    """
    记录车辆离开高速公路时的出口编号信息，并以debug级别输出

    Args:
        h (str): 出口编号
        logger (logging.Logger): 日志记录器

    Returns:

    """
    exit_hex2num[h] = exit_hex2num.get(h, 0) + 1
    logger.debug("exitHex %s", h)


def entry_hex_info(h: str, logger: logging.Logger) -> None:
    """
    记录车辆进入高速公路时的入口编号信息，并以debug级别输出

    Args:
        h (str): 入口编号
        logger (logging.Logger): 日志记录器

    Returns:

    """
    entry_hex2num[h] = entry_hex2num.get(h, 0) + 1
    logger.debug("enterHex %s", h)


def record(logger: logging.Logger) -> None:
    """
    以info级别输出记录的所有统计信息，可选：对数据进行额外操作

    Args:
        logger (logging.Logger): 日志记录器

    Returns:

    """
    top_10_entry_hex = {
        k: entry_hex2num[k]
        for k in sorted(entry_hex2num, key=entry_hex2num.get, reverse=True)[:10]
    }
    top_10_exit_hex = {
        k: exit_hex2num[k]
        for k in sorted(exit_hex2num, key=exit_hex2num.get, reverse=True)[:10]
    }
    logger.info(top_10_entry_hex)
    logger.info(top_10_exit_hex)
    logger.info(gantry_time_used)
    logger.info(total_time_used)
    logger.info(num_gantry_passed)
    logger.info(hour2entry_num)
    logger.info(hour2exit_num)
    logger.info(sum(gantry_time_used) / len(gantry_time_used))
