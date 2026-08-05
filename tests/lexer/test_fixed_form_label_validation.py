from __future__ import annotations

import pytest

from src.lexer.fixed_form import FixedFormProcessor


def normalize(lines: list[str]):
    return FixedFormProcessor(lines).normalize()


def test_non_numeric_label_field_raises_clear_error():
    lines = ["PROGRAM LEXDEMO"]
    with pytest.raises(ValueError, match="columns 1-5 must contain only a numeric label"):
        normalize(lines)