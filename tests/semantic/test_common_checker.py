from __future__ import annotations

import pytest

from src.lexer.fixed_form import FixedFormProcessor
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer
from src.semantic.scope import SemanticError

def analyze(lines: list[str]):
    normalized = FixedFormProcessor(lines).normalize()
    tokens = Lexer(normalized).tokenize()
    tu = Parser(tokens).parse()
    return SemanticAnalyzer(tu).analyze()

def test_common_block_matching_array_sizes_passes():
    analyze(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      INTEGER A(10)",
            "      COMMON /BLK/ A",
            "      CALL SUB",
            "      END",
            "",
            "      SUBROUTINE SUB",
            "      IMPLICIT NONE",
            "      INTEGER B(10)",
            "      COMMON /BLK/ B",
            "      END",
        ]
    )

def test_common_block_mismatched_array_sizes_raises():
    with pytest.raises(SemanticError):
        analyze(
            [
                "      PROGRAM MAIN",
                "      IMPLICIT NONE",
                "      INTEGER A(10)",
                "      COMMON /BLK/ A",
                "      CALL SUB",
                "      END",
                "",
                "      SUBROUTINE SUB",
                "      IMPLICIT NONE",
                "      INTEGER B(20)",
                "      COMMON /BLK/ B",
                "      END",
            ]
        )

def test_common_block_mismatched_type_still_raises():
    with pytest.raises(SemanticError):
        analyze(
            [
                "      PROGRAM MAIN",
                "      IMPLICIT NONE",
                "      INTEGER X",
                "      COMMON /BLK/ X",
                "      CALL SUB",
                "      END",
                "",
                "      SUBROUTINE SUB",
                "      IMPLICIT NONE",
                "      REAL Y",
                "      COMMON /BLK/ Y",
                "      END",
            ]
        )

def test_common_block_with_dummy_parameter_bound_is_not_falsely_rejected():
    analyze(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      INTEGER A(10)",
            "      COMMON /BLK/ A",
            "      CALL SUB(10)",
            "      END",
            "",
            "      SUBROUTINE SUB(N)",
            "      IMPLICIT NONE",
            "      INTEGER N",
            "      INTEGER B(N)",
            "      COMMON /BLK/ B",
            "      END",
        ]
    )