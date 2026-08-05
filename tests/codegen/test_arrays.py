from __future__ import annotations

import pytest

from src.ast import Identifier, IntLiteral
from src.codegen.arrays import ArrayCodegen, ArrayCodegenError
from src.semantic.symbol import Symbol, SymbolKind


def test_dimension_text_constant():
    codegen = ArrayCodegen()
    assert codegen.dimension_text(IntLiteral(value=3)) == "3"


def test_dimension_text_parameter_bound():
    codegen = ArrayCodegen()
    assert codegen.dimension_text(Identifier(name="N")) == "(*n)"

def test_dimension_text_unsupported_raises():
    codegen = ArrayCodegen()

    class _Bogus:
        pass

    with pytest.raises(ArrayCodegenError):
        codegen.dimension_text(_Bogus())

def test_flat_size_multiplies_all_constant_dimensions():
    codegen = ArrayCodegen()
    symbol = Symbol(
        name="A",
        kind=SymbolKind.ARRAY,
        data_type="INTEGER",
        dimensions=[IntLiteral(value=3), IntLiteral(value=2)],
    )
    assert codegen.flat_size(symbol) == 6


def test_flat_size_raises_for_adjustable_dimension():
    codegen = ArrayCodegen()
    symbol = Symbol(
        name="A",
        kind=SymbolKind.ARRAY,
        data_type="INTEGER",
        dimensions=[Identifier(name="N")],
    )
    with pytest.raises(ArrayCodegenError):
        codegen.flat_size(symbol)


def test_offset_text_1d():
    codegen = ArrayCodegen()
    assert codegen.offset_text(["i"], ["10"]) == "(i-1)"


def test_offset_text_2d_constant_dimension():
    codegen = ArrayCodegen()
    text = codegen.offset_text(["1", "2"], ["3", "2"])
    assert text == "(1-1) + (2-1)*3"


def test_offset_text_2d_matches_matsum_example():
    codegen = ArrayCodegen()
    text = codegen.offset_text(["2", "1"], ["3", "2"])
    assert text == "(2-1) + (1-1)*3"


def test_offset_text_with_parameter_bound():
    codegen = ArrayCodegen()
    text = codegen.offset_text(["i", "j"], ["(*n)", "(*m)"])
    assert text == "(i-1) + (j-1)*(*n)"


def test_offset_text_mismatched_rank_raises():
    codegen = ArrayCodegen()
    with pytest.raises(ArrayCodegenError):
        codegen.offset_text(["i", "j"], ["3"])