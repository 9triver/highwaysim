"""
感觉没有必要分多个类,而且类变量在greenlet下还没摸清楚
"""

import logging
from typing import List, Dict

from config import common

gantry_time_used: List[int] = []
total_time_used: List[int] = []
num_gantry_passed: List[int] = []
exit_hex_2_num: Dict[str, int] = {}
entry_hex_2_num: Dict[str, int] = {}
hour_2_entry_num: Dict[int, int] = {a: 0 for a in range(24)}
hour_2_exit_num: Dict[int, int] = {a: 0 for a in range(24)}


def entry_hour_info(now_ms: float, logger: logging.Logger):
    hour = int(now_ms / common.HOUR_MILLISECOND) % 24
    hour_2_entry_num[hour] += 1
    logger.debug("enterHour %d", hour)


def exit_hour_info(now_ms: float, logger: logging.Logger):
    hour = int(now_ms / common.HOUR_MILLISECOND) % 24
    hour_2_exit_num[hour] += 1
    logger.debug("exitHour %d", hour)


def num_passed_info(num: int, logger: logging.Logger):
    num_gantry_passed.append(num)
    logger.debug("passed %d gantry", num)


def total_time_info(now_ms: float, last_ms: float, logger: logging.Logger):
    duration = int(now_ms - last_ms)
    total_time_used.append(duration)
    logger.debug("totalTime %d ms", duration)


def gantry_time_info(now_ms: float, last_ms: float, logger: logging.Logger):
    duration = int(now_ms - last_ms)
    gantry_time_used.append(duration)
    logger.debug("thisTime %d ms", duration)


def exit_hex_info(h: str, logger: logging.Logger):
    exit_hex_2_num[h] = exit_hex_2_num.get(h, 0) + 1
    logger.debug("exitHex %s", h)


def entry_hex_info(h: str, logger: logging.Logger):
    entry_hex_2_num[h] = exit_hex_2_num.get(h, 0) + 1
    logger.debug("enterHex %s", h)


def record(logger: logging.Logger):
    top_10_entry_hex = sorted(entry_hex_2_num, key=entry_hex_2_num.get, reverse=True)[
        :10
    ]
    top_10_exit_hex = sorted(exit_hex_2_num, key=exit_hex_2_num.get, reverse=True)[:10]
    logger.info(top_10_entry_hex)
    logger.info(top_10_exit_hex)
    logger.info(gantry_time_used)
    logger.info(total_time_used)
    logger.info(num_gantry_passed)
    logger.info(hour_2_entry_num)
    logger.info(hour_2_exit_num)
