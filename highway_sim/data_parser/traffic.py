"""
高速公路交通流量数据解析与建模模块

功能概述：
    本模块负责解析小时级交通流量分布数据，建立时间间隔模型用于车辆生成调度。
    包含Traffic交通流量数据容器和Parser数据解析器两个核心类。

数据解析来源：
    hourly_traffic_distribution.csv - 小时级车辆到达间隔时间分布数据

使用示例::

    parser = Parser(traffic)
    parser.parse()
"""

from __future__ import annotations

from typing import Dict

import pandas as pd

from highway_sim.config import resources


class Traffic:
    """
    Traffic类用于解析并存储交通流量相关数据，如入口的流量分布等
    """

    def __init__(self):
        self.hour_2_interval_ms: Dict[int, float] = {}


class Parser:
    """
    Parser类用于解析交通流量数据
    """

    def __init__(self, traffic: Traffic):
        self.traffic = traffic

    def __parse_traffic_distribution(self) -> None:
        df = pd.read_csv(
            resources.RESOURCE_PATH
            + rf"{resources.PROVINCE}/statisticalData/hourly_traffic_distribution.csv",
            dtype=str,
            na_filter=False,
        )
        for row in [x[1] for x in df.iterrows()]:
            hour = int(row.iloc[0])
            interval = float(row.iloc[2])
            self.traffic.hour_2_interval_ms[hour] = interval

    def parse(self) -> None:
        """
        解析交通流量数据

        Returns:

        """
        self.__parse_traffic_distribution()
