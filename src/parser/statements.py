from __future__ import annotations

from src.ast import (
    Assignment,
    CallStmt,
    ComputedGotoStmt,
    ContinueStmt,
    DoStmt,
    Expr,
    GotoStmt,
    IfStmt,
    PrintStmt,
    ReadStmt,
    ReturnStmt,
    Stmt,
    StopStmt,
)
from src.lexer.token_type import TokenType

from .base import ParseError

_STATEMENT_STARTERS = (
    TokenType.IF,
    TokenType.DO,
    TokenType.GOTO,
    TokenType.CONTINUE,
    TokenType.CALL,
    TokenType.PRINT,
    TokenType.READ,
    TokenType.STOP,
    TokenType.RETURN,
    TokenType.IDENTIFIER,
)

class StatementParserMixin:
    def parse_statement_list(
        self, stop_tokens: frozenset[TokenType], end_label: int | None = None
    ) -> list[Stmt]:
        statements: list[Stmt] = []
        while not self._check(*stop_tokens) and not self._at_end():
            stmt = self.parse_statement()
            statements.append(stmt)
            if end_label is not None and self._terminal_label(stmt) == end_label:
                return statements
        if end_label is not None:
            raise ParseError(f"DO loop has no statement labeled {end_label}", self._peek())
        return statements

    @staticmethod
    def _terminal_label(stmt: Stmt) -> int | None:
        if isinstance(stmt, DoStmt):
            return stmt.end_label
        return stmt.label

    def parse_statement(self) -> Stmt:
        label: int | None = None
        if self._check(TokenType.LABEL):
            label = int(self._advance().lexeme)

        if not self._check(*_STATEMENT_STARTERS):
            raise ParseError("Expected a statement", self._peek())

        stmt = self._parse_statement_body()
        stmt.label = label
        return stmt

    def _parse_statement_body(self) -> Stmt:
        if self._check(TokenType.IF):
            return self.parse_if()
        if self._check(TokenType.DO):
            return self.parse_do()
        if self._check(TokenType.GOTO):
            if self._peek(1).type == TokenType.LPAREN:
                return self.parse_computed_goto()
            else:
                return self.parse_goto()
        if self._check(TokenType.CONTINUE):
            token = self._advance()
            return ContinueStmt(line=token.line)
        if self._check(TokenType.CALL):
            return self.parse_call()
        if self._check(TokenType.PRINT):
            return self.parse_print()
        if self._check(TokenType.READ):
            return self.parse_read()
        if self._check(TokenType.STOP):
            token = self._advance()
            return StopStmt(line=token.line)
        if self._check(TokenType.RETURN):
            token = self._advance()
            return ReturnStmt(line=token.line)
        if self._check(TokenType.IDENTIFIER):
            return self.parse_assignment()
        raise ParseError("Expected a statement", self._peek())

    def parse_assignment(self) -> Assignment:
        target = self.parse_lvalue()
        self._expect(TokenType.ASSIGN)
        value = self.parse_expression()
        return Assignment(target=target, value=value, line=target.line)

    def parse_if(self) -> IfStmt:
        token = self._expect(TokenType.IF)
        self._expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.THEN)

        then_body = self.parse_statement_list(frozenset({TokenType.ELSE, TokenType.ENDIF}))

        else_body: list[Stmt] = []
        if self._match(TokenType.ELSE):
            else_body = self.parse_statement_list(frozenset({TokenType.ENDIF}))

        self._expect(TokenType.ENDIF)
        return IfStmt(condition=condition, then_body=then_body, else_body=else_body, line=token.line)

    def parse_do(self) -> DoStmt:
        token = self._expect(TokenType.DO)
        end_label = int(self._expect(TokenType.INT_LITERAL).lexeme)
        loop_var = self._expect(TokenType.IDENTIFIER).lexeme
        self._expect(TokenType.ASSIGN)
        start = self.parse_expression()
        self._expect(TokenType.COMMA)
        end = self.parse_expression()

        step: Expr | None = None
        if self._match(TokenType.COMMA):
            step = self.parse_expression()

        body = self.parse_statement_list(frozenset({TokenType.END}), end_label=end_label)

        return DoStmt(
            loop_var=loop_var,
            start=start,
            end=end,
            step=step,
            end_label=end_label,
            body=body,
            line=token.line,
        )

    def parse_goto(self) -> GotoStmt:
        token = self._expect(TokenType.GOTO)
        target = int(self._expect(TokenType.INT_LITERAL).lexeme)
        return GotoStmt(target_label=target, line=token.line)

    def parse_computed_goto(self) -> ComputedGotoStmt:
        token = self._expect(TokenType.GOTO)
        self._expect(TokenType.LPAREN)
        labels = [int(self._expect(TokenType.INT_LITERAL).lexeme)]
        while self._match(TokenType.COMMA):
            labels.append(int(self._expect(TokenType.INT_LITERAL).lexeme))
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.COMMA)
        selector = self.parse_expression()
        return ComputedGotoStmt(labels=labels, selector=selector, line=token.line)

    def parse_call(self) -> CallStmt:
        token = self._expect(TokenType.CALL)
        name = self._expect(TokenType.IDENTIFIER).lexeme
        args: list[Expr] = []
        if self._match(TokenType.LPAREN):
            if not self._check(TokenType.RPAREN):
                args.append(self.parse_expression())
                while self._match(TokenType.COMMA):
                    args.append(self.parse_expression())
            self._expect(TokenType.RPAREN)
        return CallStmt(name=name, args=args, line=token.line)

    def parse_print(self) -> PrintStmt:
        token = self._expect(TokenType.PRINT)
        self._expect(TokenType.STAR)
        items: list[Expr] = []
        if self._match(TokenType.COMMA):
            items.append(self.parse_expression())
            while self._match(TokenType.COMMA):
                items.append(self.parse_expression())
        return PrintStmt(items=items, line=token.line)

    def parse_read(self) -> ReadStmt:
        token = self._expect(TokenType.READ)
        self._expect(TokenType.STAR)
        targets: list[Expr] = []
        if self._match(TokenType.COMMA):
            targets.append(self.parse_lvalue())
            while self._match(TokenType.COMMA):
                targets.append(self.parse_lvalue())
        return ReadStmt(targets=targets, line=token.line)