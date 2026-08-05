from __future__ import annotations

from dataclasses import dataclass, field

from .declarations import Decl
from .node import Node
from .statements import Stmt


@dataclass(slots=True)
class Subprogram(Node):
    name: str = ""
    params: list[str] = field(default_factory=list)
    declarations: list[Decl] = field(default_factory=list)
    body: list[Stmt] = field(default_factory=list)


@dataclass(slots=True)
class Program(Subprogram):
    pass


@dataclass(slots=True)
class Subroutine(Subprogram):
    pass


@dataclass(slots=True)
class Function(Subprogram):
    return_type: str = ""


@dataclass(slots=True)
class TranslationUnit(Node):
    program: Program | None = None
    subprograms: list[Subprogram] = field(default_factory=list)