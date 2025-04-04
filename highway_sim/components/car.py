import logging
import random

import highway_sim.mySalabim.d2_interface_enhanced as sim

from highway_sim.config import common
from highway_sim.config import fitting_data as fit
from highway_sim.data_parser.road_network import RoadNetwork
from highway_sim.data_parser.traffic import Traffic
from highway_sim.entity.location import TollPlaza, Location
from highway_sim.stats import default as stats_default
from highway_sim.util.distribution import gamma_distribution
import highway_sim.config.args as args

logger = logging.getLogger(__name__)


class Car(sim.Component):
    """
    Car类用于模拟高速公路上的车辆行为，继承自Salabim的Component类。

    主要功能包括：
    - 车辆初始化：根据道路网络随机选择入口位置
    - 路径选择：基于Gamma分布模拟车辆在门架间的移动时间
    - 动画渲染：支持2D/3D模式下车辆移动的实时渲染
    - 数据统计：记录车辆通过的门架数量、总行程时间等信息
    """

    def setup(self, road_network: RoadNetwork, traffic: Traffic, entrance: Location) -> None:
        """
        初始化Car并设置初始位置

        Args:
            road_network (RoadNetwork): 道路网络
            traffic (Traffic): 交通流量
            entrance（Location)： 入口位置

        Returns:

        """
        self.rn: RoadNetwork = road_network
        self.traffic: Traffic = traffic
        self.location: Location = entrance
        self.gantry_num: int = 1
        self.start_time: float = self.env.now()
        self.prev_location: Location = None

    def get_next_location(self) -> Location:
        """
        选择下一个位置，根据当前位置和交通流量信息进行选择

        Returns:
            Location: 下一个位置
        """
        return self.location.get_next_location(True)

    @classmethod
    def get_duration(cls, is_gantry: bool = True) -> int:
        """
        生成车辆移动到达下一个位置的时间

        Returns:
            int: 移动时间（毫秒）
        """
        if is_gantry:
            times = 75
        else:
            times = 10
        return gamma_distribution(
            fit.NEXT_GANTRY_GAMMA_ALPHA, fit.NEXT_GANTRY_GAMMA_BETA, times
        ) * common.SECOND_MILLISECOND

    def draw(self, duration: int, enable_2d: bool, enable_3d: bool) -> None:
        """
        绘制车辆的动画

        Args:
            duration (int): 动画持续时间
            enable_2d (bool): 启用2D动画
            enable_3d (bool): 启用3D动画

        Returns:

        """
        time2x = lambda t: sim.interpolate(
            t,
            self.start_time,
            self.start_time + duration,
            self.rn.lon2x(self.prev_location.longitude, 10000),
            self.rn.lon2x(self.location.longitude, 10000),
        )
        time2y = lambda t: sim.interpolate(
            t,
            self.start_time,
            self.start_time + duration,
            self.rn.lat2y(self.prev_location.latitude, 10000),
            self.rn.lat2y(self.location.latitude, 10000),
        )

        if args.ENABLE_2D:
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
        if args.ENABLE_3D:
            self.animate3d = sim.Animate3dBox(
                x=time2x,
                y=time2y,
                z=lambda t: 0.5,
                x_len=20,
                y_len=20,
                z_len=5,
                shaded=False,
            )

    def remove_animation(self, enable_2d: bool, enable_3d: bool) -> None:
        """
        移除车辆的动画

        Args:
            enable_2d (bool): 启用2D动画
            enable_3d (bool): 启用3D动画

        Returns:

        """
        if enable_2d:
            self.animate.remove()
        if enable_3d:
            self.animate3d.remove()

    def process(self) -> None:
        """
        模拟车辆行驶过程，包括路径选择、动画渲染、数据统计
        
        Returns:

        """
        stats_default.entry_hour_info(self.env.now(), logger)
        duration = 0
        if isinstance(self.location, TollPlaza):
            duration = self.get_duration(is_gantry=False)
        else:
            duration = self.get_duration(is_gantry=True)
            stats_default.gantry_time_info(duration, logger)
        self.prev_location = self.location
        self.location = self.get_next_location()
        self.start_time = self.env.now()

        self.draw(duration, args.ENABLE_2D, args.ENABLE_3D)
        self.hold(duration)
        self.remove_animation(args.ENABLE_2D, args.ENABLE_3D)
        while len(self.location.downstream) > 0:
            self.gantry_num += 1
            duration = self.get_duration(is_gantry=True)
            stats_default.gantry_time_info(duration, logger)
            self.prev_location = self.location
            self.location = self.get_next_location()

            self.start_time = self.env.now()
            self.draw(duration, args.ENABLE_2D, args.ENABLE_3D)
            self.hold(duration)
            self.remove_animation(args.ENABLE_2D, args.ENABLE_3D)

        now = self.env.now()
        stats_default.num_passed_info(self.gantry_num, logger)
        stats_default.total_time_info(now, self.start_time, logger)
        stats_default.exit_hour_info(now, logger)
        stats_default.exit_hex_info(self.location.hex_code, logger)
