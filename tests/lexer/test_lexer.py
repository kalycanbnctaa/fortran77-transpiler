from __future__ import annotations

from pathlib import Path

import pytest

from src.lexer.fixed_form import FixedFormProcessor
from src.lexer.lexer import LexError, Lexer
from src.lexer.scanner import SourceScanner
from src.lexer.token_type import TokenType


def tokenize(lines: list[str]):
    normalized = FixedFormProcessor(lines).normalize()
    return Lexer(normalized).tokenize()


def token_types(tokens):
    return [t.type for t in tokens]


def test_keyword_and_identifier():
    tokens = tokenize(["      PROGRAM DEMO"])
    assert token_types(tokens) == [TokenType.PROGRAM, TokenType.IDENTIFIER, TokenType.EOF]
    assert tokens[1].lexeme == "DEMO"


def test_case_insensitivity():
    tokens = tokenize(["      program Demo"])
    assert token_types(tokens) == [TokenType.PROGRAM, TokenType.IDENTIFIER, TokenType.EOF]
    assert tokens[1].lexeme == "DEMO"


def test_int_literal():
    tokens = tokenize(["      X = 42"])
    assert token_types(tokens) == [
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.INT_LITERAL,
        TokenType.EOF,
    ]
    assert tokens[2].lexeme == "42"


def test_real_literal_with_decimal_point():
    tokens = tokenize(["      X = 3.14"])
    assert tokens[2].type == TokenType.REAL_LITERAL
    assert tokens[2].lexeme == "3.14"


def test_real_literal_starting_with_dot():
    tokens = tokenize(["      X = .5"])
    assert tokens[2].type == TokenType.REAL_LITERAL
    assert tokens[2].lexeme == ".5"


def test_real_literal_with_exponent():
    tokens = tokenize(["      X = 1.0E5"])
    assert tokens[2].type == TokenType.REAL_LITERAL
    assert tokens[2].lexeme == "1.0E5"


def test_real_literal_dot_with_exponent():
    tokens = tokenize(["      X = .5E2"])
    assert tokens[2].type == TokenType.REAL_LITERAL
    assert tokens[2].lexeme == ".5E2"


def test_logical_literals():
    tokens = tokenize(["      X = .TRUE."])
    assert tokens[2].type == TokenType.TRUE
    tokens = tokenize(["      X = .FALSE."])
    assert tokens[2].type == TokenType.FALSE


@pytest.mark.parametrize(
    "text,expected",
    [
        (".AND.", TokenType.AND),
        (".OR.", TokenType.OR),
        (".NOT.", TokenType.NOT),
        (".EQ.", TokenType.EQ),
        (".NE.", TokenType.NE),
        (".LT.", TokenType.LT),
        (".LE.", TokenType.LE),
        (".GT.", TokenType.GT),
        (".GE.", TokenType.GE),
    ],
)
def test_dotted_operators(text: str, expected: TokenType):
    tokens = tokenize([f"      IF (A {text} B) THEN"])
    dotted = [t for t in tokens if t.type == expected]
    assert len(dotted) == 1


def test_arithmetic_and_assignment_operators():
    tokens = tokenize(["      X = A + B - C * D / E ** F"])
    assert token_types(tokens) == [
        TokenType.IDENTIFIER,
        TokenType.ASSIGN,
        TokenType.IDENTIFIER,
        TokenType.PLUS,
        TokenType.IDENTIFIER,
        TokenType.MINUS,
        TokenType.IDENTIFIER,
        TokenType.STAR,
        TokenType.IDENTIFIER,
        TokenType.SLASH,
        TokenType.IDENTIFIER,
        TokenType.DSTAR,
        TokenType.IDENTIFIER,
        TokenType.EOF,
    ]


def test_delimiters_and_array_access():
    tokens = tokenize(["      A(I, J) = 1"])
    assert token_types(tokens) == [
        TokenType.IDENTIFIER,
        TokenType.LPAREN,
        TokenType.IDENTIFIER,
        TokenType.COMMA,
        TokenType.IDENTIFIER,
        TokenType.RPAREN,
        TokenType.ASSIGN,
        TokenType.INT_LITERAL,
        TokenType.EOF,
    ]


def test_label_token_emitted_before_statement():
    tokens = tokenize(["   10 CONTINUE"])
    assert token_types(tokens) == [TokenType.LABEL, TokenType.CONTINUE, TokenType.EOF]
    assert tokens[0].lexeme == "10"


def test_unexpected_character_raises_lex_error():
    with pytest.raises(LexError):
        tokenize(["      X = 1 $ 2"])


def test_unterminated_dot_operator_raises_lex_error():
    with pytest.raises(LexError):
        tokenize(["      X = .XYZ."])


def test_lexer_demo_example_tokenizes_without_error():
    path = Path(__file__).resolve().parents[2] / "examples" / "basic" / "lexer_demo.f"
    source = SourceScanner.from_file(path).read_lines()
    normalized = FixedFormProcessor(source).normalize()
    tokens = Lexer(normalized).tokenize()

    assert tokens[-1].type == TokenType.EOF
    keyword_types = {
        TokenType.PROGRAM,
        TokenType.SUBROUTINE,
        TokenType.IF,
        TokenType.THEN,
        TokenType.ELSE,
        TokenType.ENDIF,
        TokenType.CALL,
        TokenType.RETURN,
        TokenType.PRINT,
    }
    found = {t.type for t in tokens} & keyword_types
    assert found == keyword_types