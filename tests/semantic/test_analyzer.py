from __future__ import annotations

from src.lexer.fixed_form import FixedFormProcessor
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.semantic.symbol import SymbolKind


def analyze(lines: list[str]):
    normalized = FixedFormProcessor(lines).normalize()
    tokens = Lexer(normalized).tokenize()
    tu = Parser(tokens).parse()
    return SemanticAnalyzer(tu).analyze()


def test_prefix_form_function_self_reference_resolves():
    table = analyze(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      END",
            "",
            "      INTEGER FUNCTION MULT(A, B)",
            "      IMPLICIT NONE",
            "      INTEGER A, B",
            "      MULT = A * B",
            "      END",
        ]
    )
    scope = table.scope_for("MULT")
    symbol = scope.resolve("MULT")
    assert symbol is not None
    assert symbol.kind == SymbolKind.VARIABLE
    assert symbol.data_type == "INTEGER"

    signature = table.procedure("MULT")
    assert signature is not None
    assert signature.return_type == "INTEGER"


def test_body_declared_form_function_self_reference_resolves():
    table = analyze(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      END",
            "",
            "      FUNCTION MULT(A, B)",
            "      IMPLICIT NONE",
            "      INTEGER MULT, A, B",
            "      MULT = A * B",
            "      END",
        ]
    )
    signature = table.procedure("MULT")
    assert signature is not None
    assert signature.return_type == "INTEGER"


def test_both_function_forms_produce_equivalent_signatures():
    prefix_table = analyze(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      END",
            "",
            "      INTEGER FUNCTION MULT(A, B)",
            "      IMPLICIT NONE",
            "      INTEGER A, B",
            "      MULT = A * B",
            "      END",
        ]
    )
    body_table = analyze(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      END",
            "",
            "      FUNCTION MULT(A, B)",
            "      IMPLICIT NONE",
            "      INTEGER MULT, A, B",
            "      MULT = A * B",
            "      END",
        ]
    )

    prefix_sig = prefix_table.procedure("MULT")
    body_sig = body_table.procedure("MULT")

    assert prefix_sig.return_type == body_sig.return_type
    assert [p.data_type for p in prefix_sig.param_types] == [
        p.data_type for p in body_sig.param_types
    ]


def test_niladic_prefix_function_self_reference_and_external_call_both_resolve():
    table = analyze(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      INTEGER X",
            "      X = GETVAL",
            "      END",
            "",
            "      INTEGER FUNCTION GETVAL()",
            "      IMPLICIT NONE",
            "      GETVAL = 42",
            "      END",
        ]
    )
    signature = table.procedure("GETVAL")
    assert signature is not None
    assert signature.return_type == "INTEGER"


def test_real_intrinsic_converts_integer_argument():
    table = analyze(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      INTEGER N",
            "      REAL X",
            "      N = 5",
            "      X = REAL(N)",
            "      END",
        ]
    )
    assert table is not None


def test_real_intrinsic_used_inside_expression():
    table = analyze(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      INTEGER N",
            "      REAL X",
            "      N = 3",
            "      X = REAL(N) / 2.0",
            "      END",
        ]
    )
    assert table is not None