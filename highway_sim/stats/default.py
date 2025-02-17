"""
感觉没有必要分多个类,而且类变量在greenlet下还没摸清楚
"""

import logging
from typing import List, Dict

from config import common

gantry_time_used: List[int] = []
total_time_used: List[int] = []
num_gantry_passed: List[int] = []
exit_hex2num: Dict[str, int] = {}
entry_hex2num: Dict[str, int] = {}
hour2entry_num: Dict[int, int] = {a: 0 for a in range(24)}
hour2exit_num: Dict[int, int] = {a: 0 for a in range(24)}


def entry_hour_info(now_ms: float, logger: logging.Logger):
    hour = int(now_ms / common.HOUR_MILLISECOND) % 24
    hour2entry_num[hour] += 1
    logger.debug("enterHour %d", hour)


def exit_hour_info(now_ms: float, logger: logging.Logger):
    hour = int(now_ms / common.HOUR_MILLISECOND) % 24
    hour2exit_num[hour] += 1
    logger.debug("exitHour %d", hour)


def num_passed_info(num: int, logger: logging.Logger):
    num_gantry_passed.append(num)
    logger.debug("passed %d gantry", num)


def total_time_info(now_ms: float, last_ms: float, logger: logging.Logger):
    duration = int((now_ms - last_ms) / common.SECOND_MILLISECOND)
    total_time_used.append(duration)
    logger.debug("totalTime %d s", duration)


def gantry_time_info(duration: int, logger: logging.Logger):
    d = int(duration / common.SECOND_MILLISECOND)
    gantry_time_used.append(d)
    logger.debug("thisTime %d s", d)


def exit_hex_info(h: str, logger: logging.Logger):
    exit_hex2num[h] = exit_hex2num.get(h, 0) + 1
    logger.debug("exitHex %s", h)


def entry_hex_info(h: str, logger: logging.Logger):
    entry_hex2num[h] = entry_hex2num.get(h, 0) + 1
    logger.debug("enterHex %s", h)


def record(logger: logging.Logger):
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
