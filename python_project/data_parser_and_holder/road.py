"""
应当拆分,道路信息和流量信息已经揉到一起了
parser和holder也应当拆分
"""

from __future__ import annotations

import random
from typing import Dict, Tuple, List

import pandas as pd

from config import fitting_data as fit
from config import resources
from entity.location import TollPlaza, Gantry, Location, LocationWithProb


class Road:
    class Util:
        @staticmethod
        def is_null_cell(cell: object) -> bool:
            return pd.isnull(cell) or cell in ["", "(null)", "null", "nan", "none"]

    id_2_gantry: Dict[str, Gantry] = {}
    # 门架与收费站hex不会相同,出入口hex相同,同一个收费站不同状态/主分站hex相同
    hex_2_gantry: Dict[str, Gantry] = {}
    hex_2_entrance: Dict[str, TollPlaza] = {}
    entrances: List[TollPlaza] = []
    valid_entrance_hex_list: List[str] = []
    hex_2_exit: Dict[str, TollPlaza] = {}
    province_entrances: List[Gantry] = []
    entrances_with_prob: List[Tuple[TollPlaza, float]] = []

    ENTRANCE_INDEX = 7
    ENTRANCE_NAME = "省界入口"
    EXIT_NAME = "省界出口"

    @classmethod
    def parse(cls) -> None:
        cls.__parse_gantry_information()
        cls.__parse_toll_plaza()
        cls.__parse_relation()
        cls.entrances = list(cls.hex_2_entrance.values())
        cls.__clean_invalid_entrances()
        for e in cls.entrances:
            cls.valid_entrance_hex_list.append(e.hex_code)
        cls.__calculate_entrance_prob()
        cls.__parse_next_gantry_prob()

    @classmethod
    def __parse_gantry_information(cls) -> None:
        """
        未清理停用的数据,原因是gantry与relation导出时间存在差异,若清理可能导致建立relation出现问题
        """
        df = pd.read_excel(
            resources.RESOURCE_PATH + rf"{resources.PROVINCE}/gantry.xlsx", dtype=str
        )
        for row in [x[1] for x in df.iterrows()]:
            name = row.iloc[0].strip()
            id_str = row.iloc[1].strip()
            longitude = float(row.iloc[2])
            latitude = float(row.iloc[3])
            hex_code = row.iloc[4].strip()
            hex_code_of_reverse_gantry = row.iloc[5].strip()
            type_value = row.iloc[cls.ENTRANCE_INDEX].strip()
            gantry_type = (
                Gantry.Type.PROVINCE_ENTRANCE
                if type_value == cls.ENTRANCE_NAME
                else (
                    Gantry.Type.PROVINCE_EXIT
                    if type_value == cls.EXIT_NAME
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
                cls.province_entrances.append(gantry)
            cls.id_2_gantry[id_str] = gantry
            cls.hex_2_gantry[hex_code] = gantry

    @classmethod
    def __parse_toll_plaza(cls) -> None:
        df = pd.read_excel(
            resources.RESOURCE_PATH + rf"{resources.PROVINCE}/charge.xlsx", dtype=str
        )
        for row in [x[1] for x in df.iterrows()]:
            name = row.iloc[0].strip()
            id_str = row.iloc[1].strip()
            hex_code = row.iloc[2].strip()
            tmp = row.iloc[3]
            longitude = float(0 if cls.Util.is_null_cell(tmp) else tmp)
            tmp = row.iloc[4]
            latitude = float(0 if cls.Util.is_null_cell(tmp) else tmp)
            tmp = row.iloc[5].strip()
            gantry_id = "null" if cls.Util.is_null_cell(tmp) else tmp
            status_str = row.iloc[6]

            if status_str != "运行" or "分站" in name:
                continue
            if any(x in name for x in ["入口", "外"]):
                cls.__add_2_hex_2_entrance(
                    name, id_str, longitude, latitude, hex_code, gantry_id
                )
            elif any(x in name for x in ["出口", "内"]):
                cls.__add_2_hex_2_exit(
                    name, id_str, longitude, latitude, hex_code, gantry_id
                )
            else:
                cls.__add_2_hex_2_entrance(
                    name, id_str, longitude, latitude, hex_code, gantry_id
                )
                cls.__add_2_hex_2_exit(
                    name, id_str, longitude, latitude, hex_code, gantry_id
                )

    @classmethod
    def __add_2_hex_2_entrance(cls, n, i, lo, la, h, g) -> None:
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
        cls.hex_2_entrance[h] = tp

    @classmethod
    def __add_2_hex_2_exit(cls, n, i, lo, la, h, g) -> None:
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
        cls.hex_2_exit[h] = tp

    @classmethod
    def __parse_relation(cls) -> None:
        """
        上下游hex中可能出现门架和收费站的hex, 但是id只会出现门架的id
        若上下游hex中出现收费站hex,则门架id必是改收费站承载门架的id?
        如果是这样感觉可以在parse_toll_plaza处理收费站上下游关系
        """
        df = pd.read_excel(
            resources.RESOURCE_PATH + rf"{resources.PROVINCE}/relation.xlsx", dtype=str
        )
        for row in [x[1] for x in df.iterrows()]:
            id_str = row.iloc[0].strip()
            up_hexs = row.iloc[1].strip()
            down_hexs = row.iloc[2].strip()

            if id_str not in cls.id_2_gantry:
                continue

            gantry = cls.id_2_gantry[id_str]
            if not cls.Util.is_null_cell(up_hexs):
                hexs: List[str] = up_hexs.split(r"|")
                for h in hexs:
                    h = h.strip()
                    if h in cls.hex_2_entrance:
                        tmp = cls.hex_2_entrance[h]
                        tmp.downstream.append(LocationWithProb(gantry, 0))
                        gantry.upstream.append(tmp)
                    elif h in cls.hex_2_gantry:
                        tmp = cls.hex_2_gantry[h]
                        gantry.upstream.append(tmp)

            if not cls.Util.is_null_cell(down_hexs):
                hexs: List[str] = down_hexs.split(r"|")
                for h in hexs:
                    h = h.strip()
                    if h in cls.hex_2_exit:
                        tmp = cls.hex_2_exit[h]
                        tmp.upstream.append(gantry)
                        gantry.downstream.append(LocationWithProb(tmp, 0))
                    elif h in cls.hex_2_gantry:
                        tmp = cls.hex_2_gantry[h]
                        gantry.downstream.append(LocationWithProb(tmp, 0))

    @classmethod
    def __clean_invalid_entrances(cls) -> None:
        cls.province_entrances = [
            x for x in cls.province_entrances if len(x.downstream) > 0
        ]
        cls.entrances = [x for x in cls.entrances if len(x.downstream) > 0]

    @classmethod
    def __calculate_entrance_prob(cls) -> None:
        df = pd.read_csv(
            resources.RESOURCE_PATH
            + rf"{resources.PROVINCE}/statisticalData/hourly_entry_count.csv",
            dtype=str,
        )
        total_num = 0
        hex_2_count = {}
        for row in [x[1] for x in df.iterrows()]:
            h = row.iloc[0].strip()
            if h in cls.valid_entrance_hex_list:
                num = int(row.iloc[2])
                total_num += num
                hex_2_count[h] = num + hex_2_count.get(h, 0)
        for k, v in hex_2_count.items():
            cls.entrances_with_prob.append((cls.hex_2_entrance[k], v / total_num))

    @classmethod
    def __parse_next_gantry_prob(cls) -> None:
        # 文件中的hex_code都是gantry的
        df = None
        try:
            df = pd.read_csv(
                resources.RESOURCE_PATH
                + rf"{resources.PROVINCE}/statisticalData/driver_normal.csv",
                dtype=str,
            )
        except FileNotFoundError:
            pass
        Location.enable_get_next_by_prob = True
        for row in [x[1] for x in df.iterrows()]:
            up_hex = row.iloc[0].strip()
            down_hex = row.iloc[1].strip()
            p = float(row.iloc[2])
            up = cls.hex_2_gantry[up_hex]
            for lwp in up.downstream:
                if lwp.l.hex_code == down_hex:
                    lwp.p = p

    @classmethod
    def get_entrance_by_prob(cls) -> Location:
        if random.random() < fit.PROVINCE_ENTRANCE_RATION:
            return cls.province_entrances[
                random.randint(0, len(cls.province_entrances) - 1)
            ]
        p = random.random()
        cnt = 0
        for k, v in cls.entrances_with_prob:
            cnt += v
            if cnt > p:
                return k
        return cls.entrances_with_prob[
            random.randint(0, len(cls.entrances_with_prob) - 1)
        ][0]
