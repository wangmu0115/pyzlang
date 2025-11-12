from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from interpreter import Token, TokenType
from interpreter.ast import (
    BoolLiteralExpression,
    Expression,
    FloatLiteralExpression,
    IdenExpression,
    IntLiteralExpression,
    LiteralExpression,
    StrLiteralExpression,
)

if TYPE_CHECKING:
    from interpreter import Parser


class PrefixParselet(ABC):
    """Prefix parselet interface used by the Pratt parser."""

    @abstractmethod
    def parse(self, parser: "Parser", token: Token) -> Expression: ...


class InfixParselet(ABC):
    @abstractmethod
    def parse(self, parser: "Parser", left: Expression, token: Token) -> Expression: ...


def standard_prefix_parselets() -> dict[TokenType, PrefixParselet]:
    return {
        TokenType.IDENTIFIER: IdenParselet(),
        TokenType.NUMBER: LiteralParselet(),
        TokenType.STRING: LiteralParselet(),
        TokenType.TRUE: LiteralParselet(),
        TokenType.FALSE: LiteralParselet(),
    }


def standard_infix_parselets() -> dict[TokenType, InfixParselet]: ...


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
