from __future__ import annotations

from src.ast import ArrayDecl, CommonDecl, ImplicitNoneDecl, TypeDecl

from .helpers import parse_program


def _decls(lines: list[str]):
    program = ["      PROGRAM T", *lines, "      END"]
    tu = parse_program(program)
    return tu.program.declarations


def test_implicit_none():
    decls = _decls(["      IMPLICIT NONE"])
    assert decls == [ImplicitNoneDecl()]


def test_simple_scalar_decl():
    decls = _decls(["      INTEGER I, N"])
    assert decls == [TypeDecl(base_type="INTEGER", names=["I", "N"])]


def test_array_decl():
    decls = _decls(["      INTEGER A(10)"])
    assert len(decls) == 1
    assert isinstance(decls[0], ArrayDecl)
    assert decls[0].base_type == "INTEGER"
    assert decls[0].name == "A"
    assert len(decls[0].dimensions) == 1


def test_2d_array_decl():
    decls = _decls(["      INTEGER A(3,2)"])
    assert isinstance(decls[0], ArrayDecl)
    assert len(decls[0].dimensions) == 2


def test_mixed_scalar_and_array_preserves_order():
    decls = _decls(["      INTEGER A, B(10), C"])
    assert len(decls) == 3
    assert isinstance(decls[0], TypeDecl) and decls[0].names == ["A"]
    assert isinstance(decls[1], ArrayDecl) and decls[1].name == "B"
    assert isinstance(decls[2], TypeDecl) and decls[2].names == ["C"]


def test_common_block():
    decls = _decls(["      COMMON /ACC/ RUNTOTAL, CALLCNT"])
    assert decls == [CommonDecl(block_name="ACC", variables=["RUNTOTAL", "CALLCNT"])]


def test_multiple_declarations_in_order():
    decls = _decls(
        [
            "      IMPLICIT NONE",
            "      INTEGER N, I",
            "      COMMON /ACC/ RUNTOTAL, CALLCNT",
            "      INTEGER RUNTOTAL, CALLCNT",
        ]
    )
    assert [type(d) for d in decls] == [
        ImplicitNoneDecl,
        TypeDecl,
        CommonDecl,
        TypeDecl,
    ]


def test_logical_type_decl():
    decls = _decls(["      LOGICAL FLAG"])
    assert decls == [TypeDecl(base_type="LOGICAL", names=["FLAG"])]


def test_real_type_decl():
    decls = _decls(["      REAL X, Y"])
    assert decls == [TypeDecl(base_type="REAL", names=["X", "Y"])]