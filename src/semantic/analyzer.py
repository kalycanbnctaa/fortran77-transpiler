from __future__ import annotations

from src.ast import (
    ArrayDecl,
    ArrayRef,
    Assignment,
    CallStmt,
    CommonDecl,
    ComputedGotoStmt,
    ContinueStmt,
    DoStmt,
    Expr,
    Function,
    GotoStmt,
    Identifier,
    IfStmt,
    ImplicitNoneDecl,
    PrintStmt,
    Program,
    ReadStmt,
    ReturnStmt,
    Stmt,
    StopStmt,
    Subprogram,
    Subroutine,
    TranslationUnit,
    TypeDecl,
)

from .array_checker import ArrayChecker
from .common_checker import CommonChecker
from .scope import Scope, SemanticError
from .symbol import ParamInfo, Symbol, SymbolKind
from .symbol_table import ProcedureSignature, SymbolTable
from .type_checker import NUMERIC_TYPES, TypeChecker

VALID_TYPES = frozenset({"INTEGER", "REAL", "LOGICAL", "CHARACTER"})


class SemanticAnalyzer:
    def __init__(self, translation_unit: TranslationUnit) -> None:
        self._tu = translation_unit
        self._table = SymbolTable()
        self._type_checker = TypeChecker(self._table)
        self._array_checker = ArrayChecker()
        self._common_checker = CommonChecker(self._table)

    def analyze(self) -> SymbolTable:
        subprograms = self._collect_subprograms()

        for subprogram in subprograms:
            self._declare_subprogram(subprogram)

        for subprogram in subprograms:
            self._check_subprogram(subprogram)

        self._common_checker.check()

        return self._table

    def _collect_subprograms(self) -> list[Subprogram]:
        subprograms: list[Subprogram] = []
        if self._tu.program is not None:
            subprograms.append(self._tu.program)
        subprograms.extend(self._tu.subprograms)
        return subprograms

    def _procedure_kind(self, subprogram: Subprogram) -> SymbolKind:
        if isinstance(subprogram, Program):
            return SymbolKind.PROGRAM
        if isinstance(subprogram, Subroutine):
            return SymbolKind.SUBROUTINE
        return SymbolKind.FUNCTION

    def _declare_subprogram(self, subprogram: Subprogram) -> None:
        scope = self._table.create_scope(subprogram.name)
        param_names = set(subprogram.params)

        implicit_none = any(
            isinstance(decl, ImplicitNoneDecl) for decl in subprogram.declarations
        )
        if not implicit_none:
            raise SemanticError(
                f"'{subprogram.name}' is missing IMPLICIT NONE", subprogram.line
            )

        for decl in subprogram.declarations:
            if isinstance(decl, TypeDecl):
                self._declare_type_decl(decl, scope, param_names)

        for decl in subprogram.declarations:
            if isinstance(decl, ArrayDecl):
                self._declare_array_decl(decl, scope, param_names)

        if isinstance(subprogram, Function):
            self._declare_function_result_symbol(subprogram, scope)

        for decl in subprogram.declarations:
            if isinstance(decl, CommonDecl):
                self._declare_common_decl(decl, scope, subprogram.name)

        for param in subprogram.params:
            if scope.resolve(param) is None:
                raise SemanticError(
                    f"Parameter '{param}' of '{subprogram.name}' has no type declaration",
                    subprogram.line,
                )

        self._register_procedure_signature(subprogram, scope)

    def _declare_function_result_symbol(self, subprogram: Function, scope: Scope) -> None:
        existing = scope.resolve(subprogram.name)
        if existing is not None:
            return

        if not subprogram.return_type:
            raise SemanticError(
                f"Function '{subprogram.name}' has no return type declaration",
                subprogram.line,
            )

        if subprogram.return_type not in VALID_TYPES:
            raise SemanticError(
                f"Unknown return type '{subprogram.return_type}' for function "
                f"'{subprogram.name}'",
                subprogram.line,
            )

        scope.declare(
            Symbol(
                name=subprogram.name,
                kind=SymbolKind.VARIABLE,
                data_type=subprogram.return_type,
                line=subprogram.line,
            )
        )

    def _declare_type_decl(self, decl: TypeDecl, scope: Scope, param_names: set[str]) -> None:
        if decl.base_type not in VALID_TYPES:
            raise SemanticError(f"Unknown type '{decl.base_type}'", decl.line)

        for name in decl.names:
            symbol = Symbol(
                name=name,
                kind=SymbolKind.VARIABLE,
                data_type=decl.base_type,
                is_parameter=name in param_names,
                line=decl.line,
                length=decl.length,
            )
            scope.declare(symbol)

    def _declare_array_decl(self, decl: ArrayDecl, scope: Scope, param_names: set[str]) -> None:
        if decl.base_type not in VALID_TYPES:
            raise SemanticError(f"Unknown type '{decl.base_type}'", decl.line)

        self._array_checker.validate_dimensions(decl, scope, param_names)

        symbol = Symbol(
            name=decl.name,
            kind=SymbolKind.ARRAY,
            data_type=decl.base_type,
            dimensions=list(decl.dimensions),
            is_parameter=decl.name in param_names,
            line=decl.line,
        )
        scope.declare(symbol)

    def _declare_common_decl(self, decl: CommonDecl, scope: Scope, subprogram_name: str) -> None:
        members: list[Symbol] = []
        for index, name in enumerate(decl.variables):
            symbol = scope.resolve(name)
            if symbol is None:
                raise SemanticError(
                    f"COMMON variable '{name}' has no type declaration", decl.line
                )
            symbol.common_block = decl.block_name
            symbol.common_index = index
            members.append(symbol)

        self._table.add_common_members(decl.block_name, subprogram_name, members)

    def _register_procedure_signature(self, subprogram: Subprogram, scope: Scope) -> None:
        kind = self._procedure_kind(subprogram)

        param_types: list[ParamInfo] = []
        for param in subprogram.params:
            symbol = scope.resolve(param)
            if symbol is None:
                param_types.append(ParamInfo(data_type="", rank=0))
            else:
                param_types.append(ParamInfo(data_type=symbol.data_type, rank=symbol.rank))

        return_type = ""
        if isinstance(subprogram, Function):
            own_symbol = scope.resolve(subprogram.name)
            if own_symbol is None:
                raise SemanticError(
                    f"Function '{subprogram.name}' has no return type declaration",
                    subprogram.line,
                )
            return_type = own_symbol.data_type

        signature = ProcedureSignature(
            name=subprogram.name,
            kind=kind,
            param_types=param_types,
            return_type=return_type,
            line=subprogram.line,
        )
        self._table.register_procedure(signature)

    def _check_subprogram(self, subprogram: Subprogram) -> None:
        scope = self._table.scope_for(subprogram.name)
        labels = self._collect_labels(subprogram.body)
        self._check_statements(subprogram.body, scope, labels)

    def _collect_labels(self, statements: list[Stmt]) -> set[int]:
        labels: set[int] = set()
        for stmt in statements:
            if stmt.label is not None:
                labels.add(stmt.label)
            if isinstance(stmt, DoStmt):
                labels.add(stmt.end_label)
                labels |= self._collect_labels(stmt.body)
            elif isinstance(stmt, IfStmt):
                labels |= self._collect_labels(stmt.then_body)
                labels |= self._collect_labels(stmt.else_body)
        return labels

    def _check_statements(self, statements: list[Stmt], scope: Scope, labels: set[int]) -> None:
        for stmt in statements:
            self._check_statement(stmt, scope, labels)

    def _check_statement(self, stmt: Stmt, scope: Scope, labels: set[int]) -> None:
        if isinstance(stmt, Assignment):
            self._check_assignment(stmt, scope)
        elif isinstance(stmt, IfStmt):
            self._type_checker.check_condition(stmt.condition, scope)
            self._check_statements(stmt.then_body, scope, labels)
            self._check_statements(stmt.else_body, scope, labels)
        elif isinstance(stmt, DoStmt):
            self._check_do(stmt, scope, labels)
        elif isinstance(stmt, GotoStmt):
            if stmt.target_label not in labels:
                raise SemanticError(
                    f"GOTO target label {stmt.target_label} does not exist", stmt.line
                )
        elif isinstance(stmt, ComputedGotoStmt):
            self._check_computed_goto(stmt, scope, labels)
        elif isinstance(stmt, CallStmt):
            self._check_call(stmt, scope)
        elif isinstance(stmt, PrintStmt):
            for item in stmt.items:
                self._type_checker.check(item, scope)
        elif isinstance(stmt, ReadStmt):
            for target in stmt.targets:
                self._check_lvalue(target, scope)
        elif isinstance(stmt, (ContinueStmt, StopStmt, ReturnStmt)):
            return
        else:
            raise SemanticError(f"Unknown statement node {type(stmt).__name__}", stmt.line)

    def _check_computed_goto(self, stmt: ComputedGotoStmt, scope: Scope, labels: set[int]) -> None:
        selector_type = self._type_checker.check(stmt.selector, scope)
        if selector_type not in NUMERIC_TYPES:
            raise SemanticError(
                f"Computed GOTO selector must be numeric, got {selector_type}",
                stmt.selector.line
            )
        for label in stmt.labels:
            if label not in labels:
                raise SemanticError(
                    f"Computed GOTO target label {label} does not exist", stmt.line
                )

    def _check_assignment(self, stmt: Assignment, scope: Scope) -> None:
        self._check_lvalue(stmt.target, scope)
        target_type = self._type_checker.check(stmt.target, scope)
        value_type = self._type_checker.check(stmt.value, scope)
        self._type_checker.check_assignment_compatible(target_type, value_type, stmt.line)

    def _check_lvalue(self, target: Expr, scope: Scope) -> None:
        if isinstance(target, Identifier):
            self._type_checker.check(target, scope)
            return
        if isinstance(target, ArrayRef):
            symbol = scope.resolve(target.name)
            if symbol is None:
                raise SemanticError(f"Cannot assign to '{target.name}'", target.line)
            self._type_checker.check(target, scope)
            return
        raise SemanticError("Invalid assignment target", target.line)

    def _check_do(self, stmt: DoStmt, scope: Scope, labels: set[int]) -> None:
        loop_symbol = scope.resolve(stmt.loop_var)
        if loop_symbol is None:
            raise SemanticError(f"'{stmt.loop_var}' is not declared", stmt.line)
        if loop_symbol.data_type not in NUMERIC_TYPES:
            raise SemanticError(
                f"DO loop variable '{stmt.loop_var}' must be numeric", stmt.line
            )

        for bound in (stmt.start, stmt.end, stmt.step):
            if bound is not None:
                bound_type = self._type_checker.check(bound, scope)
                if bound_type not in NUMERIC_TYPES:
                    raise SemanticError("DO loop bounds must be numeric", bound.line)

        self._check_statements(stmt.body, scope, labels)

    def _check_call(self, stmt: CallStmt, scope: Scope) -> None:
        signature = self._table.procedure(stmt.name)
        if signature is None:
            raise SemanticError(f"Subroutine '{stmt.name}' is not declared", stmt.line)
        if signature.kind != SymbolKind.SUBROUTINE:
            raise SemanticError(f"'{stmt.name}' is not a subroutine", stmt.line)
        if len(stmt.args) != len(signature.param_types):
            raise SemanticError(
                f"Subroutine '{stmt.name}' expects {len(signature.param_types)} "
                f"argument(s), got {len(stmt.args)}",
                stmt.line,
            )
        for arg, param in zip(stmt.args, signature.param_types):
            self._type_checker.check_argument(arg, scope, param, arg.line)