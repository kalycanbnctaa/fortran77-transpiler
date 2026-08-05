from __future__ import annotations

from dataclasses import dataclass

from src.ast import (
    ArrayDecl,
    ArrayRef,
    Assignment,
    BinaryOp,
    CallStmt,
    CharacterLiteral,
    CommonDecl,
    ComputedGotoStmt,
    ContinueStmt,
    Decl,
    DoStmt,
    Expr,
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
    Stmt,
    StopStmt,
    Subprogram,
    Subroutine,
    TranslationUnit,
    TypeDecl,
    UnaryOp,
)
from src.semantic import Scope, Symbol, SymbolKind, SymbolTable, TypeChecker
from src.semantic.symbol_table import ProcedureSignature
from src.semantic.type_checker import INTRINSIC_MIN_ARGS

from .arrays import ArrayCodegen, ArrayCodegenError
from .common import CommonBlockRegistry, CommonCodegenError
from .emitter import Emitter
from .formatter import (
    c_identifier,
    c_type,
    character_buffer_size,
    format_character_literal,
    format_int_literal,
    format_logical_literal,
    format_real_literal,
    format_specifier,
    scan_specifier,
)
from .intrinsics import IntrinsicCodegenError, emit_intrinsic

class CodeGenerationError(Exception):
    pass

@dataclass(slots=True)
class _SubprogramContext:
    scope: Scope
    subprogram: Subprogram
    is_function: bool
    function_result_c_name: str | None

