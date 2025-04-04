"""
高速公路车辆生成调度模块

功能概述：
本模块实现基于时间分布的车辆生成调度系统，控制车辆入口选择和生成间隔，构成仿真系统的车辆输入源。
CarGenerator类继承salabim.Component，实现离散事件驱动的车辆生成逻辑。

执行流程：
while True:
1. 计算当前仿真时间对应的小时段
2. 获取相邻3个时段的平均间隔
3. 生成带随机波动的实际间隔
4. 创建Car实例并加入仿真队列
5. 等待计算出的时间间隔

使用示例：
```
generator = CarGenerator(road_network=rn, traffic=tf)
```
"""

import logging
import random

import highway_sim.mySalabim.d2_interface_enhanced as sim

from highway_sim.stats import default as stats_default
from highway_sim.components.car import Car
from highway_sim.config import common
from highway_sim.config import fitting_data as fit
from highway_sim.entity.location import Location

logger = logging.getLogger(__name__)


class CarGenerator(sim.Component):
    """
    CarGenerator是一个仿真组件，用于模拟车辆生成过程。
    """

    def setup(self, road_network, traffic) -> None:
        """
        初始化CarGenerator，设置道路和交通流量解析器

        Args:
            road_network (RoadNetwork): 道路解析器
            traffic (Traffic): 交通流量解析器

        Returns:

        """
        self.rn = road_network
        self.traffic = traffic

    def get_entrance(self) -> Location:
        """
        考虑交通流量和省界入口的比例, 随机选择一个入口位置

        Returns:

        """
        pe = self.rn.province_entrances
        if random.random() < fit.PROVINCE_ENTRANCE_RATION:
            return random.choice(pe)
        prob = random.random()
        cnt = 0
        for k, v in self.rn.entrances_with_prob:
            cnt += v
            if cnt > prob:
                stats_default.entry_hex_info(k.hex_code, logger)
                return k
        return random.choice(pe)

    def gen_interval_ms(self) -> int:
        """
        生成车辆生成间隔时间

        Returns:
            int: 车辆生成间隔时间（毫秒）
        """
        hour = int(self.env.now() / common.HOUR_MILLISECOND) % 24
        hours = [(hour - 1) % 24, hour, (hour + 1) % 24]
        intervals = [self.traffic.hour_2_interval_ms[h] for h in hours]
        low, high = min(intervals) - 5, max(intervals) + 5
        return int(random.uniform(low, high) * (1 - fit.PROVINCE_ENTRANCE_RATION))

    def process(self) -> None:
        """
        模拟车辆生成过程，根据交通流量生成车辆

        Returns:

        """
        while True:
            entrance = self.get_entrance()
            Car(road_network=self.rn, traffic=self.traffic, entrance=entrance)
            self.hold(self.gen_interval_ms())
