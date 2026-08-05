from __future__ import annotations

from src.ast import (
    ArrayRef,
    BinaryOp,
    CharacterLiteral,
    Expr,
    FunctionCall,
    Identifier,
    IntLiteral,
    LogicalLiteral,
    RealLiteral,
    UnaryOp,
)

from .scope import Scope, SemanticError
from .symbol import ParamInfo, SymbolKind
from .symbol_table import ProcedureSignature, SymbolTable

NUMERIC_TYPES = frozenset({"INTEGER", "REAL"})

ARITHMETIC_OPERATORS = frozenset({"+", "-", "*", "/", "**"})
RELATIONAL_OPERATORS = frozenset({".EQ.", ".NE.", ".LT.", ".LE.", ".GT.", ".GE."})
LOGICAL_BINARY_OPERATORS = frozenset({".AND.", ".OR."})

INTRINSIC_MIN_ARGS = {
    "MAX": 2,
    "MIN": 2,
    "ABS": 1,
    "IABS": 1,
    "SQRT": 1,
    "EXP": 1,
    "LOG": 1,
    "LOG10": 1,
    "SIN": 1,
    "COS": 1,
    "TAN": 1,
    "MOD": 2,
    "INT": 1,
    "REAL": 1,
}

INTRINSIC_VARIADIC = frozenset({"MAX", "MIN"})

INTRINSIC_FIXED_RESULT = {
    "IABS": "INTEGER",
    "SQRT": "REAL",
    "EXP": "REAL",
    "LOG": "REAL",
    "LOG10": "REAL",
    "SIN": "REAL",
    "COS": "REAL",
    "TAN": "REAL",
    "INT": "INTEGER",
    "REAL": "REAL",
}

