from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ast import (
    ArrayDecl,
    ArrayRef,
    Assignment,
    BinaryOp,
    CallStmt,
    CommonDecl,
    ContinueStmt,
    DoStmt,
    Function,
    FunctionCall,
    GotoStmt,
    Identifier,
    IfStmt,
    ImplicitNoneDecl,
    IntLiteral,
    LogicalLiteral,
    PrintStmt,
    Program,
    ReadStmt,
    RealLiteral,
    ReturnStmt,
    StopStmt,
    Subprogram,
    Subroutine,
    TranslationUnit,
    TypeDecl,
    UnaryOp,
)


@dataclass(slots=True)
class _Group:
    label: str
    items: list[Any] = field(default_factory=list)


def expr_to_str(expr: Any) -> str:
    if expr is None:
        return ""
    if isinstance(expr, IntLiteral):
        return str(expr.value)
    if isinstance(expr, RealLiteral):
        return str(expr.value)
    if isinstance(expr, LogicalLiteral):
        return ".TRUE." if expr.value else ".FALSE."
    if isinstance(expr, Identifier):
        return expr.name
    if isinstance(expr, ArrayRef):
        indices = ", ".join(expr_to_str(i) for i in expr.indices)
        return f"{expr.name}({indices})"
    if isinstance(expr, FunctionCall):
        args = ", ".join(expr_to_str(a) for a in expr.args)
        return f"{expr.name}({args})"
    if isinstance(expr, UnaryOp):
        return f"{expr.operator}{expr_to_str(expr.operand)}"
    if isinstance(expr, BinaryOp):
        return f"({expr_to_str(expr.left)} {expr.operator} {expr_to_str(expr.right)})"
    return repr(expr)


def node_label(node: Any) -> str:
    if isinstance(node, _Group):
        return node.label

    if isinstance(node, TranslationUnit):
        return "TranslationUnit"
    if isinstance(node, Program):
        return f"Program {node.name}"
    if isinstance(node, Subroutine):
        return f"Subroutine {node.name}({', '.join(node.params)})"
    if isinstance(node, Function):
        return_type = node.return_type or "?"
        return f"Function {return_type} {node.name}({', '.join(node.params)})"

    if isinstance(node, ImplicitNoneDecl):
        return "ImplicitNoneDecl"
    if isinstance(node, TypeDecl):
        return f"TypeDecl {node.base_type} {', '.join(node.names)}"
    if isinstance(node, ArrayDecl):
        dims = ", ".join(expr_to_str(d) for d in node.dimensions)
        return f"ArrayDecl {node.base_type} {node.name}({dims})"
    if isinstance(node, CommonDecl):
        return f"CommonDecl /{node.block_name}/ {', '.join(node.variables)}"

    if isinstance(node, Assignment):
        return f"Assignment {expr_to_str(node.target)} = {expr_to_str(node.value)}"
    if isinstance(node, IfStmt):
        return f"IfStmt {expr_to_str(node.condition)}"
    if isinstance(node, DoStmt):
        step = f", {expr_to_str(node.step)}" if node.step is not None else ""
        return (
            f"DoStmt {node.loop_var} = {expr_to_str(node.start)}, "
            f"{expr_to_str(node.end)}{step} (label {node.end_label})"
        )
    if isinstance(node, GotoStmt):
        return f"GotoStmt -> {node.target_label}"
    if isinstance(node, ContinueStmt):
        return "ContinueStmt"
    if isinstance(node, CallStmt):
        args = ", ".join(expr_to_str(a) for a in node.args)
        return f"CallStmt {node.name}({args})"
    if isinstance(node, PrintStmt):
        return f"PrintStmt {', '.join(expr_to_str(i) for i in node.items)}"
    if isinstance(node, ReadStmt):
        return f"ReadStmt {', '.join(expr_to_str(t) for t in node.targets)}"
    if isinstance(node, StopStmt):
        return "StopStmt"
    if isinstance(node, ReturnStmt):
        return "ReturnStmt"

    return type(node).__name__


def node_children(node: Any) -> list[Any]:
    if isinstance(node, _Group):
        return node.items

    if isinstance(node, TranslationUnit):
        children: list[Any] = []
        if node.program is not None:
            children.append(node.program)
        children.extend(node.subprograms)
        return children

    if isinstance(node, Subprogram):
        return [*node.declarations, *node.body]

    if isinstance(node, DoStmt):
        return list(node.body)

    if isinstance(node, IfStmt):
        children = list(node.then_body)
        if node.else_body:
            children.append(_Group(label="Else", items=list(node.else_body)))
        return children

    return []