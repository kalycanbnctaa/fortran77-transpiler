from __future__ import annotations

from src.ast import Expr, Identifier, IntLiteral
from src.semantic import Symbol

from .formatter import c_identifier


class ArrayCodegenError(Exception):
    pass


class ArrayCodegen:
    def dimension_text(self, dimension: Expr) -> str:
        if isinstance(dimension, IntLiteral):
            return str(dimension.value)
        if isinstance(dimension, Identifier):
            return f"(*{c_identifier(dimension.name)})"
        raise ArrayCodegenError(
            "Array dimension must be a constant or a dummy parameter"
        )

    def dimension_texts(self, symbol: Symbol) -> list[str]:
        return [self.dimension_text(dimension) for dimension in symbol.dimensions]

    def flat_size(self, symbol: Symbol) -> int:
        total = 1
        for dimension in symbol.dimensions:
            if not isinstance(dimension, IntLiteral):
                raise ArrayCodegenError(
                    f"Cannot compute a static size for adjustable array '{symbol.name}'"
                )
            total *= dimension.value
        return total

    def offset_text(self, index_texts: list[str], dimension_texts: list[str]) -> str:
        if len(index_texts) != len(dimension_texts):
            raise ArrayCodegenError("Index count does not match array rank")

        terms = [f"({index_texts[0]}-1)"]
        running_product: list[str] = []
        for k in range(1, len(index_texts)):
            running_product.append(dimension_texts[k - 1])
            product = "*".join(running_product)
            terms.append(f"({index_texts[k]}-1)*{product}")
        return " + ".join(terms)