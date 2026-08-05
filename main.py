from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src import __version__
from src.codegen import CodeGenerationError, CodeGenerator
from src.lexer import FixedFormProcessor, Lexer, SourceScanner
from src.parser import ParseError, Parser
from src.semantic import SemanticAnalyzer, SemanticError, format_symbol_table
from src.visualization import node_children, node_label, print_tree


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fortran77-transpiler",
        description="A Fortran 77 to C transpiler.",
    )

    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        help="Path to the input Fortran source file.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to the generated C source file.",
    )

    parser.add_argument(
        "--tokens",
        action="store_true",
        help="Display lexer output.",
    )

    parser.add_argument(
        "--ast",
        action="store_true",
        help="Display abstract syntax tree.",
    )

    parser.add_argument(
        "--symbols",
        action="store_true",
        help="Display symbol table.",
    )

    parser.add_argument(
        "--emit",
        action="store_true",
        help="Generate C source code.",
    )

    parser.add_argument(
        "--source-map",
        action="store_true",
        help="Add source map comments to generated C code.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def validate_input(path: Path) -> Path:
    input_path = path.resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file '{input_path}' does not exist.")

    if not input_path.is_file():
        raise IsADirectoryError(f"'{input_path}' is not a file.")

    return input_path


def load_tokens(input_path: Path) -> list:
    source_lines = SourceScanner.from_file(input_path).read_lines()
    normalized = FixedFormProcessor(source_lines).normalize()
    return Lexer(normalized).tokenize()


def parse_translation_unit(input_path: Path):
    tokens = load_tokens(input_path)
    return Parser(tokens).parse()


def print_tokens(input_path: Path) -> None:
    tokens = load_tokens(input_path)
    for token in tokens:
        print(f"{token.type.name:<15} {token.lexeme}")


def print_ast(input_path: Path) -> None:
    translation_unit = parse_translation_unit(input_path)
    print_tree(translation_unit, node_label, node_children)


def analyze(input_path: Path):
    translation_unit = parse_translation_unit(input_path)
    table = SemanticAnalyzer(translation_unit).analyze()
    return translation_unit, table


def print_symbols(input_path: Path) -> None:
    _, table = analyze(input_path)
    print(format_symbol_table(table))


def generate_code(input_path: Path, source_map: bool = False) -> str:
    translation_unit, table = analyze(input_path)
    return CodeGenerator(translation_unit, table, source_map).generate()


def emit_c_source(input_path: Path, output: Path | None, source_map: bool) -> None:
    code = generate_code(input_path, source_map)
    if output is not None:
        output.write_text(code, encoding="utf-8")
        print(f"Wrote C source to {output.resolve()}")
    else:
        print(code)


def run_pipeline(args: argparse.Namespace) -> int:
    input_path = validate_input(args.input)

    print(f"Input : {input_path}")

    if args.output is not None:
        print(f"Output: {args.output.resolve()}")

    stages_requested = args.tokens or args.ast or args.symbols or args.emit

    if args.tokens:
        print("Stage: Lexer")
        print_tokens(input_path)

    if args.ast:
        print("Stage: Parser / AST")
        print_ast(input_path)

    if args.symbols:
        print("Stage: Semantic Analysis")
        print_symbols(input_path)

    if args.emit:
        print("Stage: Code Generation")
        emit_c_source(input_path, args.output, args.source_map)

    if not stages_requested:
        print("Stage: Full Pipeline")
        emit_c_source(input_path, args.output, args.source_map)

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.input is None:
        parser.print_help()
        return 0

    try:
        return run_pipeline(args)
    except ParseError as error:
        print(f"Syntax error: {error}", file=sys.stderr)
        return 1
    except SemanticError as error:
        print(f"Semantic error: {error}", file=sys.stderr)
        return 1
    except CodeGenerationError as error:
        print(f"Code generation error: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())