from __future__ import annotations

from dataclasses import dataclass, field

from .expressions import Expr
from .node import Node

@dataclass(slots=True)
class Decl(Node):
    pass

@dataclass(slots=True)
class TypeDecl(Decl):
    base_type: str = ""
    names: list[str] = field(default_factory=list)
    length: int | None = None          # untuk CHARACTER

@dataclass(slots=True)
class ArrayDecl(Decl):
    base_type: str = ""
    name: str = ""
    dimensions: list[Expr] = field(default_factory=list)

@dataclass(slots=True)
class ImplicitNoneDecl(Decl):
    pass

@dataclass(slots=True)
class CommonDecl(Decl):
    block_name: str = ""
    variables: list[str] = field(default_factory=list)