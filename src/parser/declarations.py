from __future__ import annotations

from src.ast import ArrayDecl, CommonDecl, Decl, ImplicitNoneDecl, TypeDecl
from src.lexer.token_type import TokenType

TYPE_KEYWORDS = (TokenType.INTEGER, TokenType.REAL, TokenType.LOGICAL, TokenType.CHARACTER)

class DeclarationParserMixin:
    def _check_type_keyword(self) -> bool:
        return self._check(*TYPE_KEYWORDS)

    def parse_declarations(self) -> list[Decl]:
        decls: list[Decl] = []
        while True:
            if self._check(TokenType.IMPLICIT):
                decls.append(self.parse_implicit_none())
            elif self._check(TokenType.COMMON):
                decls.append(self.parse_common())
            elif self._check_type_keyword():
                decls.extend(self.parse_type_decl())
            else:
                break
        return decls

    def parse_implicit_none(self) -> ImplicitNoneDecl:
        token = self._expect(TokenType.IMPLICIT)
        self._expect(TokenType.NONE)
        return ImplicitNoneDecl(line=token.line)

    def parse_common(self) -> CommonDecl:
        token = self._expect(TokenType.COMMON)
        self._expect(TokenType.SLASH)
        block_name = self._expect(TokenType.IDENTIFIER).lexeme
        self._expect(TokenType.SLASH)

        variables = [self._expect(TokenType.IDENTIFIER).lexeme]
        while self._match(TokenType.COMMA):
            variables.append(self._expect(TokenType.IDENTIFIER).lexeme)

        return CommonDecl(block_name=block_name, variables=variables, line=token.line)

    def parse_type_decl(self) -> list[Decl]:
        type_token = self._advance()
        base_type = type_token.lexeme
        char_length: int | None = None

        # Support CHARACTER*N
        if base_type == "CHARACTER" and self._match(TokenType.STAR):
            length_token = self._expect(TokenType.INT_LITERAL)
            char_length = int(length_token.lexeme)

        decls: list[Decl] = []
        pending_names: list[str] = []

        def flush() -> None:
            if pending_names:
                decls.append(
                    TypeDecl(
                        base_type=base_type,
                        names=list(pending_names),
                        length=char_length,
                        line=type_token.line,
                    )
                )
                pending_names.clear()

        while True:
            ident_token = self._expect(TokenType.IDENTIFIER)
            if self._check(TokenType.LPAREN):
                flush()
                self._advance()
                dimensions = [self.parse_expression()]
                while self._match(TokenType.COMMA):
                    dimensions.append(self.parse_expression())
                self._expect(TokenType.RPAREN)
                decls.append(
                    ArrayDecl(
                        base_type=base_type,
                        name=ident_token.lexeme,
                        dimensions=dimensions,
                        line=ident_token.line,
                    )
                )
            else:
                pending_names.append(ident_token.lexeme)

            if not self._match(TokenType.COMMA):
                break

        flush()
        return decls