from __future__ import annotations

import pytest

from src.codegen.intrinsics import IntrinsicCodegenError, emit_intrinsic


def test_max_binary():
    assert emit_intrinsic("MAX", ["a", "b"], ["INTEGER", "INTEGER"]) == "((a)>(b)?(a):(b))"


def test_max_variadic_reduces_left_to_right():
    text = emit_intrinsic("MAX", ["a", "b", "c"], ["INTEGER", "INTEGER", "INTEGER"])
    assert text == "((((a)>(b)?(a):(b)))>(c)?(((a)>(b)?(a):(b))):(c))"


def test_min_binary():
    assert emit_intrinsic("MIN", ["a", "b"], ["INTEGER", "INTEGER"]) == "((a)<(b)?(a):(b))"


def test_abs_integer_uses_stdlib_abs():
    assert emit_intrinsic("ABS", ["x"], ["INTEGER"]) == "abs(x)"


def test_abs_real_uses_fabsf():
    assert emit_intrinsic("ABS", ["x"], ["REAL"]) == "fabsf(x)"


def test_iabs_always_uses_abs():
    assert emit_intrinsic("IABS", ["x"], ["INTEGER"]) == "abs(x)"


def test_mod_integer_uses_percent():
    assert emit_intrinsic("MOD", ["a", "b"], ["INTEGER", "INTEGER"]) == "(a % b)"


def test_mod_real_uses_fmodf():
    assert emit_intrinsic("MOD", ["a", "b"], ["REAL", "INTEGER"]) == "fmodf(a, b)"


def test_int_cast():
    assert emit_intrinsic("INT", ["x"], ["REAL"]) == "(int)(x)"


def test_real_cast():
    assert emit_intrinsic("REAL", ["x"], ["INTEGER"]) == "(float)(x)"


@pytest.mark.parametrize(
    "name,c_name",
    [
        ("SQRT", "sqrtf"),
        ("EXP", "expf"),
        ("LOG", "logf"),
        ("LOG10", "log10f"),
        ("SIN", "sinf"),
        ("COS", "cosf"),
        ("TAN", "tanf"),
    ],
)
def test_unary_math_functions(name: str, c_name: str):
    assert emit_intrinsic(name, ["x"], ["REAL"]) == f"{c_name}(x)"


def test_unknown_intrinsic_raises():
    with pytest.raises(IntrinsicCodegenError):
        emit_intrinsic("UNKNOWN", ["x"], ["REAL"])