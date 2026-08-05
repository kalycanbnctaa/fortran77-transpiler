from __future__ import annotations

from pathlib import Path

from src.lexer.fixed_form import FixedFormProcessor
from src.lexer.scanner import SourceScanner


def normalize(lines: list[str]):
    return FixedFormProcessor(lines).normalize()


def test_comment_lines_with_C_and_star_are_dropped():
    lines = [
        "C this is a comment",
        "* this is also a comment",
        "      PRINT *, 1",
    ]
    result = normalize(lines)
    assert len(result) == 1
    assert result[0].statement == "PRINT *, 1"


def test_blank_lines_are_dropped():
    lines = ["", "   ", "      PRINT *, 1"]
    result = normalize(lines)
    assert len(result) == 1


def test_label_is_extracted_from_columns_1_to_5():
    lines = ["   10 CONTINUE"]
    result = normalize(lines)
    assert result[0].label == 10
    assert result[0].statement == "CONTINUE"


def test_no_label_gives_none():
    lines = ["      X = 1"]
    result = normalize(lines)
    assert result[0].label is None


def test_continuation_merges_into_previous_statement():
    lines = [
        "      TOTAL = 1 +",
        "     +        2 +",
        "     +        3",
    ]
    result = normalize(lines)
    assert len(result) == 1
    assert result[0].statement == "TOTAL = 1 + 2 + 3"


def test_continuation_without_previous_line_raises():
    lines = ["     +   2"]
    try:
        normalize(lines)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_columns_beyond_72_are_ignored():
    line = "      PRINT *, 1" + " " * 56 + "SEQ0001"
    assert len(line) > 72
    result = normalize([line])
    assert "SEQ0001" not in result[0].statement
    assert result[0].statement == "PRINT *, 1"


def test_example_file_end_to_end():
    path = Path(__file__).resolve().parents[2] / "examples" / "basic" / "fixed_form_demo.f"
    source = SourceScanner.from_file(path).read_lines()
    result = normalize(source)

    statements = [n.statement for n in result]
    assert "PROGRAM DEMO" in statements
    assert "IMPLICIT NONE" in statements
    assert "TOTAL = 1 + 2 + 3" in statements

    labeled = [n for n in result if n.label == 10]
    assert len(labeled) == 1
    assert labeled[0].statement == "TOTAL = TOTAL + 1"

    printed = [n for n in result if n.statement.startswith("PRINT")]
    assert len(printed) == 1
    assert "IDENT1" not in printed[0].statement