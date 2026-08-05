from __future__ import annotations

from .symbol import Symbol


class SemanticError(Exception):
    def __init__(self, message: str, line: int = 0) -> None:
        prefix = f"Line {line}: " if line else ""
        super().__init__(f"{prefix}{message}")
        self.line = line


class Scope:
    def __init__(self, name: str) -> None:
        self.name = name
        self._symbols: dict[str, Symbol] = {}

    def declare(self, symbol: Symbol) -> None:
        key = symbol.name.upper()
        if key in self._symbols:
            raise SemanticError(
                f"'{symbol.name}' is already declared in '{self.name}'", symbol.line
            )
        self._symbols[key] = symbol

    def resolve(self, name: str) -> Symbol | None:
        return self._symbols.get(name.upper())

    def has(self, name: str) -> bool:
        return name.upper() in self._symbols

    def symbols(self) -> list[Symbol]:
        return list(self._symbols.values())