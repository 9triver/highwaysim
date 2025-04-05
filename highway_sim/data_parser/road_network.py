# 应当拆分?
# 注意,即使read_excel 设置dtype = str,遇到空值还是会转换为float(NaN),需要设置na_filter=False
# greenlet可以共享全局变量和实例,但是不能共享类变量,这是为什么呢
# greenlet貌似因为在一个线程内,所以不用加锁
# 单例模式对greenlet没用,因为greenlet会清除类变量,而单例模式_instance要用类变量
# 所以尽量不要使用类变量
# 每个 greenlet 有自己的 执行上下文（execution context），这个上下文包括栈、局部变量、寄存器等与协程执行相关的状态
#
# gantry.xlxs里面有重复数据,需要删除,否则导致出现多个hex相同但id不同的对象
"""
高速公路路网数据解析与建模模块

功能概述：
本模块负责解析高速公路基础数据文件，构建包含门架、收费站及其拓扑关系的路网模型，提供路径概率计算和地理坐标映射功能。
主要包含RoadNetwork道路网络数据容器类和Parser数据解析器类。

数据解析来源：
    1. gantry.xlsx      - 门架基础信息（经纬度、Hex编码、类型等）
    2. charge.xlsx      - 收费站信息（出入口类型、关联门架等）
    3. relation.xlsx    - 门架上下游拓扑关系
    4. hourly_entry_count.csv - 入口车流量统计，用于解析入口选择概率
    5. driver_normal.csv - 路径选择概率分布，用于解析下游门架选择概率

路网建模逻辑：
    1. 空间映射体系：
        - 通过min/max经纬度计算坐标映射比例
        - lon2x()/lat2y()方法实现经纬度到画布坐标的线性映射
        - draw()方法实现基于Tkinter的可视化绘制

    2. 拓扑关系构建：
        - 解析relation.xlsx建立门架上下游关系
        - 使用LocationWithProb对象存储带概率的下游节点
        - 入口收费站通过entrances_with_prob实现按流量加权随机

    3. 数据清洗规则：
        - 过滤状态非"运行"的收费站
        - 移除无有效下游的入口节点
        - 处理重复门架Hex编码(保留首次出现实例)

使用示例::

    parser = Parser(road_network)
    parser.parse()
    road_network.draw(canvas, 800, 600) # 在800x600画布上绘制路网
"""

from __future__ import annotations

import logging
import random
import tkinter
from typing import Dict, Tuple, List, Set

import pandas as pd

from highway_sim.config import fitting_data as fit
from highway_sim.config import resources
from highway_sim.entity import location
from highway_sim.entity.location import TollPlaza, Gantry, Location, LocationWithProb
from highway_sim.stats import default as stats_default
from highway_sim.util import parser

logger = logging.getLogger(__name__)


class RoadNetwork:
    """
    道路数据类
    包含门架、收费站信息；门架拓扑关系；下游门架选择概率；
    因为使用greenlet的原因，不能使用类变量，需要手动控制创建实例为单例
    """

    def __init__(self):
        self.id_2_gantry: Dict[str, Gantry] = {}
        # 门架与收费站hex不会相同,出入口hex相同,同一个收费站不同状态/主分站hex相同
        self.hex_2_gantry: Dict[str, Gantry] = {}
        self.hex_2_entrance: Dict[str, TollPlaza] = {}
        self.entrances: List[TollPlaza] = []
        self.valid_entrance_hex_set: Set[str] = set()
        self.hex_2_exit: Dict[str, TollPlaza] = {}
        self.province_entrances: List[Gantry] = []
        self.entrances_with_prob: List[Tuple[TollPlaza, float]] = []
        self.entrances_all: int = 0
        self.min_latitude = 90
        self.max_latitude = -90
        self.min_longitude = 180
        self.max_longitude = -180
        self.scale_factor = 1.0

    def lon2x(self, lon: float, resolution) -> float:
        """
        根据解析的门架经纬度信息，计算传入的经度在窗口中的x坐标

        Args:
            lon (float): 经度数据
            resolution (float): 窗口分辨率，即坐标轴长度

        Returns:
            float: x坐标
        """
        return (
                (lon - self.min_longitude)
                / (self.max_longitude - self.min_longitude)
                * resolution
        ) * self.scale_factor

    def lat2y(self, lat: float, resolution: float) -> float:
        """
        根据解析的门架经纬度信息，计算传入的纬度在窗口中的y坐标

        Args:
            lat (float): 纬度数据
            resolution (float): 窗口分辨率，即坐标轴长度

        Returns:
            float: y坐标
        """
        return (
            (
                    (lat - self.min_latitude)
                    / (self.max_longitude - self.min_longitude)
                    * resolution
            )
        ) * self.scale_factor

    def draw(
            self,
            cv: tkinter.Canvas,
            width: float,
            height: float,
            road_color: str = "black",
            create_oval: bool = True,
    ) -> None:
        """
        根据解析的门架信息在传入的画布中绘制地图，道路用两条门架中的线表示，可以选择是否绘制门架
        自动将门架最长轴对齐到画布的相应轴

        Args:
            cv (tkinter.Canvas): 画布对象
            width (float): 画布宽度（像素数量）
            height (float): 画布高度（像素数量）
            road_color  (str): 道路颜色
            create_oval (bool): 是否绘制门架

        Returns:

        """

        hex_drawn: Set[str] = set()

        def draw_gantry(gantry: Location, prev: Location = None):
            if gantry.hex_code in hex_drawn:
                return

            x = self.lon2x(gantry.longitude, width)
            y = height - self.lat2y(gantry.latitude, width)
            hex_drawn.add(gantry.hex_code)
            if create_oval:
                tag = cv.create_oval(x - 2, y - 2, x + 2, y + 2, fill="gray")
                cv.tag_bind(tag, "<Button-1>", lambda event: print(gantry.name))
            if prev:
                x_prev = self.lon2x(prev.longitude, width)
                y_prev = height - self.lat2y(prev.latitude, width)
                cv.create_line(x_prev, y_prev, x, y, width=1, fill=road_color)
            for e in gantry.downstream:
                draw_gantry(e.l, gantry)

        for entry in self.hex_2_entrance.values():
            if entry.hex_code not in hex_drawn:
                draw_gantry(entry)


