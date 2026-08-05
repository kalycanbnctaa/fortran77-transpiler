from __future__ import annotations

from pathlib import Path

from src.codegen.generator import CodeGenerator
from src.lexer.fixed_form import FixedFormProcessor
from src.lexer.lexer import Lexer
from src.parser.parser import Parser
from src.semantic.analyzer import SemanticAnalyzer


def generate(lines: list[str]) -> str:
    normalized = FixedFormProcessor(lines).normalize()
    tokens = Lexer(normalized).tokenize()
    tu = Parser(tokens).parse()
    table = SemanticAnalyzer(tu).analyze()
    return CodeGenerator(tu, table).generate()


def generate_example(relative_path: str) -> str:
    path = Path(__file__).resolve().parents[2] / relative_path
    lines = path.read_text(encoding="utf-8").splitlines()
    return generate(lines)