from __future__ import annotations

from src.ast import Subprogram, TranslationUnit
from src.lexer.token import Token
from src.lexer.token_type import TokenType

from .base import ParseError, TokenCursor
from .declarations import DeclarationParserMixin
from .expressions import ExpressionParserMixin
from .statements import StatementParserMixin
from .subprograms import SubprogramParserMixin


class Parser(
    SubprogramParserMixin,
    StatementParserMixin,
    DeclarationParserMixin,
    ExpressionParserMixin,
    TokenCursor,
):
    def __init__(self, tokens: list[Token]) -> None:
        super().__init__(tokens)

    def parse(self) -> TranslationUnit:
        program = None
        subprograms: list[Subprogram] = []

        while not self._at_end():
            if self._check(TokenType.PROGRAM):
                program = self.parse_program()
            elif self._check(TokenType.SUBROUTINE):
                subprograms.append(self.parse_subroutine())
            elif self._check(TokenType.FUNCTION) or self._is_typed_function_header():
                subprograms.append(self.parse_function())
            else:
                raise ParseError(
                    "Expected PROGRAM, SUBROUTINE, or FUNCTION", self._peek()
                )

        return TranslationUnit(program=program, subprograms=subprograms)


__all__ = ["Parser", "ParseError"]