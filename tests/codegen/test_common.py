from __future__ import annotations

import pytest

from src.codegen.common import CommonBlockRegistry, CommonCodegenError
from src.lexer.fixed_form import FixedFormProcessor
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer

def build_table(lines: list[str]):
    normalized = FixedFormProcessor(lines).normalize()
    tokens = Lexer(normalized).tokenize()
    tu = Parser(tokens).parse()
    return SemanticAnalyzer(tu).analyze()

def test_fields_taken_from_first_declaring_subprogram():
    table = build_table(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      INTEGER RUNTOTAL, CALLCNT",
            "      COMMON /ACC/ RUNTOTAL, CALLCNT",
            "      CALL SUB",
            "      END",
            "",
            "      SUBROUTINE SUB",
            "      IMPLICIT NONE",
            "      INTEGER TOTAL, CNT",
            "      COMMON /ACC/ TOTAL, CNT",
            "      END",
        ]
    )
    registry = CommonBlockRegistry(table)
    fields = registry.fields("ACC")
    assert [f.name for f in fields] == ["RUNTOTAL", "CALLCNT"]

def test_member_access_uses_canonical_field_regardless_of_local_alias():
    table = build_table(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      INTEGER RUNTOTAL, CALLCNT",
            "      COMMON /ACC/ RUNTOTAL, CALLCNT",
            "      CALL SUB",
            "      END",
            "",
            "      SUBROUTINE SUB",
            "      IMPLICIT NONE",
            "      INTEGER TOTAL, CNT",
            "      COMMON /ACC/ TOTAL, CNT",
            "      END",
        ]
    )
    registry = CommonBlockRegistry(table)
    assert registry.member_access("ACC", 0) == "acc.runtotal"
    assert registry.member_access("ACC", 1) == "acc.callcnt"

def test_render_struct_scalar_members():
    table = build_table(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      INTEGER X",
            "      COMMON /BLK/ X",
            "      END",
        ]
    )
    registry = CommonBlockRegistry(table)
    lines = registry.render_struct("BLK")
    assert lines == [
        "struct blk_t {",
        "    int x;",
        "} blk;",
    ]

def test_render_struct_array_member():
    table = build_table(
        [
            "      PROGRAM MAIN",
            "      IMPLICIT NONE",
            "      INTEGER A(10)",
            "      COMMON /BLK/ A",
            "      END",
        ]
    )
    registry = CommonBlockRegistry(table)
    lines = registry.render_struct("BLK")
    assert lines == [
        "struct blk_t {",
        "    int a[10];",
        "} blk;",
    ]

def test_adjustable_common_array_raises():
    table = build_table(
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
    with pytest.raises(CommonCodegenError):
        CommonBlockRegistry(table)