class TypeChecker:
    def __init__(self, table: SymbolTable) -> None:
        self._table = table

    def check(self, expr: Expr, scope: Scope) -> str:
        if isinstance(expr, IntLiteral):
            return "INTEGER"
        if isinstance(expr, RealLiteral):
            return "REAL"
        if isinstance(expr, LogicalLiteral):
            return "LOGICAL"
        if isinstance(expr, CharacterLiteral):
            return "CHARACTER"
        if isinstance(expr, Identifier):
            return self._check_identifier(expr, scope)
        if isinstance(expr, FunctionCall):
            return self._check_function_call(expr, scope)
        if isinstance(expr, ArrayRef):
            return self._check_array_ref(expr, scope)
        if isinstance(expr, UnaryOp):
            return self._check_unary(expr, scope)
        if isinstance(expr, BinaryOp):
            return self._check_binary(expr, scope)
        raise SemanticError(f"Unknown expression node {type(expr).__name__}", expr.line)

    def _check_identifier(self, expr: Identifier, scope: Scope) -> str:
        symbol = scope.resolve(expr.name)
        if symbol is not None:
            if symbol.kind == SymbolKind.ARRAY:
                raise SemanticError(
                    f"'{expr.name}' is an array and must be indexed", expr.line
                )
            return symbol.data_type

        signature = self._table.procedure(expr.name)
        if signature is not None and signature.kind == SymbolKind.FUNCTION and not signature.param_types:
            return signature.return_type

        raise SemanticError(f"'{expr.name}' is not declared", expr.line)

    def _check_array_ref(self, expr: ArrayRef, scope: Scope) -> str:
        symbol = scope.resolve(expr.name)
        if symbol is not None:
            if symbol.kind != SymbolKind.ARRAY:
                raise SemanticError(f"'{expr.name}' is not an array", expr.line)
            if len(expr.indices) != symbol.rank:
                raise SemanticError(
                    f"'{expr.name}' expects {symbol.rank} index(es), "
                    f"got {len(expr.indices)}",
                    expr.line,
                )
            for index in expr.indices:
                index_type = self.check(index, scope)
                if index_type not in NUMERIC_TYPES:
                    raise SemanticError(
                        f"Array index for '{expr.name}' must be numeric, "
                        f"got {index_type}",
                        index.line,
                    )
            return symbol.data_type

        signature = self._table.procedure(expr.name)
        if signature is not None and signature.kind == SymbolKind.FUNCTION:
            return self._check_call_signature(
                expr.name, expr.indices, signature, scope, expr.line
            )

        if expr.name in INTRINSIC_MIN_ARGS:
            return self._check_intrinsic_call(expr, scope)

        raise SemanticError(f"'{expr.name}' is not declared", expr.line)

    def _check_function_call(self, expr: FunctionCall, scope: Scope) -> str:
        signature = self._table.procedure(expr.name)
        if signature is None:
            if expr.name in INTRINSIC_MIN_ARGS:
                return self._check_intrinsic_call(expr, scope)
            raise SemanticError(f"Function '{expr.name}' is not declared", expr.line)
        if signature.kind != SymbolKind.FUNCTION:
            raise SemanticError(f"'{expr.name}' is not a function", expr.line)
        return self._check_call_signature(expr.name, expr.args, signature, scope, expr.line)

    def _check_call_signature(
        self,
        name: str,
        args: list[Expr],
        signature: ProcedureSignature,
        scope: Scope,
        line: int,
    ) -> str:
        if len(args) != len(signature.param_types):
            raise SemanticError(
                f"'{name}' expects {len(signature.param_types)} argument(s), "
                f"got {len(args)}",
                line,
            )
        for arg, param in zip(args, signature.param_types):
            self.check_argument(arg, scope, param, arg.line)
        return signature.return_type

    def _check_intrinsic_call(self, expr: Expr, scope: Scope) -> str:
        name = expr.name
        args = expr.indices if isinstance(expr, ArrayRef) else expr.args
        min_args = INTRINSIC_MIN_ARGS[name]

        if name in INTRINSIC_VARIADIC:
            if len(args) < min_args:
                raise SemanticError(
                    f"Intrinsic '{name}' expects at least {min_args} argument(s), "
                    f"got {len(args)}",
                    expr.line,
                )
        elif len(args) != min_args:
            raise SemanticError(
                f"Intrinsic '{name}' expects {min_args} argument(s), got {len(args)}",
                expr.line,
            )

        arg_types = [self.check(arg, scope) for arg in args]
        for arg, arg_type in zip(args, arg_types):
            if arg_type not in NUMERIC_TYPES:
                raise SemanticError(
                    f"Intrinsic '{name}' requires numeric arguments, got {arg_type}",
                    arg.line,
                )

        if name in INTRINSIC_FIXED_RESULT:
            return INTRINSIC_FIXED_RESULT[name]

        return "REAL" if "REAL" in arg_types else "INTEGER"

    def check_argument(self, arg: Expr, scope: Scope, param: ParamInfo, line: int) -> None:
        if param.rank > 0:
            if not isinstance(arg, Identifier):
                raise SemanticError(
                    "Array argument must be passed by name without subscript", line
                )
            symbol = scope.resolve(arg.name)
            if symbol is None:
                raise SemanticError(f"'{arg.name}' is not declared", arg.line)
            if symbol.kind != SymbolKind.ARRAY or symbol.rank != param.rank:
                raise SemanticError(
                    f"'{arg.name}' does not match the expected array argument", arg.line
                )
            if symbol.data_type != param.data_type:
                raise SemanticError(
                    f"'{arg.name}' has type {symbol.data_type}, expected {param.data_type}",
                    arg.line,
                )
            return

        arg_type = self.check(arg, scope)
        self.check_assignment_compatible(param.data_type, arg_type, line)

    def _check_unary(self, expr: UnaryOp, scope: Scope) -> str:
        operand_type = self.check(expr.operand, scope)
        if expr.operator == ".NOT.":
            if operand_type != "LOGICAL":
                raise SemanticError(
                    f".NOT. requires a LOGICAL operand, got {operand_type}", expr.line
                )
            return "LOGICAL"
        if operand_type not in NUMERIC_TYPES:
            raise SemanticError(
                f"Unary '{expr.operator}' requires a numeric operand, got {operand_type}",
                expr.line,
            )
        return operand_type

    def _check_binary(self, expr: BinaryOp, scope: Scope) -> str:
        left_type = self.check(expr.left, scope)
        right_type = self.check(expr.right, scope)

        if expr.operator in ARITHMETIC_OPERATORS:
            if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                raise SemanticError(
                    f"Operator '{expr.operator}' requires numeric operands, "
                    f"got {left_type} and {right_type}",
                    expr.line,
                )
            return "REAL" if "REAL" in (left_type, right_type) else "INTEGER"

        if expr.operator in RELATIONAL_OPERATORS:
            if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                if not (left_type == "CHARACTER" and right_type == "CHARACTER" and expr.operator in (".EQ.", ".NE.")):
                    raise SemanticError(
                        f"Operator '{expr.operator}' requires numeric operands, "
                        f"got {left_type} and {right_type}",
                        expr.line,
                    )
            return "LOGICAL"

        if expr.operator in LOGICAL_BINARY_OPERATORS:
            if left_type != "LOGICAL" or right_type != "LOGICAL":
                raise SemanticError(
                    f"Operator '{expr.operator}' requires LOGICAL operands, "
                    f"got {left_type} and {right_type}",
                    expr.line,
                )
            return "LOGICAL"

        raise SemanticError(f"Unknown operator '{expr.operator}'", expr.line)

    def check_assignment_compatible(self, target_type: str, value_type: str, line: int) -> None:
        if target_type == value_type:
            return
        if target_type in NUMERIC_TYPES and value_type in NUMERIC_TYPES:
            return
        raise SemanticError(f"Cannot assign {value_type} to {target_type}", line)

    def check_condition(self, expr: Expr, scope: Scope) -> None:
        condition_type = self.check(expr, scope)
        if condition_type != "LOGICAL":
            raise SemanticError(f"Condition must be LOGICAL, got {condition_type}", expr.line)