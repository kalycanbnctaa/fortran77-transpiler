from __future__ import annotations

from src.ast import IntLiteral
from .scope import SemanticError
from .symbol import Symbol
from .symbol_table import SymbolTable

class CommonChecker:
    def __init__(self, table: SymbolTable) -> None:
        self._table = table

    def check(self) -> None:
        for block_name, per_subprogram in self._table.common_blocks().items():
            self._check_block(block_name, per_subprogram)

    def _check_block(self, block_name: str, per_subprogram: dict[str, list[Symbol]]) -> None:
        entries = list(per_subprogram.items())
        if len(entries) < 2:
            return

        reference_subprogram, reference_symbols = entries[0]
        reference_layout = [self._member_signature(symbol) for symbol in reference_symbols]

        for subprogram_name, symbols in entries[1:]:
            layout = [self._member_signature(symbol) for symbol in symbols]

            if len(layout) != len(reference_layout):
                raise SemanticError(
                    f"COMMON block '/{block_name}/' has {len(reference_layout)} "
                    f"member(s) in '{reference_subprogram}' but {len(layout)} "
                    f"member(s) in '{subprogram_name}'"
                )

            for index, (reference_entry, entry) in enumerate(zip(reference_layout, layout)):
                if not self._signatures_compatible(reference_entry, entry):
                    raise SemanticError(
                        f"COMMON block '/{block_name}/' member {index + 1} is "
                        f"{self._describe(reference_entry)} in '{reference_subprogram}' "
                        f"but {self._describe(entry)} in '{subprogram_name}'"
                    )

    @staticmethod
    def _member_signature(symbol: Symbol) -> tuple:
        dimension_sizes = tuple(
            dimension.value if isinstance(dimension, IntLiteral) else None
            for dimension in symbol.dimensions
        )
        return (symbol.data_type, symbol.rank, dimension_sizes)

    @staticmethod
    def _signatures_compatible(reference: tuple, other: tuple) -> bool:
        ref_type, ref_rank, ref_dims = reference
        other_type, other_rank, other_dims = other
        if ref_type != other_type or ref_rank != other_rank:
            return False
        for ref_dim, other_dim in zip(ref_dims, other_dims):
            if ref_dim is not None and other_dim is not None and ref_dim != other_dim:
                return False
        return True

    @staticmethod
    def _describe(signature: tuple) -> str:
        data_type, rank, dimension_sizes = signature
        if rank == 0:
            return data_type
        sizes = ", ".join(
            str(size) if size is not None else "?" for size in dimension_sizes
        )
        return f"{data_type}({sizes})"