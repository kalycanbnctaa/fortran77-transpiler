from __future__ import annotations

from src.lexer.token import Token
from src.lexer.token_type import TokenType


class ParseError(Exception):
    def __init__(self, message: str, token: Token) -> None:
        super().__init__(
            f"Line {token.line}: {message} (got {token.type.name} {token.lexeme!r})"
        )
        self.token = token


class TokenCursor:
    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def _peek(self, offset: int = 0) -> Token:
        index = min(self._pos + offset, len(self._tokens) - 1)
        return self._tokens[index]

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _advance(self) -> Token:
        token = self._tokens[self._pos]
        if self._pos < len(self._tokens) - 1:
            self._pos += 1
        return token

    def _match(self, *types: TokenType) -> Token | None:
        if self._check(*types):
            return self._advance()
        return None

    def _expect(self, token_type: TokenType, message: str | None = None) -> Token:
        if not self._check(token_type):
            raise ParseError(message or f"Expected {token_type.name}", self._peek())
        return self._advance()