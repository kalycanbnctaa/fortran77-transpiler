from __future__ import annotations

from src.lexer.token_type import TokenType

OR_OPERATORS = frozenset({TokenType.OR})
AND_OPERATORS = frozenset({TokenType.AND})
NOT_OPERATOR = TokenType.NOT
RELATIONAL_OPERATORS = frozenset(
    {
        TokenType.EQ,
        TokenType.NE,
        TokenType.LT,
        TokenType.LE,
        TokenType.GT,
        TokenType.GE,
    }
)
ADDITIVE_OPERATORS = frozenset({TokenType.PLUS, TokenType.MINUS})
MULTIPLICATIVE_OPERATORS = frozenset({TokenType.STAR, TokenType.SLASH})
POWER_OPERATOR = TokenType.DSTAR