class CodeGenerator:
    UNARY_OPERATORS = {"+": "+", "-": "-", ".NOT.": "!"}

    BINARY_OPERATORS = {
        "+": "+",
        "-": "-",
        "*": "*",
        "/": "/",
        ".EQ.": "==",
        ".NE.": "!=",
        ".LT.": "<",
        ".LE.": "<=",
        ".GT.": ">",
        ".GE.": ">=",
        ".AND.": "&&",
        ".OR.": "||",
    }

    def __init__(self, translation_unit: TranslationUnit, table: SymbolTable, source_map: bool = False) -> None:
        self._tu = translation_unit
        self._table = table
        self._type_checker = TypeChecker(table)
        self._emitter = Emitter()
        self._arrays = ArrayCodegen()
        self._source_map = source_map

        try:
            self._commons = CommonBlockRegistry(table)
        except CommonCodegenError as error:
            raise CodeGenerationError(str(error)) from error

        self._context: _SubprogramContext | None = None
        self._temp_counter = 0
        self._temp_decls: list[str] = []

    def _allocate_temp(self, expr: Expr) -> str:
        temp_name = f"_tmp{self._temp_counter}"
        self._temp_counter += 1
        expr_text = self._emit_expr(expr)
        expr_type = self._type_checker.check(expr, self._context.scope)
        if expr_type == "CHARACTER":
            self._temp_decls.append(f"char {temp_name}[80];")
            self._temp_decls.append(f'strcpy({temp_name}, {expr_text});')
        else:
            c_base = c_type(expr_type)
            self._temp_decls.append(f"{c_base} {temp_name} = {expr_text};")
        return temp_name

    def _line(self, text: str = "", source_line: int = 0) -> None:
        if self._source_map and source_line:
            text += f"  // line {source_line}"
        self._emitter.line(text)

    def _blank(self) -> None:
        self._emitter.blank()

    def generate(self) -> str:
        if self._tu.program is None:
            raise CodeGenerationError("Translation unit has no PROGRAM to generate")

        subprograms = list(self._tu.subprograms)

        self._emit_headers()
        self._blank()

        for block_name in self._commons.block_names():
            for line in self._commons.render_struct(block_name):
                self._line(line)
            self._blank()

        for subprogram in subprograms:
            self._line(self._signature_text(subprogram) + ";")
        if subprograms:
            self._blank()

        self._emit_program(self._tu.program)

        for subprogram in subprograms:
            self._blank()
            self._emit_subprogram(subprogram)

        return self._emitter.render()

    def _emit_headers(self) -> None:
        self._line("#include <stdio.h>")
        self._line("#include <math.h>")
        self._line("#include <stdlib.h>")
        self._line("#include <string.h>")

    def _signature_text(self, subprogram: Subprogram) -> str:
        scope = self._table.scope_for(subprogram.name)
        params_text: list[str] = []
        for pname in subprogram.params:
            symbol = scope.resolve(pname)
            if symbol is None:
                raise CodeGenerationError(f"Parameter '{pname}' has no symbol")
            params_text.append(f"{c_type(symbol.data_type)} *{c_identifier(pname)}")
        params_joined = ", ".join(params_text) if params_text else "void"

        if isinstance(subprogram, Function):
            own_symbol = scope.resolve(subprogram.name)
            if own_symbol is None:
                raise CodeGenerationError(
                    f"Function '{subprogram.name}' has no return type symbol"
                )
            return_type = c_type(own_symbol.data_type)
            return f"{return_type} {c_identifier(subprogram.name)}({params_joined})"

        return f"void {c_identifier(subprogram.name)}({params_joined})"

    def _emit_program(self, program: Program) -> None:
        scope = self._table.scope_for(program.name)
        self._context = _SubprogramContext(
            scope=scope, subprogram=program, is_function=False, function_result_c_name=None
        )

        self._line("int main(void) {", program.line)
        self._emitter.indent()

        emitted_decls = self._emit_local_declarations(program)
        if self._temp_decls:
            for decl in self._temp_decls:
                self._line(decl)
            self._temp_decls.clear()
        if emitted_decls or self._temp_decls:
            self._blank()

        self._emit_statements(program.body)
        self._line("return 0;")

        self._emitter.dedent()
        self._line("}")

        self._context = None

    def _emit_subprogram(self, subprogram: Subprogram) -> None:
        scope = self._table.scope_for(subprogram.name)
        is_function = isinstance(subprogram, Function)
        result_c_name = f"{c_identifier(subprogram.name)}_val" if is_function else None
        self._context = _SubprogramContext(
            scope=scope,
            subprogram=subprogram,
            is_function=is_function,
            function_result_c_name=result_c_name,
        )

        self._line(self._signature_text(subprogram) + " {", subprogram.line)
        self._emitter.indent()

        if is_function:
            own_symbol = scope.resolve(subprogram.name)
            if own_symbol is None:
                raise CodeGenerationError(
                    f"Function '{subprogram.name}' has no return type symbol"
                )
            self._line(f"{c_type(own_symbol.data_type)} {result_c_name};")

        emitted_decls = self._emit_local_declarations(subprogram)
        if self._temp_decls:
            for decl in self._temp_decls:
                self._line(decl)
            self._temp_decls.clear()
        if emitted_decls or is_function or self._temp_decls:
            self._blank()

        self._emit_statements(subprogram.body)

        if is_function:
            self._line(f"return {result_c_name};")

        self._emitter.dedent()
        self._line("}")

        self._context = None

    def _emit_local_declarations(self, subprogram: Subprogram) -> bool:
        emitted = False
        for decl in subprogram.declarations:
            if isinstance(decl, ImplicitNoneDecl):
                continue
            if isinstance(decl, TypeDecl):
                if self._emit_type_decl_filtered(decl):
                    emitted = True
            elif isinstance(decl, ArrayDecl):
                if self._emit_array_decl_filtered(decl):
                    emitted = True
            elif isinstance(decl, CommonDecl):
                continue
            else:
                raise CodeGenerationError(f"Unknown declaration node {type(decl).__name__}")
        return emitted

    def _is_plain_local(self, name: str) -> bool:
        symbol = self._context.scope.resolve(name)
        if symbol is None:
            return False
        if symbol.is_parameter:
            return False
        if symbol.common_block is not None:
            return False
        if (
            self._context.is_function
            and name.upper() == self._context.subprogram.name.upper()
        ):
            return False
        return True

    def _emit_type_decl_filtered(self, decl: TypeDecl) -> bool:
        names_to_emit = [name for name in decl.names if self._is_plain_local(name)]
        if not names_to_emit:
            return False
        if decl.base_type == "CHARACTER":
            size = character_buffer_size(decl.length)
            names_text = ", ".join(f"{c_identifier(name)}[{size}]" for name in names_to_emit)
            self._line(f"char {names_text};", decl.line)
            return True
        c_base = c_type(decl.base_type)
        names_text = ", ".join(c_identifier(name) for name in names_to_emit)
        self._line(f"{c_base} {names_text};", decl.line)
        return True

    def _emit_array_decl_filtered(self, decl: ArrayDecl) -> bool:
        if not self._is_plain_local(decl.name):
            return False
        symbol = self._context.scope.resolve(decl.name)
        try:
            size = self._arrays.flat_size(symbol)
        except ArrayCodegenError as error:
            raise CodeGenerationError(str(error)) from error
        c_base = c_type(symbol.data_type)
        self._line(f"{c_base} {c_identifier(decl.name)}[{size}];", decl.line)
        return True

    def _array_base_text(self, symbol: Symbol) -> str:
        if symbol.common_block is not None:
            return self._commons.member_access(symbol.common_block, symbol.common_index)
        return c_identifier(symbol.name)

    def _array_access_text(self, symbol: Symbol, index_texts: list[str]) -> str:
        try:
            dimension_texts = self._arrays.dimension_texts(symbol)
            offset = self._arrays.offset_text(index_texts, dimension_texts)
        except ArrayCodegenError as error:
            raise CodeGenerationError(str(error)) from error
        base = self._array_base_text(symbol)
        return f"{base}[{offset}]"

    def _scalar_access_text(self, symbol: Symbol) -> str:
        if symbol.common_block is not None:
            return self._commons.member_access(symbol.common_block, symbol.common_index)
        if (
            self._context.is_function
            and symbol.name.upper() == self._context.subprogram.name.upper()
            and not symbol.is_parameter
        ):
            return self._context.function_result_c_name
        if symbol.is_parameter:
            if symbol.data_type == "CHARACTER":
                return c_identifier(symbol.name)
            return f"(*{c_identifier(symbol.name)})"
        return c_identifier(symbol.name)

    def _resolve_symbol(self, expr: Expr) -> Symbol | None:
        if isinstance(expr, Identifier):
            return self._context.scope.resolve(expr.name)
        if isinstance(expr, ArrayRef):
            return self._context.scope.resolve(expr.name)
        return None

    def _emit_statements(self, statements: list[Stmt]) -> None:
        for stmt in statements:
            if stmt.label is not None:
                self._line(f"L{stmt.label}: ;", stmt.line)
            self._emit_statement(stmt)

    def _emit_statement(self, stmt: Stmt) -> None:
        if isinstance(stmt, Assignment):
            self._emit_assignment(stmt)
        elif isinstance(stmt, PrintStmt):
            self._emit_print(stmt)
        elif isinstance(stmt, ReadStmt):
            self._emit_read(stmt)
        elif isinstance(stmt, StopStmt):
            self._line("exit(0);", stmt.line)
        elif isinstance(stmt, ReturnStmt):
            self._emit_return(stmt)
        elif isinstance(stmt, IfStmt):
            self._emit_if(stmt)
        elif isinstance(stmt, DoStmt):
            self._emit_do(stmt)
        elif isinstance(stmt, GotoStmt):
            self._line(f"goto L{stmt.target_label};", stmt.line)
        elif isinstance(stmt, ComputedGotoStmt):
            self._emit_computed_goto(stmt)
        elif isinstance(stmt, CallStmt):
            self._emit_call_stmt(stmt)
        elif isinstance(stmt, ContinueStmt):
            return
        else:
            raise CodeGenerationError(f"Unknown statement node {type(stmt).__name__}")

    def _emit_return(self, stmt: ReturnStmt) -> None:
        if self._context.is_function:
            self._line(f"return {self._context.function_result_c_name};", stmt.line)
        elif isinstance(self._context.subprogram, Subroutine):
            self._line("return;", stmt.line)
        else:
            self._line("return 0;", stmt.line)

    def _emit_assignment(self, stmt: Assignment) -> None:
        target_text = self._emit_target(stmt.target)
        value_text = self._emit_expr(stmt.value)
        target_type = self._type_checker.check(stmt.target, self._context.scope)
        if target_type == "CHARACTER":
            sym = self._resolve_symbol(stmt.target)
            if sym is None:
                raise CodeGenerationError("Cannot resolve CHARACTER target")
            length = sym.length if sym.length is not None else 1
            self._line(
                f'snprintf({target_text}, {length + 1}, "%-{length}.{length}s", {value_text});',
                stmt.line,
            )
        else:
            self._line(f"{target_text} = {value_text};", stmt.line)

    def _emit_target(self, target: Expr) -> str:
        scope = self._context.scope
        if isinstance(target, Identifier):
            symbol = scope.resolve(target.name)
            if symbol is None:
                raise CodeGenerationError(f"'{target.name}' is not declared")
            return self._scalar_access_text(symbol)
        if isinstance(target, ArrayRef):
            symbol = scope.resolve(target.name)
            if symbol is None or symbol.kind != SymbolKind.ARRAY:
                raise CodeGenerationError(f"'{target.name}' is not an array")
            index_texts = [self._emit_expr(index) for index in target.indices]
            return self._array_access_text(symbol, index_texts)
        raise CodeGenerationError("Invalid assignment target")

    def _emit_print(self, stmt: PrintStmt) -> None:
        if not stmt.items:
            self._line('printf("\\n");', stmt.line)
            return

        specifiers: list[str] = []
        args: list[str] = []
        for item in stmt.items:
            item_type = self._type_checker.check(item, self._context.scope)
            item_text = self._emit_expr(item)
            if item_type == "LOGICAL":
                specifiers.append("%s")
                args.append(f'({item_text} ? "T" : "F")')
            else:
                specifiers.append(format_specifier(item_type))
                args.append(item_text)

        format_string = " ".join(specifiers) + "\\n"
        arg_text = ", ".join(args)
        self._line(f'printf("{format_string}", {arg_text});', stmt.line)

    def _emit_read(self, stmt: ReadStmt) -> None:
        if not stmt.targets:
            return

        specifiers: list[str] = []
        args: list[str] = []
        for target in stmt.targets:
            target_type = self._type_checker.check(target, self._context.scope)
            specifiers.append(scan_specifier(target_type))
            target_text = self._emit_target(target)
            if target_type == "CHARACTER":
                args.append(target_text)
            else:
                args.append(f"&({target_text})")

        format_string = " ".join(specifiers)
        arg_text = ", ".join(args)
        self._line(f'scanf("{format_string}", {arg_text});', stmt.line)

    def _emit_if(self, stmt: IfStmt) -> None:
        condition_text = self._emit_expr(stmt.condition)
        self._line(f"if ({condition_text}) {{", stmt.line)
        self._emitter.indent()
        self._emit_statements(stmt.then_body)
        self._emitter.dedent()
        if stmt.else_body:
            self._line("} else {", stmt.else_body[0].line if stmt.else_body else 0)
            self._emitter.indent()
            self._emit_statements(stmt.else_body)
            self._emitter.dedent()
            self._line("}")
        else:
            self._line("}")

    def _static_step_sign(self, step: Expr) -> int | None:
        if isinstance(step, IntLiteral):
            return 1 if step.value >= 0 else -1
        if isinstance(step, UnaryOp) and step.operator in ("+", "-"):
            inner = self._static_step_sign(step.operand)
            if inner is None:
                return None
            return inner if step.operator == "+" else -inner
        return None

    def _emit_do(self, stmt: DoStmt) -> None:
        symbol = self._context.scope.resolve(stmt.loop_var)
        if symbol is None:
            raise CodeGenerationError(f"'{stmt.loop_var}' is not declared")
        loop_var = self._scalar_access_text(symbol)

        start_text = self._emit_expr(stmt.start)
        end_text = self._emit_expr(stmt.end)

        if stmt.step is None:
            condition = f"{loop_var} <= {end_text}"
            increment = f"{loop_var}++"
        else:
            step_text = self._emit_expr(stmt.step)
            increment = f"{loop_var} += {step_text}"

            sign = self._static_step_sign(stmt.step)
            if sign is not None:
                if sign >= 0:
                    condition = f"{loop_var} <= {end_text}"
                else:
                    condition = f"{loop_var} >= {end_text}"
            else:
                condition = (
                    f"(({step_text}) >= 0 ? "
                    f"({loop_var} <= {end_text}) : "
                    f"({loop_var} >= {end_text}))"
                )

        self._line(f"for ({loop_var} = {start_text}; {condition}; {increment}) {{", stmt.line)
        self._emitter.indent()
        self._emit_statements(stmt.body)
        self._emitter.dedent()
        self._line("}")

    def _emit_computed_goto(self, stmt: ComputedGotoStmt) -> None:
        selector_text = self._emit_expr(stmt.selector)
        self._line(f"switch ({selector_text}) {{", stmt.line)
        self._emitter.indent()
        for i, label in enumerate(stmt.labels, start=1):
            self._line(f"case {i}: goto L{label};", stmt.line)
        self._line("default: break;", stmt.line)
        self._emitter.dedent()
        self._line("}")

    def _emit_call_stmt(self, stmt: CallStmt) -> None:
        signature = self._table.procedure(stmt.name)
        if signature is None:
            raise CodeGenerationError(f"Subroutine '{stmt.name}' is not declared")
        if signature.kind != SymbolKind.SUBROUTINE:
            raise CodeGenerationError(f"'{stmt.name}' is not a subroutine")
        arg_texts = [
            self._emit_reference(arg, param)
            for arg, param in zip(stmt.args, signature.param_types)
        ]
        self._line(f"{c_identifier(stmt.name)}({', '.join(arg_texts)});", stmt.line)

    def _emit_reference(self, expr: Expr, param) -> str:
        scope = self._context.scope

        if isinstance(expr, Identifier):
            symbol = scope.resolve(expr.name)
            if symbol is None:
                raise CodeGenerationError(f"'{expr.name}' is not declared")
            if symbol.kind == SymbolKind.ARRAY:
                return self._array_base_text(symbol)
            if symbol.common_block is not None:
                access = self._commons.member_access(symbol.common_block, symbol.common_index)
                if symbol.data_type == "CHARACTER":
                    return access
                return f"&({access})"
            if symbol.is_parameter:
                return c_identifier(symbol.name)
            if (
                self._context.is_function
                and symbol.name.upper() == self._context.subprogram.name.upper()
            ):
                return f"&{self._context.function_result_c_name}"
            if symbol.data_type == "CHARACTER":
                return c_identifier(symbol.name)
            return f"&{c_identifier(symbol.name)}"

        if isinstance(expr, ArrayRef):
            symbol = scope.resolve(expr.name)
            if symbol is None or symbol.kind != SymbolKind.ARRAY:
                raise CodeGenerationError(
                    f"'{expr.name}' must be an array element to pass by reference"
                )
            index_texts = [self._emit_expr(index) for index in expr.indices]
            access = self._array_access_text(symbol, index_texts)
            return f"&({access})"

        if isinstance(expr, (IntLiteral, RealLiteral, LogicalLiteral, CharacterLiteral)):
            expr_type = self._type_checker.check(expr, self._context.scope)
            temp = self._allocate_temp(expr)
            if expr_type == "CHARACTER":
                return temp
            return f"&{temp}"

        raise CodeGenerationError(
            "Passing a non-variable expression as an argument is not supported"
        )

    def _emit_expr(self, expr: Expr) -> str:
        if isinstance(expr, IntLiteral):
            return format_int_literal(expr.value)
        if isinstance(expr, RealLiteral):
            return format_real_literal(expr.value)
        if isinstance(expr, LogicalLiteral):
            return format_logical_literal(expr.value)
        if isinstance(expr, CharacterLiteral):
            return format_character_literal(expr.value)
        if isinstance(expr, Identifier):
            return self._emit_identifier(expr)
        if isinstance(expr, ArrayRef):
            return self._emit_array_ref(expr)
        if isinstance(expr, UnaryOp):
            return self._emit_unary(expr)
        if isinstance(expr, BinaryOp):
            return self._emit_binary(expr)
        if isinstance(expr, FunctionCall):
            raise CodeGenerationError("Unsupported expression node FunctionCall")
        raise CodeGenerationError(f"Unknown expression node {type(expr).__name__}")

    def _emit_identifier(self, expr: Identifier) -> str:
        symbol = self._context.scope.resolve(expr.name)
        if symbol is not None:
            if symbol.kind == SymbolKind.ARRAY:
                raise CodeGenerationError(f"'{expr.name}' is an array and must be indexed")
            return self._scalar_access_text(symbol)

        signature = self._table.procedure(expr.name)
        if signature is not None and signature.kind == SymbolKind.FUNCTION and not signature.param_types:
            return f"{c_identifier(expr.name)}()"

        raise CodeGenerationError(f"'{expr.name}' is not declared")

    def _emit_array_ref(self, expr: ArrayRef) -> str:
        scope = self._context.scope
        symbol = scope.resolve(expr.name)
        if symbol is not None and symbol.kind == SymbolKind.ARRAY:
            index_texts = [self._emit_expr(index) for index in expr.indices]
            return self._array_access_text(symbol, index_texts)

        signature = self._table.procedure(expr.name)
        if signature is not None and signature.kind == SymbolKind.FUNCTION:
            return self._emit_call_expr(expr.name, expr.indices, signature)

        if expr.name in INTRINSIC_MIN_ARGS:
            return self._emit_intrinsic_expr(expr.name, expr.indices)

        raise CodeGenerationError(f"'{expr.name}' is not declared")

    def _emit_call_expr(
        self, name: str, args: list[Expr], signature: ProcedureSignature
    ) -> str:
        arg_texts = [
            self._emit_reference(arg, param)
            for arg, param in zip(args, signature.param_types)
        ]
        return f"{c_identifier(name)}({', '.join(arg_texts)})"

    def _emit_intrinsic_expr(self, name: str, args: list[Expr]) -> str:
        arg_types = [self._type_checker.check(arg, self._context.scope) for arg in args]
        arg_texts = [self._emit_expr(arg) for arg in args]
        try:
            return emit_intrinsic(name, arg_texts, arg_types)
        except IntrinsicCodegenError as error:
            raise CodeGenerationError(str(error)) from error

    def _emit_unary(self, expr: UnaryOp) -> str:
        operand = self._emit_expr(expr.operand)
        c_op = self.UNARY_OPERATORS.get(expr.operator)
        if c_op is None:
            raise CodeGenerationError(f"Unknown unary operator '{expr.operator}'")
        if c_op == "!":
            return f"!({operand})"
        return f"{c_op}{operand}"

    def _emit_binary(self, expr: BinaryOp) -> str:
        if expr.operator == "**":
            base = self._emit_expr(expr.left)
            exponent = self._emit_expr(expr.right)

            left_type = self._type_checker.check(expr.left, self._context.scope)
            right_type = self._type_checker.check(expr.right, self._context.scope)

            if left_type == "INTEGER" and right_type == "INTEGER":
                return f"(int)llround(pow({base}, {exponent}))"

            return f"pow({base}, {exponent})"

        if expr.operator in (".EQ.", ".NE."):
            left_type = self._type_checker.check(expr.left, self._context.scope)
            right_type = self._type_checker.check(expr.right, self._context.scope)
            if left_type == "CHARACTER" and right_type == "CHARACTER":
                left = self._emit_expr(expr.left)
                right = self._emit_expr(expr.right)
                cmp_op = "==" if expr.operator == ".EQ." else "!="
                return f"(strcmp({left}, {right}) {cmp_op} 0)"

        c_op = self.BINARY_OPERATORS.get(expr.operator)
        if c_op is None:
            raise CodeGenerationError(f"Unknown binary operator '{expr.operator}'")

        left = self._emit_expr(expr.left)
        right = self._emit_expr(expr.right)
        return f"({left} {c_op} {right})"