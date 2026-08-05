from __future__ import annotations

from .keywords import KEYWORDS
from .models import NormalizedLine
from .operators import DOTTED_OPERATORS, SYMBOL_OPERATORS
from .token import Token
from .token_type import TokenType

class LexError(Exception):
    def __init__(self, message: str, line: int) -> None:
        super().__init__(f"Line {line}: {message}")
        self.line = line

class Lexer:
    def __init__(self, lines: list[NormalizedLine]) -> None:
        self._lines = lines

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []

        for normalized in self._lines:
            if normalized.label is not None:
                tokens.append(
                    Token(TokenType.LABEL, str(normalized.label), normalized.source_line, 1)
                )

            tokens.extend(
                self._tokenize_statement(normalized.statement, normalized.source_line)
            )

        last_line = tokens[-1].line if tokens else 0
        tokens.append(Token(TokenType.EOF, "", last_line, 0))
        return tokens

    def _tokenize_statement(self, statement: str, line: int) -> list[Token]:
        tokens: list[Token] = []
        i = 0
        length = len(statement)

        while i < length:
            ch = statement[i]

            if ch.isspace():
                i += 1
                continue

            if ch == "'":
                start = i
                i += 1
                while i < length and statement[i] != "'":
                    i += 1
                if i >= length:
                    raise LexError("Unterminated character literal", line)
                lexeme = statement[start:i+1]
                tokens.append(Token(TokenType.CHARACTER_LITERAL, lexeme, line, start+1))
                i += 1
                continue

            if ch == ".":
                dotted = self._match_dotted_operator(statement, i)
                if dotted is not None:
                    lexeme, token_type = dotted
                    tokens.append(Token(token_type, lexeme, line, i + 1))
                    i += len(lexeme)
                    continue

                if i + 1 < length and statement[i + 1].isdigit():
                    start = i
                    lexeme, i = self._consume_real_from_dot(statement, i)
                    tokens.append(Token(TokenType.REAL_LITERAL, lexeme, line, start + 1))
                    continue

                raise LexError(f"Unexpected character '.' at column {i + 1}", line)

            if ch.isalpha():
                start = i
                lexeme, i = self._consume_identifier(statement, i)
                upper = lexeme.upper()
                token_type = KEYWORDS.get(upper, TokenType.IDENTIFIER)
                tokens.append(Token(token_type, upper, line, start + 1))
                continue

            if ch.isdigit():
                start = i
                lexeme, i, is_real = self._consume_number(statement, i)
                token_type = TokenType.REAL_LITERAL if is_real else TokenType.INT_LITERAL
                tokens.append(Token(token_type, lexeme, line, start + 1))
                continue

            if statement[i : i + 2] == "**":
                tokens.append(Token(TokenType.DSTAR, "**", line, i + 1))
                i += 2
                continue

            if ch in SYMBOL_OPERATORS:
                tokens.append(Token(SYMBOL_OPERATORS[ch], ch, line, i + 1))
                i += 1
                continue

            raise LexError(f"Unexpected character {ch!r} at column {i + 1}", line)

        return tokens

    @staticmethod
    def _match_dotted_operator(statement: str, start: int) -> tuple[str, TokenType] | None:
        for lexeme, token_type in DOTTED_OPERATORS.items():
            end = start + len(lexeme)
            if statement[start:end].upper() == lexeme:
                return statement[start:end], token_type
        return None

    @staticmethod
    def _consume_identifier(statement: str, start: int) -> tuple[str, int]:
        i = start
        length = len(statement)
        while i < length and statement[i].isalnum():
            i += 1
        return statement[start:i], i

    @staticmethod
    def _consume_number(statement: str, start: int) -> tuple[str, int, bool]:
        i = start
        length = len(statement)
        is_real = False

        while i < length and statement[i].isdigit():
            i += 1

        if i < length and statement[i] == ".":
            is_real = True
            i += 1
            while i < length and statement[i].isdigit():
                i += 1

        i, is_real = Lexer._consume_exponent(statement, i, is_real)

        return statement[start:i], i, is_real

    @staticmethod
    def _consume_real_from_dot(statement: str, start: int) -> tuple[str, int]:
        i = start + 1
        length = len(statement)

        while i < length and statement[i].isdigit():
            i += 1

        i, _ = Lexer._consume_exponent(statement, i, True)

        return statement[start:i], i

    @staticmethod
    def _consume_exponent(statement: str, i: int, is_real: bool) -> tuple[int, bool]:
        length = len(statement)

        if i >= length or statement[i] not in ("E", "e"):
            return i, is_real

        j = i + 1
        if j < length and statement[j] in ("+", "-"):
            j += 1

        if j < length and statement[j].isdigit():
            j += 1
            while j < length and statement[j].isdigit():
                j += 1
            return j, True

        return i, is_real