from __future__ import annotations

from dataclasses import dataclass, field

from src.ast import IntLiteral
from src.semantic import Symbol, SymbolTable

from .formatter import c_identifier, c_type

class CommonCodegenError(Exception):
    pass

@dataclass(slots=True)
class CommonField:
    name: str
    data_type: str
    dimension_sizes: list[int] = field(default_factory=list)

    @property
    def rank(self) -> int:
        return len(self.dimension_sizes)

class CommonBlockRegistry:
    def __init__(self, table: SymbolTable) -> None:
        self._blocks: dict[str, list[CommonField]] = {}
        self._build(table)

    def _build(self, table: SymbolTable) -> None:
        for block_name, per_subprogram in table.common_blocks().items():
            entries = list(per_subprogram.items())
            if not entries:
                continue

            reference_subprogram, reference_symbols = entries[0]
            # Buat field dari referensi (akan di-check konsistensinya)
            fields = [self._to_field(symbol) for symbol in reference_symbols]

            # Periksa konsistensi dengan unit lain
            for subprogram_name, symbols in entries[1:]:
                if len(symbols) != len(fields):
                    raise CommonCodegenError(
                        f"COMMON block '/{block_name}/' has {len(fields)} member(s) in "
                        f"'{reference_subprogram}' but {len(symbols)} in '{subprogram_name}'"
                    )

                for idx, (ref_sym, sym) in enumerate(zip(reference_symbols, symbols)):
                    # Tipe dan rank harus sama
                    if ref_sym.data_type != sym.data_type or ref_sym.rank != sym.rank:
                        raise CommonCodegenError(
                            f"COMMON block '/{block_name}/' member {idx+1} type mismatch "
                            f"between '{reference_subprogram}' and '{subprogram_name}'"
                        )

                    # Dimensi harus berupa konstanta dan nilainya sama
                    for dim_idx, (ref_dim, sym_dim) in enumerate(zip(ref_sym.dimensions, sym.dimensions)):
                        if not isinstance(ref_dim, IntLiteral) or not isinstance(sym_dim, IntLiteral):
                            raise CommonCodegenError(
                                f"COMMON block '/{block_name}/' array '{ref_sym.name}' "
                                f"has non‑constant dimension in '{reference_subprogram}' or '{subprogram_name}'"
                            )
                        if ref_dim.value != sym_dim.value:
                            raise CommonCodegenError(
                                f"COMMON block '/{block_name}/' array '{ref_sym.name}' dimension mismatch: "
                                f"{ref_dim.value} vs {sym_dim.value}"
                            )

            self._blocks[block_name.upper()] = fields

    @staticmethod
    def _to_field(symbol: Symbol) -> CommonField:
        sizes: list[int] = []
        for dimension in symbol.dimensions:
            if not isinstance(dimension, IntLiteral):
                raise CommonCodegenError(
                    f"COMMON array '{symbol.name}' must have constant dimensions"
                )
            sizes.append(dimension.value)
        return CommonField(name=symbol.name, data_type=symbol.data_type, dimension_sizes=sizes)

    def block_names(self) -> list[str]:
        return list(self._blocks.keys())

    def fields(self, block_name: str) -> list[CommonField]:
        return self._blocks[block_name.upper()]

    def struct_type_name(self, block_name: str) -> str:
        return f"{block_name.lower()}_t"

    def instance_name(self, block_name: str) -> str:
        return block_name.lower()

    def field_c_name(self, block_name: str, index: int) -> str:
        return c_identifier(self.fields(block_name)[index].name)

    def member_access(self, block_name: str, index: int) -> str:
        return f"{self.instance_name(block_name)}.{self.field_c_name(block_name, index)}"

    def render_struct(self, block_name: str) -> list[str]:
        lines = [f"struct {self.struct_type_name(block_name)} {{"]
        for member in self.fields(block_name):
            base = c_type(member.data_type)
            name = c_identifier(member.name)
            if member.rank == 0:
                lines.append(f"    {base} {name};")
            else:
                size = 1
                for dim in member.dimension_sizes:
                    size *= dim
                lines.append(f"    {base} {name}[{size}];")
        lines.append(f"}} {self.instance_name(block_name)};")
        return lines