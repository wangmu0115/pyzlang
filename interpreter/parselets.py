from abc import ABC, abstractmethod
from enum import IntEnum
from typing import TYPE_CHECKING

from interpreter import Token, TokenType
from interpreter.ast import (
    AssignExpression,
    BinaryOperatorExpression,
    BoolLiteralExpression,
    Expression,
    FloatLiteralExpression,
    IdenExpression,
    IntLiteralExpression,
    LiteralExpression,
    StrLiteralExpression,
    UnaryOperatorExpression,
)

if TYPE_CHECKING:
    from interpreter import Parser


class ParserError(Exception): ...


class Precedence(IntEnum):  # 语言优先级
    DEFAULT = -1
    ASSIGN_BELOW = 0  # assign is right-associative
    ASSIGN = 1  # =, +=, -=, *=, /=, |=, &=
    CONDITIONAL = 2  # ? :
    LOGICAL = 3  # &, |
    EQUALS = 4  # ==, !=
    LEGE = 5  # <, <=, >, >=
    ADDSUB = 6  # +, -
    MULDIV = 7  # *, /
    PREFIX = 8  # !, +, -
    CALL = 9  # callable(x)


class PrefixParselet(ABC):
    """Prefix parselet interface used by the Pratt parser."""

    @abstractmethod
    def parse(self, parser: "Parser", token: Token) -> Expression: ...


class InfixParselet(ABC):
    @abstractmethod
    def parse(self, parser: "Parser", left: Expression, token: Token) -> Expression: ...

    @property
    @abstractmethod
    def precedence(self) -> Precedence: ...


def standard_prefix_parselets() -> dict[TokenType, PrefixParselet]:
    return {
        TokenType.IDENTIFIER: IdenParselet(),
        TokenType.NUMBER: LiteralParselet(),
        TokenType.STRING: LiteralParselet(),
        TokenType.TRUE: LiteralParselet(),
        TokenType.FALSE: LiteralParselet(),
        TokenType.ADD: UnaryOperatorParselet(),
        TokenType.SUB: UnaryOperatorParselet(),
        TokenType.NOT: UnaryOperatorParselet(),
        TokenType.LPAREN: GroupParselet(),
    }


def standard_infix_parselets() -> dict[TokenType, InfixParselet]:
    return {
        # binary operators
        TokenType.ADD: BinaryOperatorParselet(Precedence.ADDSUB),
        TokenType.SUB: BinaryOperatorParselet(Precedence.ADDSUB),
        TokenType.MUL: BinaryOperatorParselet(Precedence.MULDIV),
        TokenType.DIV: BinaryOperatorParselet(Precedence.MULDIV),
        TokenType.LT: BinaryOperatorParselet(Precedence.LEGE),
        TokenType.LE: BinaryOperatorParselet(Precedence.LEGE),
        TokenType.GT: BinaryOperatorParselet(Precedence.LEGE),
        TokenType.GE: BinaryOperatorParselet(Precedence.LEGE),
        TokenType.EQ: BinaryOperatorParselet(Precedence.EQUALS),
        TokenType.NEQ: BinaryOperatorParselet(Precedence.EQUALS),
        TokenType.AND: BinaryOperatorParselet(Precedence.LOGICAL),
        TokenType.OR: BinaryOperatorParselet(Precedence.LOGICAL),
        # assignment
        TokenType.ASSIGN: AssignParselet(),
        TokenType.IADD: AssignParselet(),
        TokenType.ISUB: AssignParselet(),
        TokenType.IMUL: AssignParselet(),
        TokenType.IDIV: AssignParselet(),
        TokenType.IAND: AssignParselet(),
        TokenType.IOR: AssignParselet(),
    }


class IdenParselet(PrefixParselet):
    """Simple parselet for identifier like "foo"."""

    def parse(self, parser: "Parser", token: Token) -> IdenExpression:
        return IdenExpression(token.text)


class LiteralParselet(PrefixParselet):
    """Simple parselet for int/float/boolean/str literal."""

    def parse(self, parser: "Parser", token: Token) -> LiteralExpression:
        match token.type:
            case TokenType.STRING:
                return StrLiteralExpression(token.text)
            case TokenType.TRUE:
                return BoolLiteralExpression(True)
            case TokenType.FALSE:
                return BoolLiteralExpression(False)
            case TokenType.NUMBER:
                number_txt = token.text
                if "." in number_txt or "e" in number_txt or "E" in number_txt:
                    return FloatLiteralExpression(float(number_txt))
                elif number_txt.startswith("0x") or number_txt.startswith("0X"):
                    return IntLiteralExpression(int(number_txt, 16))
                else:
                    return IntLiteralExpression(int(number_txt, 10))
            case _:
                raise NotImplementedError()


class UnaryOperatorParselet(PrefixParselet):
    """Generic prefix parselet for a unary arithmetic operator.
    Unary operators: +, -, !
    """

    def parse(self, parser: "Parser", token: Token) -> UnaryOperatorExpression:
        parser.consume_next()  # move to the beginning of right operand
        right = parser.parse_expression(Precedence.PREFIX)
        return UnaryOperatorExpression(token, right)


class GroupParselet(PrefixParselet):
    """Prase parentheses used to group an expression. like "5 * (2 + 3)"."""

    def parse(self, parser: "Parser", token: Token) -> Expression:
        parser.consume_next()  # move to the beginning of expression in parentheses.
        expr = parser.parse_expression(Precedence.DEFAULT)  # ( {} )
        parser.consume_next()  # move to right parenthese
        if parser.curr_token.text != TokenType.RPAREN:
            raise ParserError("The grouped expression must end with a right parenthese.")
        return expr


class BinaryOperatorParselet(InfixParselet):
    """Generic infix parselet for a binary arithmetic operator.
    Binary operators: +, -, *, /, >, >=, <, <=, ==, !=, &, |
    """

    def __init__(self, precedence: Precedence):
        self.__precedence = precedence

    def parse(self, parser: "Parser", left: Expression, token: Token) -> BinaryOperatorExpression:
        parser.consume_next()  # move to the beginning of right operand
        right = parser.parse_expression(self.precedence)
        return BinaryOperatorExpression(left, token, right)

    @property
    def precedence(self) -> Precedence:
        return self.__precedence


class AssignParselet(InfixParselet):
    """Infix parselet for assignment expressions like "foo=bar".
    Assign operators: =, +=, -=, *=, /=, &=, |=.
    The left side of an assignment must be a simple identifier, like "a",
    assignment expressions are right-associative, "a = b = c" is parsed as "a = (b = c)".
    """

    def parse(self, parser: "Parser", left: Expression, token: Token) -> AssignExpression:
        if not isinstance(left, IdenExpression):
            raise ParserError(f"The left side of an assignment must be a simple identifier, but get: {self.left!r}.")
        parser.consume_next()  # move to the beginning of right side
        right = parser.parse_expression(Precedence.ASSIGN_BELOW)
        return AssignExpression(left.iden, token, right)

    @property
    def precedence(self) -> Precedence:
        return Precedence.ASSIGN
