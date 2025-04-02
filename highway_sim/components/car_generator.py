import random

import mySalabim.d2_interface_enhanced as sim

from highway_sim.components.car import Car
from highway_sim.config import common
from highway_sim.config import fitting_data as fit


class CarGenerator(sim.Component):
    """
    CarGenerator是一个仿真组件，用于模拟车辆生成过程。
    """

    def setup(self, road, traffic) -> None:
        """
        初始化CarGenerator，设置道路和交通流量解析器

        Args:
            road (Road): 道路解析器
            traffic (Traffic): 交通流量解析器

        Returns:

        """
        self.road = road
        self.traffic = traffic

    def process(self) -> None:
        """
        模拟车辆生成过程，根据交通流量生成车辆

        Returns:

        """
        while True:
            Car(road=self.road, traffic=self.traffic)
            self.hold(self.__gen_interval_ms())

    def __gen_interval_ms(self) -> int:
        hour: int = int(self.env.now() / common.HOUR_MILLISECOND) % 24
        interval1 = self.traffic.hour_2_interval_ms[(hour + 23) % 24]
        interval2 = self.traffic.hour_2_interval_ms[hour]
        interval3 = self.traffic.hour_2_interval_ms[(hour + 1) % 24]
        low = min(interval1, interval2, interval3) - 5
        high = max(interval1, interval2, interval3) + 5
        return int(
            (low + random.random() * (high - low)) * (1 - fit.PROVINCE_ENTRANCE_RATION)
        )
