import logging

import mySalabim.d2_interface_enhanced as sim

from highway_sim.config import common
from highway_sim.config import fitting_data as fit
from highway_sim.data_parser_and_holder.road import Road
from highway_sim.data_parser_and_holder.traffic import Traffic
from highway_sim.entity.location import TollPlaza, Location
from highway_sim.stats import default as stats_default
from highway_sim.util.distribution import gamma_distribution

logger = logging.getLogger(__name__)

ENABLE_3D = True
ENABLE_2D = True


class Car(sim.Component):
    """
    Car类用于模拟高速公路上的车辆行为，继承自Salabim的Component类。

    主要功能包括：
    - 车辆初始化：根据道路网络随机选择入口位置
    - 路径选择：基于Gamma分布模拟车辆在门架间的移动时间
    - 动画渲染：支持2D/3D模式下车辆移动的实时渲染
    - 数据统计：记录车辆通过的门架数量、总行程时间等信息
    """

    def setup(self, road, traffic) -> None:
        """
        初始化Car，设置初始位置

        Args:
            road: 道路parser
            traffic: 交通流量parser

        Returns:

        """
        self.road: Road = road
        self.traffic: Traffic = traffic
        self.location: Location = self.road.get_entrance_by_prob()
        self.gantry_num: int = 1
        self.start_time: float = self.env.now()
        self.prev_location: Location = None

    def process(self) -> None:
        """
        模拟车辆行驶过程，包括路径选择、动画渲染、数据统计
        
        Returns:

        """
        stats_default.entry_hour_info(self.env.now(), logger)
        duration = 0
        if isinstance(self.location, TollPlaza):
            duration = (
                    gamma_distribution(
                        fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 10
                    )
                    * common.SECOND_MILLISECOND
            )
        else:
            duration = (
                    gamma_distribution(
                        fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 75
                    )
                    * common.SECOND_MILLISECOND
            )
            stats_default.gantry_time_info(duration, logger)
        self.prev_location = self.location
        self.location = self.location.get_next_location(True)
        self.start_time = self.env.now()

        time2x = lambda t: sim.interpolate(
            t,
            self.start_time,
            self.start_time + duration,
            self.road.lon2x(self.prev_location.longitude, 10000),
            self.road.lon2x(self.location.longitude, 10000),
        )
        time2y = lambda t: sim.interpolate(
            t,
            self.start_time,
            self.start_time + duration,
            self.road.lat2y(self.prev_location.latitude, 10000),
            self.road.lat2y(self.location.latitude, 10000),
        )
        if ENABLE_2D:
            self.animate = sim.AnimateRectangle(
                x=time2x,
                y=time2y,
                spec=(
                    -10,
                    -10,
                    10,
                    10,
                ),
                linewidth=0,
                fillcolor="black",
            )
        if ENABLE_3D:
            self.animate3d = sim.Animate3dBox(
                x=time2x,
                y=time2y,
                z=lambda t: 0.5,
                x_len=20,
                y_len=20,
                z_len=5,
                shaded=False,
            )
        self.hold(duration)
        if ENABLE_2D:
            self.animate.remove()
        if ENABLE_3D:
            self.animate3d.remove()
        while len(self.location.downstream) > 0:
            self.gantry_num += 1
            duration = (
                    gamma_distribution(
                        fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, 75
                    )
                    * common.SECOND_MILLISECOND
            )
            stats_default.gantry_time_info(duration, logger)
            self.prev_location = self.location
            self.location = self.location.get_next_location(True)

            self.start_time = self.env.now()
            time2x = lambda t: sim.interpolate(
                t,
                self.start_time,
                self.start_time + duration,
                self.road.lon2x(self.prev_location.longitude, 10000),
                self.road.lon2x(self.location.longitude, 10000),
            )
            time2y = lambda t: sim.interpolate(
                t,
                self.start_time,
                self.start_time + duration,
                self.road.lat2y(self.prev_location.latitude, 10000),
                self.road.lat2y(self.location.latitude, 10000),
            )
            if ENABLE_2D:
                self.animate = sim.AnimateRectangle(
                    x=time2x,
                    y=time2y,
                    spec=(
                        -10,
                        -10,
                        10,
                        10,
                    ),
                    linewidth=0,
                    fillcolor="black",
                )
            if ENABLE_3D:
                self.animate3d = sim.Animate3dBox(
                    x=time2x,
                    y=time2y,
                    z=lambda t: 0.5,
                    x_len=20,
                    y_len=20,
                    z_len=5,
                    shaded=False,
                )
            self.hold(duration)
            if ENABLE_2D:
                self.animate.remove()
            if ENABLE_3D:
                self.animate3d.remove()

        now = self.env.now()
        stats_default.num_passed_info(self.gantry_num, logger)
        stats_default.total_time_info(now, self.start_time, logger)
        stats_default.exit_hour_info(now, logger)
        stats_default.exit_hex_info(self.location.hex_code, logger)
