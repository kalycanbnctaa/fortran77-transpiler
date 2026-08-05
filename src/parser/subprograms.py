from __future__ import annotations

from src.ast import Function, Program, Subroutine
from src.lexer.token_type import TokenType


class SubprogramParserMixin:
    def _is_typed_function_header(self) -> bool:
        return self._check_type_keyword() and self._peek(1).type == TokenType.FUNCTION

    def parse_program(self) -> Program:
        token = self._expect(TokenType.PROGRAM)
        name = self._expect(TokenType.IDENTIFIER).lexeme
        declarations = self.parse_declarations()
        body = self.parse_statement_list(frozenset({TokenType.END}))
        self._expect(TokenType.END)
        return Program(name=name, declarations=declarations, body=body, line=token.line)

    def parse_subroutine(self) -> Subroutine:
        token = self._expect(TokenType.SUBROUTINE)
        name = self._expect(TokenType.IDENTIFIER).lexeme
        params = self.parse_param_list() if self._check(TokenType.LPAREN) else []
        declarations = self.parse_declarations()
        body = self.parse_statement_list(frozenset({TokenType.END}))
        self._expect(TokenType.END)
        return Subroutine(
            name=name, params=params, declarations=declarations, body=body, line=token.line
        )

    def parse_function(self) -> Function:
        return_type = ""
        start_token = self._peek()
        if self._check_type_keyword():
            return_type = self._advance().lexeme

        self._expect(TokenType.FUNCTION)
        name = self._expect(TokenType.IDENTIFIER).lexeme
        params = self.parse_param_list() if self._check(TokenType.LPAREN) else []
        declarations = self.parse_declarations()
        body = self.parse_statement_list(frozenset({TokenType.END}))
        self._expect(TokenType.END)
        return Function(
            name=name,
            params=params,
            declarations=declarations,
            body=body,
            return_type=return_type,
            line=start_token.line,
        )

    def parse_param_list(self) -> list[str]:
        self._expect(TokenType.LPAREN)
        params: list[str] = []
        if not self._check(TokenType.RPAREN):
            params.append(self._expect(TokenType.IDENTIFIER).lexeme)
            while self._match(TokenType.COMMA):
                params.append(self._expect(TokenType.IDENTIFIER).lexeme)
        self._expect(TokenType.RPAREN)
        return params