from __future__ import annotations

from src.ast import ArrayDecl, Expr, Identifier, IntLiteral

from .scope import Scope, SemanticError
from .symbol import SymbolKind


class ArrayChecker:
    def validate_dimensions(
        self, decl: ArrayDecl, scope: Scope, param_names: set[str]
    ) -> None:
        for dimension in decl.dimensions:
            self._validate_dimension(decl.name, dimension, scope, param_names)

    def _validate_dimension(
        self, array_name: str, dimension: Expr, scope: Scope, param_names: set[str]
    ) -> None:
        if isinstance(dimension, IntLiteral):
            if dimension.value <= 0:
                raise SemanticError(
                    f"Array '{array_name}' dimension must be a positive integer",
                    dimension.line,
                )
            return

        if isinstance(dimension, Identifier):
            upper_params = {name.upper() for name in param_names}
            if dimension.name.upper() not in upper_params:
                raise SemanticError(
                    f"Array '{array_name}' dimension '{dimension.name}' must be a "
                    "constant or a dummy parameter of the enclosing subprogram",
                    dimension.line,
                )
            symbol = scope.resolve(dimension.name)
            if (
                symbol is None
                or symbol.kind != SymbolKind.VARIABLE
                or symbol.data_type != "INTEGER"
            ):
                raise SemanticError(
                    f"Array bound '{dimension.name}' must be a scalar INTEGER parameter",
                    dimension.line,
                )
            return

        raise SemanticError(
            f"Array '{array_name}' dimension must be a constant or a dummy parameter",
            dimension.line,
        )