from __future__ import annotations

from .symbol import SymbolKind
from .symbol_table import SymbolTable


def format_symbol_table(table: SymbolTable) -> str:
    lines: list[str] = []

    lines.append("Procedures")
    lines.append("----------")
    for signature in table.procedures():
        params = ", ".join(
            f"{param.data_type}{f'({param.rank}D)' if param.rank else ''}"
            for param in signature.param_types
        )
        return_part = f" -> {signature.return_type}" if signature.return_type else ""
        lines.append(f"{signature.kind.name} {signature.name}({params}){return_part}")

    for scope in table.all_scopes():
        lines.append("")
        header = f"Scope: {scope.name}"
        lines.append(header)
        lines.append("-" * len(header))
        for symbol in scope.symbols():
            parts = [symbol.name, symbol.kind.name, symbol.data_type]
            if symbol.kind == SymbolKind.ARRAY:
                parts.append(f"rank={symbol.rank}")
            if symbol.is_parameter:
                parts.append("parameter")
            if symbol.common_block:
                parts.append(f"common=/{symbol.common_block}/[{symbol.common_index}]")
            lines.append("  " + " ".join(parts))

    return "\n".join(lines)