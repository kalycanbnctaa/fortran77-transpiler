from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from src.ast import Expr

class SymbolKind(Enum):
    VARIABLE = auto()
    ARRAY = auto()
    SUBROUTINE = auto()
    FUNCTION = auto()
    PROGRAM = auto()

@dataclass(slots=True)
class Symbol:
    name: str
    kind: SymbolKind
    data_type: str = ""
    dimensions: list[Expr] = field(default_factory=list)
    is_parameter: bool = False
    common_block: str | None = None
    common_index: int = -1
    line: int = 0
    length: int | None = None          

    @property
    def rank(self) -> int:
        return len(self.dimensions)

@dataclass(slots=True)
class ParamInfo:
    data_type: str
    rank: int = 0