from __future__ import annotations

from typing import Any

from .declarations import ArrayDecl, CommonDecl, ImplicitNoneDecl, TypeDecl
from .expressions import (
    ArrayRef,
    BinaryOp,
    FunctionCall,
    Identifier,
    IntLiteral,
    LogicalLiteral,
    RealLiteral,
    UnaryOp,
)
from .program import Function, Program, Subroutine, TranslationUnit
from .statements import (
    Assignment,
    CallStmt,
    ContinueStmt,
    DoStmt,
    GotoStmt,
    IfStmt,
    PrintStmt,
    ReadStmt,
    ReturnStmt,
    StopStmt,
)


class Visitor:
    def generic_visit(self, node: Any) -> Any:
        raise NotImplementedError(
            f"No visit_{type(node).__name__} method defined on {type(self).__name__}"
        )

    def visit_TranslationUnit(self, node: TranslationUnit) -> Any:
        return self.generic_visit(node)

    def visit_Program(self, node: Program) -> Any:
        return self.generic_visit(node)

    def visit_Subroutine(self, node: Subroutine) -> Any:
        return self.generic_visit(node)

    def visit_Function(self, node: Function) -> Any:
        return self.generic_visit(node)

    def visit_TypeDecl(self, node: TypeDecl) -> Any:
        return self.generic_visit(node)

    def visit_ArrayDecl(self, node: ArrayDecl) -> Any:
        return self.generic_visit(node)

    def visit_ImplicitNoneDecl(self, node: ImplicitNoneDecl) -> Any:
        return self.generic_visit(node)

    def visit_CommonDecl(self, node: CommonDecl) -> Any:
        return self.generic_visit(node)

    def visit_Assignment(self, node: Assignment) -> Any:
        return self.generic_visit(node)

    def visit_IfStmt(self, node: IfStmt) -> Any:
        return self.generic_visit(node)

    def visit_DoStmt(self, node: DoStmt) -> Any:
        return self.generic_visit(node)

    def visit_GotoStmt(self, node: GotoStmt) -> Any:
        return self.generic_visit(node)

    def visit_ContinueStmt(self, node: ContinueStmt) -> Any:
        return self.generic_visit(node)

    def visit_CallStmt(self, node: CallStmt) -> Any:
        return self.generic_visit(node)

    def visit_PrintStmt(self, node: PrintStmt) -> Any:
        return self.generic_visit(node)

    def visit_ReadStmt(self, node: ReadStmt) -> Any:
        return self.generic_visit(node)

    def visit_StopStmt(self, node: StopStmt) -> Any:
        return self.generic_visit(node)

    def visit_ReturnStmt(self, node: ReturnStmt) -> Any:
        return self.generic_visit(node)

    def visit_IntLiteral(self, node: IntLiteral) -> Any:
        return self.generic_visit(node)

    def visit_RealLiteral(self, node: RealLiteral) -> Any:
        return self.generic_visit(node)

    def visit_LogicalLiteral(self, node: LogicalLiteral) -> Any:
        return self.generic_visit(node)

    def visit_Identifier(self, node: Identifier) -> Any:
        return self.generic_visit(node)

    def visit_ArrayRef(self, node: ArrayRef) -> Any:
        return self.generic_visit(node)

    def visit_FunctionCall(self, node: FunctionCall) -> Any:
        return self.generic_visit(node)

    def visit_BinaryOp(self, node: BinaryOp) -> Any:
        return self.generic_visit(node)

    def visit_UnaryOp(self, node: UnaryOp) -> Any:
        return self.generic_visit(node)