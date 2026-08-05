from __future__ import annotations

from .token_type import TokenType

KEYWORDS: dict[str, TokenType] = {
    "PROGRAM": TokenType.PROGRAM,
    "END": TokenType.END,
    "SUBROUTINE": TokenType.SUBROUTINE,
    "FUNCTION": TokenType.FUNCTION,
    "RETURN": TokenType.RETURN,
    "CALL": TokenType.CALL,
    "IMPLICIT": TokenType.IMPLICIT,
    "NONE": TokenType.NONE,
    "INTEGER": TokenType.INTEGER,
    "REAL": TokenType.REAL,
    "LOGICAL": TokenType.LOGICAL,
    "CHARACTER": TokenType.CHARACTER,
    "COMMON": TokenType.COMMON,
    "DO": TokenType.DO,
    "CONTINUE": TokenType.CONTINUE,
    "IF": TokenType.IF,
    "THEN": TokenType.THEN,
    "ELSE": TokenType.ELSE,
    "ENDIF": TokenType.ENDIF,
    "GOTO": TokenType.GOTO,
    "STOP": TokenType.STOP,
    "PRINT": TokenType.PRINT,
    "READ": TokenType.READ,
}