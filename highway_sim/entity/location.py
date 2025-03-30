from __future__ import annotations

import enum
import logging
import random
from abc import ABC
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LocationWithProb:
    l: Location
    p: float


enable_get_next_by_prob: bool = True


@dataclass(repr=False)
class Location(ABC):
    name: str = ""
    id: str = ""
    hex_code: str = ""
    longitude: float = 0
    latitude: float = 0
    # 这里有嵌套结构,导致自动生成repr异常
    upstream: List[Location] = field(default_factory=list)
    # 对downstream的操作需要取第一个或任意一个元素,换用dict会比较麻烦
    # 因为每个gantry的downstream不多,在parse数据时不使用dict影响不大
    downstream: List[LocationWithProb] = field(default_factory=list)

    def get_next_location(self, enable_prob: bool = False) -> Optional[Location, None]:
        if len(self.downstream) == 0:
            return None
        if not (enable_prob and enable_get_next_by_prob):
            return random.choice(self.downstream).l
        # if len(self.hex_code) != 8:
        #     logger.warning("%s %s", self.hex_code, hex(id(self)))
        #     logger.warning({x.l.hex_code: x.p for x in self.downstream})
        r = random.random()
        cnt: float = 0.0
        for lwp in self.downstream:
            lo = lwp.l
            p = lwp.p
            # if len(self.hex_code) != 8:
            #     logger.warning("%s %f", lo.hex_code, p)
            cnt += p
            if cnt >= r:
                # logger.warning("next with prob %f %f", cnt, r)
                return lo
        # if len(self.hex_code) != 8:
        #     logger.warning("next without prob")
        return random.choice(self.downstream).l

    def __repr__(self):
        return f"Location(name={self.name}, id={self.id}, hex={self.hex_code}, longitude={self.longitude}, latitude={self.latitude})"


@dataclass(repr=False)
class Gantry(Location):
    class Type(enum.Enum):
        COMMON = enum.auto()
        PROVINCE_ENTRANCE = enum.auto()
        PROVINCE_EXIT = enum.auto()

        def __str__(self):
            return self.name

    hex_code_of_reverse_gantry: str = ""
    gantry_type: Type = Type.COMMON

    def __repr__(self):
        return super().__repr__() + str(self.gantry_type)


@dataclass(repr=False)
class TollPlaza(Location):
    class Type(enum.Enum):
        ENTRANCE = enum.auto()
        EXIT = enum.auto()

        def __str__(self):
            return self.name

    tp_type: Type = Type.ENTRANCE
    supported_gantry_id: str = "null"

    def __repr__(self):
        return super().__repr__() + str(self.tp_type)
