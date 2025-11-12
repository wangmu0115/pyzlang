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
    def __init__(self, type: TokenType, text: Optional[str] = None):
        self.__type = type
        self.__text = text or type.value

    @property
    def type(self):
        return self.__type

    @property
    def text(self):
        return self.__text

    def __repr__(self):
        return f"Token(type={self.type.name}, text='{self.text}')"

    def __str__(self):
        return f"{self.type.name}('{self.text}')"


BUILTIN_KEYWORDS = {tt.value: tt for tt in TokenType if tt.value[0] in ascii_letters}
BUILTIN_SYMBOLS = {tt.value: tt for tt in TokenType if tt.value[0] not in ascii_letters and not tt.value.startswith("____")}