class Parser:
    """
    高速路网络数据解析器

    从文件中解析道路数据并填充到RoadNetwork实例中
    """

    def __init__(self, road_network: RoadNetwork):
        self.road_network = road_network
        self.__ENTRANCE_INDEX = 7
        self.__ENTRANCE_NAME = "省界入口"
        self.__EXIT_NAME = "省界出口"

    def parse(self) -> None:
        """
        执行完整解析流程
        """
        self.__parse_gantry_information()
        self.__parse_toll_plaza()
        self.__parse_relation()
        self.road_network.entrances = list(self.road_network.hex_2_entrance.values())
        self.__clean_invalid_entrances()
        for e in self.entrances:
            self.road_network.valid_entrance_hex_set.add(e.hex_code)
        self.__calculate_entrance_prob()
        self.__parse_next_gantry_prob()
        gantries = list(self.road_network.hex_2_gantry.values())
        for g in gantries:
            self.road_network.min_latitude = min(self.road_network.min_latitude, g.latitude)
            self.road_network.max_latitude = max(self.road_network.max_latitude, g.latitude)
            self.road_network.min_longitude = min(self.road_network.min_longitude, g.longitude)
            self.road_network.max_longitude = max(self.road_network.max_longitude, g.longitude)

    def __parse_gantry_information(self) -> None:
        """
        未清理停用的数据,原因是gantry与relation导出时间存在差异,若清理可能导致建立relation出现问题
        """
        df = pd.read_excel(
            resources.RESOURCE_PATH + rf"{resources.PROVINCE}/gantry.xlsx",
            dtype=str,
            na_filter=False,
        )
        for row in [x[1] for x in df.iterrows()]:
            name = row.iloc[0].strip()
            id_str = row.iloc[1].strip()
            longitude = float(row.iloc[2])
            latitude = float(row.iloc[3])
            hex_code = row.iloc[4].strip()
            hex_code_of_reverse_gantry = row.iloc[5].strip()
            type_value = row.iloc[self.__ENTRANCE_INDEX].strip()
            gantry_type = (
                Gantry.Type.PROVINCE_ENTRANCE
                if type_value == self.__ENTRANCE_NAME
                else (
                    Gantry.Type.PROVINCE_EXIT
                    if type_value == self.__EXIT_NAME
                    else Gantry.Type.COMMON
                )
            )
            # 收费站id不会相同,但是hex会
            if hex_code in self.road_network.hex_2_gantry:
                self.road_network.id_2_gantry[id_str] = self.road_network.hex_2_gantry[hex_code]
                continue
            gantry = Gantry(
                name=name,
                _id=id_str,
                longitude=longitude,
                latitude=latitude,
                hex_code=hex_code,
                _hex_code_of_reverse_gantry=hex_code_of_reverse_gantry,
                _gantry_type=gantry_type,
            )
            if gantry_type == Gantry.Type.PROVINCE_ENTRANCE:
                self.road_network.province_entrances.append(gantry)
            self.road_network.id_2_gantry[id_str] = gantry
            self.road_network.hex_2_gantry[hex_code] = gantry

    def __parse_toll_plaza(self) -> None:
        df = pd.read_excel(
            resources.RESOURCE_PATH + rf"{resources.PROVINCE}/charge.xlsx",
            dtype=str,
            na_filter=False,
        )
        for row in [x[1] for x in df.iterrows()]:
            name = row.iloc[0].strip()
            id_str = row.iloc[1].strip()
            hex_code = row.iloc[2].strip()
            tmp = row.iloc[3]
            longitude = float(0 if parser.is_null_cell(tmp) else tmp)
            tmp = row.iloc[4]
            latitude = float(0 if parser.is_null_cell(tmp) else tmp)
            tmp = row.iloc[5].strip()
            gantry_id = "null" if parser.is_null_cell(tmp) else tmp
            status_str = row.iloc[6]

            if status_str != "运行" or "分站" in name:
                continue
            if any(x in name for x in ["入口", "外"]):
                self.__add_2_hex_2_entrance(
                    name, id_str, longitude, latitude, hex_code, gantry_id
                )
            elif any(x in name for x in ["出口", "内"]):
                self.__add_2_hex_2_exit(
                    name, id_str, longitude, latitude, hex_code, gantry_id
                )
            else:
                self.__add_2_hex_2_entrance(
                    name, id_str, longitude, latitude, hex_code, gantry_id
                )
                self.__add_2_hex_2_exit(
                    name, id_str, longitude, latitude, hex_code, gantry_id
                )

    def __add_2_hex_2_entrance(self, n, i, lo, la, h, g) -> None:
        t = TollPlaza.Type.ENTRANCE
        tp = TollPlaza(
            name=n,
            _id=i,
            longitude=lo,
            latitude=la,
            hex_code=h,
            _tp_type=t,
            _supported_gantry_id=g,
        )
        self.road_network.hex_2_entrance[h] = tp

    def __add_2_hex_2_exit(self, n, i, lo, la, h, g) -> None:
        t = TollPlaza.Type.EXIT
        tp = TollPlaza(
            name=n,
            _id=i,
            longitude=lo,
            latitude=la,
            hex_code=h,
            _tp_type=t,
            _supported_gantry_id=g,
        )
        self.road_network.hex_2_exit[h] = tp

    def __parse_relation(self) -> None:
        """
        上下游hex中可能出现门架和收费站的hex, 但是id只会出现门架的id
        若上下游hex中出现收费站hex,则门架id必是该收费站承载门架的id?
        如果是这样感觉可以在parse_toll_plaza处理收费站上下游关系
        """
        df = pd.read_excel(
            resources.RESOURCE_PATH + rf"{resources.PROVINCE}/relation.xlsx",
            dtype=str,
            na_filter=False,
        )
        for row in [x[1] for x in df.iterrows()]:
            id_str = row.iloc[0].strip()
            up_hexs = row.iloc[1].strip()
            down_hexs = row.iloc[2].strip()

            if id_str not in self.road_network.id_2_gantry:
                continue

            gantry = self.road_network.id_2_gantry[id_str]
            if not parser.is_null_cell(up_hexs):
                hexs: List[str] = up_hexs.split(r"|")
                for h in hexs:
                    h = h.strip()
                    if h in self.road_network.hex_2_entrance:
                        tmp = self.road_network.hex_2_entrance[h]
                        tmp.downstream.append(LocationWithProb(gantry, 0))
                        gantry.upstream.append(tmp)
                    elif h in self.road_network.hex_2_gantry:
                        tmp = self.road_network.hex_2_gantry[h]
                        gantry.upstream.append(tmp)

            if not parser.is_null_cell(down_hexs):
                hexs: List[str] = down_hexs.split(r"|")
                for h in hexs:
                    h = h.strip()
                    if h in self.road_network.hex_2_exit:
                        tmp = self.road_network.hex_2_exit[h]
                        tmp.upstream.append(gantry)
                        gantry.downstream.append(LocationWithProb(tmp, 0))
                    elif h in self.road_network.hex_2_gantry:
                        tmp = self.road_network.hex_2_gantry[h]
                        gantry.downstream.append(LocationWithProb(tmp, 0))

    def __clean_invalid_entrances(self) -> None:
        """
        verified
        """
        self.province_entrances = [
            x for x in self.road_network.province_entrances if len(x.downstream) > 0
        ]
        self.entrances = [x for x in self.road_network.entrances if len(x.downstream) > 0]

    def __calculate_entrance_prob(self) -> None:
        # verified
        df = pd.read_csv(
            resources.RESOURCE_PATH
            + rf"{resources.PROVINCE}/statisticalData/hourly_entry_count.csv",
            dtype=str,
            na_filter=False,
        )
        hex_2_count = {}
        for row in [x[1] for x in df.iterrows()]:
            h = row.iloc[0].strip()
            if h in self.road_network.valid_entrance_hex_set:
                num = int(row.iloc[2])
                self.road_network.entrances_all += num
                hex_2_count[h] = num + hex_2_count.get(h, 0)
        for k, v in hex_2_count.items():
            self.road_network.entrances_with_prob.append(
                (self.road_network.hex_2_entrance[k], v / self.road_network.entrances_all)
            )

    def __parse_next_gantry_prob(self) -> None:
        # 文件中的hex_code都是gantry的
        # verified
        df = pd.read_csv(
            resources.RESOURCE_PATH
            + rf"{resources.PROVINCE}/statisticalData/driver_normal.csv",
            dtype=str,
            na_filter=False,
        )
        location.enable_get_next_by_prob = True
        for row in [x[1] for x in df.iterrows()]:
            up_hex = row.iloc[0].strip()
            down_hex = row.iloc[1].strip()
            p = float(row.iloc[2])
            up = self.road_network.hex_2_gantry[up_hex]
            for lwp in up.downstream:
                if lwp.l.hex_code == down_hex:
                    lwp.p = float(p)
                    break
