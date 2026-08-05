from __future__ import annotations

from pathlib import Path

from src.ast import DoStmt, Function, Program, Subroutine
from src.lexer.fixed_form import FixedFormProcessor
from src.lexer.lexer import Lexer
from src.lexer.scanner import SourceScanner
from src.parser.parser import Parser

from .helpers import parse_program


def test_program_name_and_end():
    tu = parse_program(["      PROGRAM FOO", "      END"])
    assert isinstance(tu.program, Program)
    assert tu.program.name == "FOO"


def test_subroutine_with_params():
    tu = parse_program(
        [
            "      PROGRAM MAIN",
            "      END",
            "",
            "      SUBROUTINE SHOW(VAL)",
            "      IMPLICIT NONE",
            "      REAL VAL",
            "      RETURN",
            "      END",
        ]
    )
    assert len(tu.subprograms) == 1
    sub = tu.subprograms[0]
    assert isinstance(sub, Subroutine)
    assert sub.name == "SHOW"
    assert sub.params == ["VAL"]


def test_function_with_type_prefix():
    tu = parse_program(
        [
            "      PROGRAM MAIN",
            "      END",
            "",
            "      INTEGER FUNCTION MULT(A, B)",
            "      IMPLICIT NONE",
            "      INTEGER A, B",
            "      MULT = A * B",
            "      END",
        ]
    )
    fn = tu.subprograms[0]
    assert isinstance(fn, Function)
    assert fn.name == "MULT"
    assert fn.return_type == "INTEGER"
    assert fn.params == ["A", "B"]


def test_function_with_type_declared_in_body():
    tu = parse_program(
        [
            "      PROGRAM MAIN",
            "      END",
            "",
            "      FUNCTION MULT(A, B)",
            "      INTEGER MULT, A, B",
            "      MULT = A * B",
            "      END",
        ]
    )
    fn = tu.subprograms[0]
    assert isinstance(fn, Function)
    assert fn.return_type == ""
    assert fn.params == ["A", "B"]


def test_multiple_subprograms_after_program():
    tu = parse_program(
        [
            "      PROGRAM MAIN",
            "      END",
            "",
            "      SUBROUTINE A()",
            "      END",
            "",
            "      SUBROUTINE B()",
            "      END",
        ]
    )
    assert [s.name for s in tu.subprograms] == ["A", "B"]


def _parse_example(relative_path: str):
    path = Path(__file__).resolve().parents[2] / relative_path
    lines = SourceScanner.from_file(path).read_lines()
    normalized = FixedFormProcessor(lines).normalize()
    tokens = Lexer(normalized).tokenize()
    return Parser(tokens).parse()


def test_sumsquares_example_end_to_end():
    tu = _parse_example("examples/common/sumsquares.f")
    assert tu.program.name == "SUMSQUARES"
    assert [s.name for s in tu.subprograms] == ["ADDSQUARE"]

    do_loops = [s for s in tu.program.body if isinstance(s, DoStmt)]
    assert len(do_loops) == 1
    assert do_loops[0].end_label == 10


def test_matsum_example_end_to_end_nested_shared_label():
    tu = _parse_example("examples/arrays/matsum.f")
    assert tu.program.name == "MATSUM"

    outer_do = next(s for s in tu.program.body if isinstance(s, DoStmt))
    assert outer_do.end_label == 10
    assert len(outer_do.body) == 1
    inner_do = outer_do.body[0]
    assert isinstance(inner_do, DoStmt)
    assert inner_do.end_label == 10


def test_lexer_demo_example_parses_without_error():
    tu = _parse_example("examples/basic/lexer_demo.f")
    assert tu.program.name == "LEXDEMO"
    assert [s.name for s in tu.subprograms] == ["SHOW"]

def test_subroutine_without_parentheses():
    tu = parse_program(
        [
            "      PROGRAM MAIN",
            "      END",
            "",
            "      SUBROUTINE FOO",
            "      END",
        ]
    )
    sub = tu.subprograms[0]
    assert isinstance(sub, Subroutine)
    assert sub.name == "FOO"
    assert sub.params == []


def test_subroutine_without_parentheses_with_declarations():
    tu = parse_program(
        [
            "      PROGRAM MAIN",
            "      END",
            "",
            "      SUBROUTINE FOO",
            "      IMPLICIT NONE",
            "      INTEGER X",
            "      X = 1",
            "      END",
        ]
    )
    sub = tu.subprograms[0]
    assert isinstance(sub, Subroutine)
    assert sub.params == []
    assert len(sub.body) == 1