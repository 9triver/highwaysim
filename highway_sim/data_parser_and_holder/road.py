"""
应当拆分,道路信息和流量信息已经揉到一起了
parser和holder也应当拆分?
注意,及时read_excel 设置dtype = str,遇到空值还是会转换为float(NaN),需要设置na_filter=False
greenlet可以共享全局变量和实例,但是不能共享类变量,这是为什么呢
greenlet貌似因为在一个线程内,所以不用加锁
单例模式对greenlet没用,因为greenlet会清楚类变量,而单例模式_instance要用类变量
所以尽量不要使用类变量
每个 greenlet 有自己的 执行上下文（execution context），这个上下文包括栈、局部变量、寄存器等与协程执行相关的状态
"""

from __future__ import annotations

import random
from typing import Dict, Tuple, List, Set

import pandas as pd

from highway_sim.config import fitting_data as fit
from highway_sim.config import resources
from highway_sim.entity import location
from highway_sim.entity.location import TollPlaza, Gantry, Location, LocationWithProb
from highway_sim.util import parser


class Road:
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

    ENTRANCE_INDEX = 7
    ENTRANCE_NAME = "省界入口"
    EXIT_NAME = "省界出口"

    def parse(self) -> None:
        self.__parse_gantry_information()
        self.__parse_toll_plaza()
        self.__parse_relation()
        self.entrances = list(self.hex_2_entrance.values())
        self.__clean_invalid_entrances()
        for e in self.entrances:
            self.valid_entrance_hex_set.add(e.hex_code)
        self.__calculate_entrance_prob()
        self.__parse_next_gantry_prob()

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
            type_value = row.iloc[self.ENTRANCE_INDEX].strip()
            gantry_type = (
                Gantry.Type.PROVINCE_ENTRANCE
                if type_value == self.ENTRANCE_NAME
                else (
                    Gantry.Type.PROVINCE_EXIT
                    if type_value == self.EXIT_NAME
                    else Gantry.Type.COMMON
                )
            )
            gantry = Gantry(
                name=name,
                id=id_str,
                longitude=longitude,
                latitude=latitude,
                hex_code=hex_code,
                hex_code_of_reverse_gantry=hex_code_of_reverse_gantry,
                gantry_type=gantry_type,
            )

            if gantry_type == Gantry.Type.PROVINCE_ENTRANCE:
                self.province_entrances.append(gantry)
            self.id_2_gantry[id_str] = gantry
            self.hex_2_gantry[hex_code] = gantry

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
            id=i,
            longitude=lo,
            latitude=la,
            hex_code=h,
            tp_type=t,
            supported_gantry_id=g,
        )
        self.hex_2_entrance[h] = tp

    def __add_2_hex_2_exit(self, n, i, lo, la, h, g) -> None:
        t = TollPlaza.Type.EXIT
        tp = TollPlaza(
            name=n,
            id=i,
            longitude=lo,
            latitude=la,
            hex_code=h,
            tp_type=t,
            supported_gantry_id=g,
        )
        self.hex_2_exit[h] = tp

    def __parse_relation(self) -> None:
        """
        上下游hex中可能出现门架和收费站的hex, 但是id只会出现门架的id
        若上下游hex中出现收费站hex,则门架id必是改收费站承载门架的id?
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

            if id_str not in self.id_2_gantry:
                continue

            gantry = self.id_2_gantry[id_str]
            if not parser.is_null_cell(up_hexs):
                hexs: List[str] = up_hexs.split(r"|")
                for h in hexs:
                    h = h.strip()
                    if h in self.hex_2_entrance:
                        tmp = self.hex_2_entrance[h]
                        tmp.downstream.append(LocationWithProb(gantry, 0))
                        gantry.upstream.append(tmp)
                    elif h in self.hex_2_gantry:
                        tmp = self.hex_2_gantry[h]
                        gantry.upstream.append(tmp)

            if not parser.is_null_cell(down_hexs):
                hexs: List[str] = down_hexs.split(r"|")
                for h in hexs:
                    h = h.strip()
                    if h in self.hex_2_exit:
                        tmp = self.hex_2_exit[h]
                        tmp.upstream.append(gantry)
                        gantry.downstream.append(LocationWithProb(tmp, 0))
                    elif h in self.hex_2_gantry:
                        tmp = self.hex_2_gantry[h]
                        gantry.downstream.append(LocationWithProb(tmp, 0))

    def __clean_invalid_entrances(self) -> None:
        self.province_entrances = [
            x for x in self.province_entrances if len(x.downstream) > 0
        ]
        self.entrances = [x for x in self.entrances if len(x.downstream) > 0]

    def __calculate_entrance_prob(self) -> None:
        df = pd.read_csv(
            resources.RESOURCE_PATH
            + rf"{resources.PROVINCE}/statisticalData/hourly_entry_count.csv",
            dtype=str,
            na_filter=False,
        )
        total_num = 0
        hex_2_count = {}
        for row in [x[1] for x in df.iterrows()]:
            h = row.iloc[0].strip()
            if h in self.valid_entrance_hex_set:
                num = int(row.iloc[2])
                total_num += num
                hex_2_count[h] = num + hex_2_count.get(h, 0)
        for k, v in hex_2_count.items():
            self.entrances_with_prob.append((self.hex_2_entrance[k], v / total_num))

    def __parse_next_gantry_prob(self) -> None:
        # 文件中的hex_code都是gantry的
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
            up = self.hex_2_gantry[up_hex]
            for lwp in up.downstream:
                if lwp.l.hex_code == down_hex:
                    lwp.p = p

    def get_entrance_by_prob(self) -> Location:
        if random.random() < fit.PROVINCE_ENTRANCE_RATION:
            return random.choice(self.province_entrances)
        p = random.random()
        cnt = 0
        for k, v in self.entrances_with_prob:
            cnt += v
            if cnt > p:
                return k
        return (self.entrances_with_prob[-1])[0]
