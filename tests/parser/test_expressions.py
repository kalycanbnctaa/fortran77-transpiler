from __future__ import annotations

from src.ast import ArrayRef, BinaryOp, Identifier, IntLiteral, LogicalLiteral, RealLiteral, UnaryOp

from .helpers import parse_expr

def test_int_and_real_literals():
    assert parse_expr("42") == IntLiteral(value=42)
    assert parse_expr("3.14") == RealLiteral(value=3.14)

def test_logical_literals():
    assert parse_expr(".TRUE.") == LogicalLiteral(value=True)
    assert parse_expr(".FALSE.") == LogicalLiteral(value=False)

def test_identifier():
    assert parse_expr("FOO") == Identifier(name="FOO")

def test_array_ref_with_multiple_indices():
    expr = parse_expr("A(I, J)")
    assert isinstance(expr, ArrayRef)
    assert expr.name == "A"
    assert expr.indices == [Identifier(name="I"), Identifier(name="J")]

def test_additive_is_left_associative():
    expr = parse_expr("A - B + C")
    assert isinstance(expr, BinaryOp)
    assert expr.operator == "+"
    assert isinstance(expr.left, BinaryOp)
    assert expr.left.operator == "-"

def test_multiplicative_binds_tighter_than_additive():
    expr = parse_expr("A + B * C")
    assert isinstance(expr, BinaryOp)
    assert expr.operator == "+"
    assert isinstance(expr.right, BinaryOp)
    assert expr.right.operator == "*"

def test_power_is_right_associative():
    expr = parse_expr("A ** B ** C")
    assert isinstance(expr, BinaryOp)
    assert expr.operator == "**"
    assert isinstance(expr.right, BinaryOp)
    assert expr.right.operator == "**"

def test_power_binds_tighter_than_unary_minus():
    expr = parse_expr("-A ** 2")
    assert isinstance(expr, UnaryOp)
    assert expr.operator == "-"
    assert isinstance(expr.operand, BinaryOp)
    assert expr.operand.operator == "**"

def test_parentheses_override_precedence():
    expr = parse_expr("(A + B) * C")
    assert isinstance(expr, BinaryOp)
    assert expr.operator == "*"
    assert isinstance(expr.left, BinaryOp)
    assert expr.left.operator == "+"

def test_relational_operator():
    expr = parse_expr("N .GT. 0")
    assert isinstance(expr, BinaryOp)
    assert expr.operator == ".GT."

def test_and_or_not_precedence():
    expr = parse_expr("N .GT. 0 .AND. FLAG .OR. .NOT. FLAG")
    assert isinstance(expr, BinaryOp)
    assert expr.operator == ".OR."
    assert isinstance(expr.left, BinaryOp)
    assert expr.left.operator == ".AND."
    assert isinstance(expr.right, UnaryOp)
    assert expr.right.operator == ".NOT."

def test_lowercase_operators_are_normalized_uppercase():
    expr = parse_expr("a .and. b")
    assert expr.operator == ".AND."

def test_real_intrinsic_call_parses():
    expr = parse_expr("REAL(N)")
    assert isinstance(expr, ArrayRef)
    assert expr.name == "REAL"
    assert expr.indices == [Identifier(name="N")]

def test_real_intrinsic_call_with_expression_argument():
    expr = parse_expr("REAL(N + 1)")
    assert isinstance(expr, ArrayRef)
    assert expr.name == "REAL"
    assert len(expr.indices) == 1
    assert isinstance(expr.indices[0], BinaryOp)

def test_real_intrinsic_call_usable_inside_larger_expression():
    expr = parse_expr("REAL(N) / 2.0")
    assert isinstance(expr, BinaryOp)
    assert expr.operator == "/"
    assert isinstance(expr.left, ArrayRef)
    assert expr.left.name == "REAL"