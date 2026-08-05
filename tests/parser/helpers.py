from __future__ import annotations

from src.lexer.fixed_form import FixedFormProcessor
from src.lexer.lexer import Lexer
from src.lexer.token import Token
from src.parser.parser import Parser


def tokenize(lines: list[str]) -> list[Token]:
    normalized = FixedFormProcessor(lines).normalize()
    return Lexer(normalized).tokenize()


def parse_program(lines: list[str]):
    tokens = tokenize(lines)
    return Parser(tokens).parse()


def parse_expr(text: str):
    tokens = tokenize([f"      X = {text}"])
    parser = Parser(tokens)
    parser._advance()
    parser._advance()
    return parser.parse_expression()