from __future__ import annotations

import enum
import random
from abc import ABC
from dataclasses import dataclass, field
from typing import List, Tuple, ClassVar, Optional


@dataclass
class Location(ABC):
    enable_get_next_by_prob: ClassVar[bool] = False
    name: str = ""
    id: str = ""
    hex_code: str = ""
    longitude: float = 0
    latitude: float = 0
    upstream: List[Tuple[Location, float]] = field(default_factory=list)
    downstream: List[Tuple[Location, float]] = field(default_factory=list)

    def get_next_location(self, enable_prob: bool = False) -> Optional[Location, None]:
        if len(self.downstream) == 0:
            return None
        if enable_prob and self.enable_get_next_by_prob and self.downstream[0][1] != 0:
            p = random.random()
            cnt = 0
            for lo, f in self.downstream:
                cnt += f
                if cnt > p:
                    return lo
            return self.downstream[-1]
        return self.downstream[random.randint(0, len(self.downstream) - 1)]


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
