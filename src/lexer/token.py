from __future__ import annotations

from dataclasses import dataclass

from .token_type import TokenType


@dataclass(slots=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int