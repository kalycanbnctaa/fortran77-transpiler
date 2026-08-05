from __future__ import annotations

from .token_type import TokenType

DOTTED_OPERATORS: dict[str, TokenType] = {
    ".TRUE.": TokenType.TRUE,
    ".FALSE.": TokenType.FALSE,
    ".AND.": TokenType.AND,
    ".OR.": TokenType.OR,
    ".NOT.": TokenType.NOT,
    ".EQ.": TokenType.EQ,
    ".NE.": TokenType.NE,
    ".LT.": TokenType.LT,
    ".LE.": TokenType.LE,
    ".GT.": TokenType.GT,
    ".GE.": TokenType.GE,
}

SYMBOL_OPERATORS: dict[str, TokenType] = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "=": TokenType.ASSIGN,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ",": TokenType.COMMA,
}