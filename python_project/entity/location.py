from __future__ import annotations

import enum
import random
from abc import ABC
from dataclasses import dataclass, field
from typing import List, ClassVar, Optional


@dataclass
class LocationWithProb:
    l: Location
    p: float


@dataclass
class Location(ABC):
    enable_get_next_by_prob: ClassVar[bool] = False
    name: str = ""
    id: str = ""
    hex_code: str = ""
    longitude: float = 0
    latitude: float = 0
    upstream: List[Location] = field(default_factory=list)
    # 对downstream的操作需要取第一个或任意一个元素,换用dict会比较麻烦
    # 因为每个gantry的downstream不多,在parse数据时不使用dict影响不大
    downstream: List[LocationWithProb] = field(default_factory=list)

    def get_next_location(self, enable_prob: bool = False) -> Optional[Location, None]:
        if len(self.downstream) == 0:
            return None
        if enable_prob and self.enable_get_next_by_prob and self.downstream[0].p != 0:
            p = random.random()
            cnt = 0
            for lo, f in self.downstream:
                cnt += f
                if cnt > p:
                    return lo
            return self.downstream[-1].l
        return random.choice(self.downstream).l


@dataclass
class Gantry(Location):
    class Type(enum.Enum):
        COMMON = enum.auto()
        PROVINCE_ENTRANCE = enum.auto()
        PROVINCE_EXIT = enum.auto()

    hex_code_of_reverse_gantry: str = ""
    gantry_type: Type = Type.COMMON


@dataclass
class TollPlaza(Location):
    class Type(enum.Enum):
        ENTRANCE = enum.auto()
        EXIT = enum.auto()

    tp_type: Type = Type.ENTRANCE
    supported_gantry_id: str = "null"
