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

    def parse(self) -> None:
        """
        解析流量相关数据，如入口的流量分布，并存储

        Returns:

        """
        self.__parse_traffic_distribution()

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
            self.hour_2_interval_ms[hour] = interval
