from __future__ import annotations

from dataclasses import dataclass, field

from .expressions import Expr
from .node import Node

@dataclass(slots=True)
class Stmt(Node):
    label: int | None = None

@dataclass(slots=True)
class Assignment(Stmt):
    target: Expr | None = None
    value: Expr | None = None

@dataclass(slots=True)
class IfStmt(Stmt):
    condition: Expr | None = None
    then_body: list[Stmt] = field(default_factory=list)
    else_body: list[Stmt] = field(default_factory=list)

@dataclass(slots=True)
class DoStmt(Stmt):
    loop_var: str = ""
    start: Expr | None = None
    end: Expr | None = None
    step: Expr | None = None
    end_label: int = 0
    body: list[Stmt] = field(default_factory=list)

@dataclass(slots=True)
class GotoStmt(Stmt):
    target_label: int = 0

@dataclass(slots=True)
class ComputedGotoStmt(Stmt):
    labels: list[int] = field(default_factory=list)
    selector: Expr | None = None

@dataclass(slots=True)
class ContinueStmt(Stmt):
    pass

@dataclass(slots=True)
class CallStmt(Stmt):
    name: str = ""
    args: list[Expr] = field(default_factory=list)

@dataclass(slots=True)
class PrintStmt(Stmt):
    items: list[Expr] = field(default_factory=list)

@dataclass(slots=True)
class ReadStmt(Stmt):
    targets: list[Expr] = field(default_factory=list)

@dataclass(slots=True)
class StopStmt(Stmt):
    pass

@dataclass(slots=True)
class ReturnStmt(Stmt):
    pass