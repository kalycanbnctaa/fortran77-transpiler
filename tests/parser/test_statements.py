from __future__ import annotations

import pytest

from src.ast import (
    ArrayRef,
    Assignment,
    CallStmt,
    ContinueStmt,
    DoStmt,
    GotoStmt,
    Identifier,
    IfStmt,
    PrintStmt,
    ReadStmt,
    ReturnStmt,
    StopStmt,
)
from src.parser import ParseError

from .helpers import parse_program


def _body(lines: list[str]):
    program = [
        "      PROGRAM T",
        "      IMPLICIT NONE",
        "      INTEGER I, J, N, TOTAL, VAL",
        "      REAL X",
        "      LOGICAL FLAG",
        *lines,
        "      END",
    ]
    tu = parse_program(program)
    return tu.program.body


def test_simple_assignment():
    body = _body(["      X = 1"])
    assert len(body) == 1
    assert isinstance(body[0], Assignment)
    assert body[0].target == Identifier(name="X")


def test_array_assignment_target():
    body = _body(["      A(I, J) = 1"])
    assert isinstance(body[0].target, ArrayRef)
    assert body[0].target.name == "A"


def test_if_then_else_endif():
    body = _body(
        [
            "      IF (N .GT. 0) THEN",
            "          X = 1.0",
            "      ELSE",
            "          X = 0.0",
            "      ENDIF",
        ]
    )
    assert len(body) == 1
    stmt = body[0]
    assert isinstance(stmt, IfStmt)
    assert len(stmt.then_body) == 1
    assert len(stmt.else_body) == 1


def test_if_without_else():
    body = _body(["      IF (N .GT. 0) THEN", "          X = 1.0", "      ENDIF"])
    stmt = body[0]
    assert isinstance(stmt, IfStmt)
    assert stmt.else_body == []


def test_do_loop_basic():
    body = _body(["      DO 10 I = 1, N", "          X = 1.0", "   10 CONTINUE"])
    stmt = body[0]
    assert isinstance(stmt, DoStmt)
    assert stmt.loop_var == "I"
    assert stmt.end_label == 10
    assert stmt.step is None
    assert len(stmt.body) == 2
    assert isinstance(stmt.body[1], ContinueStmt)
    assert stmt.body[1].label == 10


def test_do_loop_with_step():
    body = _body(["      DO 10 I = 1, N, 3", "   10 CONTINUE"])
    stmt = body[0]
    assert stmt.step is not None


def test_nested_do_with_shared_label_closes_both_loops():
    body = _body(
        [
            "      DO 10 I = 1, 3",
            "          DO 10 J = 1, 2",
            "              TOTAL = TOTAL + 1",
            "   10 CONTINUE",
        ]
    )
    assert len(body) == 1
    outer = body[0]
    assert isinstance(outer, DoStmt)
    assert outer.end_label == 10
    assert len(outer.body) == 1
    inner = outer.body[0]
    assert isinstance(inner, DoStmt)
    assert inner.end_label == 10
    assert len(inner.body) == 2


def test_goto():
    body = _body(["      GOTO 10", "   10 CONTINUE"])
    assert isinstance(body[0], GotoStmt)
    assert body[0].target_label == 10


def test_call_with_args():
    body = _body(["      CALL ADDSQUARE(I)"])
    stmt = body[0]
    assert isinstance(stmt, CallStmt)
    assert stmt.name == "ADDSQUARE"
    assert len(stmt.args) == 1


def test_call_without_args():
    body = _body(["      CALL FOO"])
    stmt = body[0]
    assert isinstance(stmt, CallStmt)
    assert stmt.args == []


def test_print_multiple_items():
    body = _body(["      PRINT *, X, TOTAL"])
    stmt = body[0]
    assert isinstance(stmt, PrintStmt)
    assert len(stmt.items) == 2


def test_read_targets():
    body = _body(["      READ *, X, TOTAL"])
    stmt = body[0]
    assert isinstance(stmt, ReadStmt)
    assert len(stmt.targets) == 2


def test_stop_and_return():
    body = _body(["      STOP"])
    assert isinstance(body[0], StopStmt)


def test_statement_label_is_attached():
    body = _body(["   99 X = 1"])
    assert body[0].label == 99


def test_do_loop_without_matching_label_raises():
    with pytest.raises(ParseError):
        _body(["      DO 99 I = 1, N", "          PRINT *, I"])