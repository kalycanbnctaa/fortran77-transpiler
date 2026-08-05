from __future__ import annotations

from dataclasses import dataclass, field

from .node import Node

@dataclass(slots=True)
class Expr(Node):
    pass

@dataclass(slots=True)
class IntLiteral(Expr):
    value: int = 0

@dataclass(slots=True)
class RealLiteral(Expr):
    value: float = 0.0

@dataclass(slots=True)
class LogicalLiteral(Expr):
    value: bool = False

@dataclass(slots=True)
class CharacterLiteral(Expr):
    value: str = ""

@dataclass(slots=True)
class Identifier(Expr):
    name: str = ""

@dataclass(slots=True)
class ArrayRef(Expr):
    name: str = ""
    indices: list[Expr] = field(default_factory=list)

@dataclass(slots=True)
class FunctionCall(Expr):
    name: str = ""
    args: list[Expr] = field(default_factory=list)

@dataclass(slots=True)
class BinaryOp(Expr):
    operator: str = ""
    left: Expr | None = None
    right: Expr | None = None

@dataclass(slots=True)
class UnaryOp(Expr):
    operator: str = ""
    operand: Expr | None = None