from __future__ import annotations

from pathlib import Path

from src.ast import (
    ArrayDecl,
    ArrayRef,
    Assignment,
    BinaryOp,
    CommonDecl,
    DoStmt,
    Identifier,
    IfStmt,
    ImplicitNoneDecl,
    IntLiteral,
    LogicalLiteral,
    Program,
    RealLiteral,
    TypeDecl,
    UnaryOp,
)
from src.lexer.fixed_form import FixedFormProcessor
from src.lexer.lexer import Lexer
from src.lexer.scanner import SourceScanner
from src.parser.parser import Parser
from src.visualization.ast_dump import expr_to_str, node_children, node_label


def test_expr_to_str_literals():
    assert expr_to_str(IntLiteral(value=42)) == "42"
    assert expr_to_str(RealLiteral(value=3.14)) == "3.14"
    assert expr_to_str(LogicalLiteral(value=True)) == ".TRUE."
    assert expr_to_str(LogicalLiteral(value=False)) == ".FALSE."
    assert expr_to_str(Identifier(name="X")) == "X"


def test_expr_to_str_array_ref():
    expr = ArrayRef(name="A", indices=[Identifier(name="I"), Identifier(name="J")])
    assert expr_to_str(expr) == "A(I, J)"


def test_expr_to_str_binary_op_is_parenthesized():
    expr = BinaryOp(operator="+", left=Identifier(name="A"), right=Identifier(name="B"))
    assert expr_to_str(expr) == "(A + B)"


def test_expr_to_str_unary_op():
    expr = UnaryOp(operator="-", operand=Identifier(name="A"))
    assert expr_to_str(expr) == "-A"


def test_expr_to_str_none_is_empty():
    assert expr_to_str(None) == ""


def test_node_label_type_decl():
    decl = TypeDecl(base_type="INTEGER", names=["I", "N"])
    assert node_label(decl) == "TypeDecl INTEGER I, N"


def test_node_label_array_decl():
    decl = ArrayDecl(base_type="INTEGER", name="A", dimensions=[IntLiteral(value=3)])
    assert node_label(decl) == "ArrayDecl INTEGER A(3)"


def test_node_label_common_decl():
    decl = CommonDecl(block_name="ACC", variables=["X", "Y"])
    assert node_label(decl) == "CommonDecl /ACC/ X, Y"


def test_node_label_implicit_none():
    assert node_label(ImplicitNoneDecl()) == "ImplicitNoneDecl"


def test_node_label_assignment():
    stmt = Assignment(target=Identifier(name="X"), value=IntLiteral(value=1))
    assert node_label(stmt) == "Assignment X = 1"


def test_node_children_program_concatenates_decls_and_body():
    program = Program(
        name="T",
        declarations=[ImplicitNoneDecl()],
        body=[Assignment(target=Identifier(name="X"), value=IntLiteral(value=1))],
    )
    children = node_children(program)
    assert len(children) == 2
    assert isinstance(children[0], ImplicitNoneDecl)
    assert isinstance(children[1], Assignment)


def test_node_children_do_stmt_is_its_body():
    inner = Assignment(target=Identifier(name="X"), value=IntLiteral(value=1))
    do_stmt = DoStmt(loop_var="I", start=IntLiteral(value=1), end=IntLiteral(value=10), body=[inner])
    assert node_children(do_stmt) == [inner]


def test_node_children_if_stmt_wraps_else_in_group():
    then_stmt = Assignment(target=Identifier(name="X"), value=IntLiteral(value=1))
    else_stmt = Assignment(target=Identifier(name="X"), value=IntLiteral(value=0))
    if_stmt = IfStmt(condition=None, then_body=[then_stmt], else_body=[else_stmt])

    children = node_children(if_stmt)
    assert len(children) == 2
    assert children[0] is then_stmt
    assert node_label(children[1]) == "Else"
    assert node_children(children[1]) == [else_stmt]


def test_node_children_if_stmt_without_else_has_no_group():
    then_stmt = Assignment(target=Identifier(name="X"), value=IntLiteral(value=1))
    if_stmt = IfStmt(condition=None, then_body=[then_stmt], else_body=[])
    assert node_children(if_stmt) == [then_stmt]


def _parse_example(relative_path: str):
    path = Path(__file__).resolve().parents[2] / relative_path
    lines = SourceScanner.from_file(path).read_lines()
    normalized = FixedFormProcessor(lines).normalize()
    tokens = Lexer(normalized).tokenize()
    return Parser(tokens).parse()


def test_matsum_nested_do_shared_label_renders_as_single_chain():
    tu = _parse_example("examples/arrays/matsum.f")
    outer_do = next(s for s in node_children(tu.program) if isinstance(s, DoStmt))
    outer_children = node_children(outer_do)
    assert len(outer_children) == 1
    inner_do = outer_children[0]
    assert isinstance(inner_do, DoStmt)
    assert len(node_children(inner_do)) == 2