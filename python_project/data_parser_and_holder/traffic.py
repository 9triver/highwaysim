from __future__ import annotations

from typing import Dict

import pandas as pd

from config import resources


class Traffic:
    hour_2_interval_ms: Dict[int, float]

    @classmethod
    def parse(cls) -> None:
        cls.__parse_traffic_distribution()

    @classmethod
    def __parse_traffic_distribution(cls) -> None:
        df = pd.read_csv(
            resources.RESOURCE_PATH
            + rf"{resources.PROVINCE}/statisticalData/hourly_traffic_distribution.csv",
            dtype=str,
        )
        for row in [x[1] for x in df.iterrows()]:
            hour = int(row.iloc[0])
            interval = float(row.iloc[2])
            cls.hour_2_interval_ms[hour] = interval
