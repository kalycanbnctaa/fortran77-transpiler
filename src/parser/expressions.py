from __future__ import annotations

from src.ast import (
    ArrayRef,
    BinaryOp,
    CharacterLiteral,
    Expr,
    Identifier,
    IntLiteral,
    LogicalLiteral,
    RealLiteral,
    UnaryOp,
)
from src.lexer.token_type import TokenType

from .base import ParseError
from .precedence import (
    ADDITIVE_OPERATORS,
    MULTIPLICATIVE_OPERATORS,
    RELATIONAL_OPERATORS,
)

class ExpressionParserMixin:
    def parse_expression(self) -> Expr:
        left = self.parse_and()
        while self._check(TokenType.OR):
            op = self._advance()
            right = self.parse_and()
            left = BinaryOp(operator=op.lexeme.upper(), left=left, right=right, line=left.line)
        return left

    def parse_and(self) -> Expr:
        left = self.parse_not()
        while self._check(TokenType.AND):
            op = self._advance()
            right = self.parse_not()
            left = BinaryOp(operator=op.lexeme.upper(), left=left, right=right, line=left.line)
        return left

    def parse_not(self) -> Expr:
        if self._check(TokenType.NOT):
            op = self._advance()
            operand = self.parse_not()
            return UnaryOp(operator=op.lexeme.upper(), operand=operand, line=op.line)
        return self.parse_relational()

    def parse_relational(self) -> Expr:
        left = self.parse_additive()
        if self._check(*RELATIONAL_OPERATORS):
            op = self._advance()
            right = self.parse_additive()
            return BinaryOp(operator=op.lexeme.upper(), left=left, right=right, line=left.line)
        return left

    def parse_additive(self) -> Expr:
        left = self.parse_multiplicative()
        while self._check(*ADDITIVE_OPERATORS):
            op = self._advance()
            right = self.parse_multiplicative()
            left = BinaryOp(operator=op.lexeme, left=left, right=right, line=left.line)
        return left

    def parse_multiplicative(self) -> Expr:
        left = self.parse_unary()
        while self._check(*MULTIPLICATIVE_OPERATORS):
            op = self._advance()
            right = self.parse_unary()
            left = BinaryOp(operator=op.lexeme, left=left, right=right, line=left.line)
        return left

    def parse_unary(self) -> Expr:
        if self._check(TokenType.PLUS, TokenType.MINUS):
            op = self._advance()
            operand = self.parse_unary()
            return UnaryOp(operator=op.lexeme, operand=operand, line=op.line)
        return self.parse_power()

    def parse_power(self) -> Expr:
        base = self.parse_primary()
        if self._match(TokenType.DSTAR):
            exponent = self.parse_unary()
            return BinaryOp(operator="**", left=base, right=exponent, line=base.line)
        return base

    def parse_primary(self) -> Expr:
        token = self._peek()

        if self._check(TokenType.INT_LITERAL):
            self._advance()
            return IntLiteral(value=int(token.lexeme), line=token.line)

        if self._check(TokenType.REAL_LITERAL):
            self._advance()
            return RealLiteral(value=float(token.lexeme), line=token.line)

        if self._check(TokenType.CHARACTER_LITERAL):
            self._advance()
            value = token.lexeme[1:-1]
            return CharacterLiteral(value=value, line=token.line)

        if self._check(TokenType.TRUE):
            self._advance()
            return LogicalLiteral(value=True, line=token.line)

        if self._check(TokenType.FALSE):
            self._advance()
            return LogicalLiteral(value=False, line=token.line)

        if self._check(TokenType.IDENTIFIER):
            return self.parse_identifier_expr()

        if self._check(TokenType.REAL) and self._peek(1).type == TokenType.LPAREN:
            return self.parse_real_intrinsic_call()

        if self._match(TokenType.LPAREN):
            expr = self.parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        raise ParseError("Expected an expression", token)

    def parse_real_intrinsic_call(self) -> Expr:
        token = self._expect(TokenType.REAL)
        self._expect(TokenType.LPAREN)
        args: list[Expr] = []
        if not self._check(TokenType.RPAREN):
            args.append(self.parse_expression())
            while self._match(TokenType.COMMA):
                args.append(self.parse_expression())
        self._expect(TokenType.RPAREN)
        return ArrayRef(name="REAL", indices=args, line=token.line)

    def parse_identifier_expr(self) -> Expr:
        token = self._expect(TokenType.IDENTIFIER)
        name = token.lexeme

        if self._match(TokenType.LPAREN):
            args: list[Expr] = []
            if not self._check(TokenType.RPAREN):
                args.append(self.parse_expression())
                while self._match(TokenType.COMMA):
                    args.append(self.parse_expression())
            self._expect(TokenType.RPAREN)
            return ArrayRef(name=name, indices=args, line=token.line)

        return Identifier(name=name, line=token.line)

    def parse_lvalue(self) -> Expr:
        if not self._check(TokenType.IDENTIFIER):
            raise ParseError("Expected an identifier", self._peek())
        return self.parse_identifier_expr()