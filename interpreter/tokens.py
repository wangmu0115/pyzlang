from enum import StrEnum
from string import ascii_letters
from typing import Optional


class TokenType(StrEnum):
    ILLEGAL = "____ILLEGAL____"  # unsupported token
    EOF = "____EOF____"  # End Of File

    IDENTIFIER = "____IDEN____"  # 标识符
    NUMBER = "____NUMBER____"
    STRING = "____STRING____"

    ASSIGN = "="  # 运算符
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    IADD = "+="
    ISUB = "-="
    IMUL = "*="
    IDIV = "/="

    NOT = "!"
    AND = "&"
    OR = "|"
    IAND = "&="
    IOR = "|="

    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    EQ = "=="
    NEQ = "!="

    COMMA = ","
    SEMICOLON = ";"

    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"

    TRUE = "true"  # Boolean
    FALSE = "false"

    LET = "let"
    RETURN = "return"
    FUNCTION = "fn"
    IF = "if"
    ELSE = "else"


class Token:
    def __init__(self, type: TokenType, literal: Optional[str] = None):
        self.__type = type
        self.__literal = literal or type.value

    @property
    def type(self):
        return self.__type

    @property
    def literal(self):
        return self.__literal

    def __repr__(self):
        return f"Token(type={self.type.name}, literal='{self.literal}')"

    def __str__(self):
        return f"{self.type.name}('{self.literal}')"


BUILTIN_KEYWORDS = {tt.value: tt for tt in TokenType if tt.value[0] in ascii_letters}
BUILTIN_SYMBOLS = {tt.value: tt for tt in TokenType if tt.value[0] not in ascii_letters and not tt.value.startswith("____")}
