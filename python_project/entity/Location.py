from __future__ import annotations

import enum
from abc import ABC
from dataclasses import dataclass, field
from typing import List


@dataclass
class Location(ABC):
    name: str = ""
    id: str = ""
    hex_code: str = ""
    longitude: float = 0
    latitude: float = 0
    upstream: List[Location] = field(default_factory=list)
    downstream: List[Location] = field(default_factory=list)


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
