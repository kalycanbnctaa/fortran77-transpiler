from __future__ import annotations

import pytest

from src.codegen.formatter import (
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

def test_c_type_mapping():
    assert c_type("INTEGER") == "int"
    assert c_type("REAL") == "float"
    assert c_type("LOGICAL") == "int"
    assert c_type("CHARACTER") == "char"

def test_c_type_unknown_raises():
    with pytest.raises(ValueError):
        c_type("COMPLEX")

def test_format_specifier_mapping():
    assert format_specifier("INTEGER") == "%d"
    assert format_specifier("REAL") == "%f"
    assert format_specifier("LOGICAL") == "%d"
    assert format_specifier("CHARACTER") == "%s"

def test_scan_specifier_mapping():
    assert scan_specifier("INTEGER") == "%d"
    assert scan_specifier("REAL") == "%f"
    assert scan_specifier("CHARACTER") == "%s"

def test_c_identifier_lowercases():
    assert c_identifier("RUNTOTAL") == "runtotal"
    assert c_identifier("N") == "n"

def test_format_int_literal():
    assert format_int_literal(42) == "42"
    assert format_int_literal(-7) == "-7"

def test_format_real_literal_with_decimal():
    assert format_real_literal(3.14) == "3.14"

def test_format_real_literal_whole_number_keeps_decimal_point():
    assert format_real_literal(50.0) == "50.0"
    assert format_real_literal(2.0) == "2.0"

def test_format_real_literal_small_fraction():
    assert format_real_literal(0.5) == "0.5"

def test_format_logical_literal():
    assert format_logical_literal(True) == "1"
    assert format_logical_literal(False) == "0"

def test_format_character_literal_escapes_quotes_and_backslashes():
    assert format_character_literal("Hello") == '"Hello"'
    assert format_character_literal('a"b') == '"a\\"b"'
    assert format_character_literal("a\\b") == '"a\\\\b"'

def test_character_buffer_size_uses_length_plus_one():
    assert character_buffer_size(5) == 6
    assert character_buffer_size(1) == 2

def test_character_buffer_size_defaults_to_one_when_none():
    assert character_buffer_size(None) == 2