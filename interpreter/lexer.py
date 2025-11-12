from string import ascii_letters

from interpreter import BUILTIN_KEYWORDS, BUILTIN_SYMBOLS, Token, TokenType


class LexerError(Exception): ...


class Lexer:
    def __init__(self, input: str):
        self.input = input

    def __iter__(self):
        position = 0  # pointer to the position of the input string
        while position < len(self.input):
            ch = self.input[position]
            match ch:
                case " " | "\r" | "\n" | "\t":  # skip whitespace
                    ...
                case '"':
                    literal = _read_string(self.input, position)
                    position += len(literal) + 1
                    yield Token(TokenType.STRING, literal)
                case "=" | "!" | "<" | ">" | "+" | "-" | "*" | "/" | "&" | "|":
                    operator = _read_operator(self.input, position)
                    position += len(operator) - 1
                    yield Token(BUILTIN_SYMBOLS[operator])
                case "," | ";" | "(" | ")" | "{" | "}" | "[" | "]":
                    yield Token(BUILTIN_SYMBOLS[ch])
                case _:
                    if _is_letter(ch):  # identifier
                        iden = _read_iden(self.input, position)
                        position += len(iden) - 1
                        yield Token(BUILTIN_KEYWORDS.get(iden, TokenType.IDENTIFIER), iden)
                    elif _is_digit(ch):  # numbers
                        number = _read_number(self.input, position)
                        position += len(number) - 1
                        yield Token(TokenType.NUMBER, number)
                    else:
                        raise LexerError(f"Unknown illegal characters: {ch}")
            position += 1
        yield Token(TokenType.EOF)


def _read_string(seq: str, start_position: int) -> str:  # "<字符序列>"
    end_position = start_position + 1
    while end_position < len(seq) and seq[end_position] != '"':
        end_position += 1
    if end_position == len(seq):
        raise LexerError("The string must be enclosed in double quotes.")
    return seq[start_position + 1 : end_position]


def _read_operator(seq: str, position: int) -> str:  # 运算符: >, >=, ...
    if position >= len(seq) - 1:
        return seq[position]
    if seq[position + 1] == "=":
        return seq[position : position + 2]
    else:
        return seq[position]


def _read_iden(seq: str, start_position: int) -> str:  # 标识符: _abc, abc, abc_1, abc123, ...
    end_position = start_position + 1
    while end_position < len(seq):
        ch = seq[end_position]
        if _is_letter(ch) or _is_digit(ch):
            end_position += 1
        else:
            break
    return seq[start_position:end_position]


def _read_number(seq: str, start_position: int) -> str:  # 整数: 42, 0x12AB ；浮点数: 0.1, 1e+7, 1e-7, 2.3e7
    hex = __is_hex(seq, start_position)  # 十六进制
    if hex:
        end_position = start_position + 2
        while end_position < len(seq) and seq[end_position] in "0123456789abcdefABCDEF":
            end_position += 1
        return seq[start_position:end_position]
    else:
        cnt_point = 0  # 小数点 <= 1
        cnt_e = 0  # 1e-8, 1e6
        end_position = start_position + 1
        while end_position < len(seq):
            ch = seq[end_position]
            match ch:
                case "." | "e" | "E":
                    cnt_point, cnt_e = __check_float(ch, cnt_point, cnt_e)
                    end_position += 1
                case "-" | "+":
                    if seq[end_position - 1] == "e" or seq[end_position - 1] == "E":
                        end_position += 1
                    else:
                        break
                case _:
                    if _is_digit(ch):
                        end_position += 1
                    else:
                        break
        return seq[start_position:end_position]


def _is_letter(ch: str) -> bool:
    return ch == "_" or ch in ascii_letters


def _is_digit(ch: str) -> bool:
    return ch in list("0123456789")


def __is_hex(seq: str, position: int):
    if position >= len(seq) - 1:
        return False
    elif seq[position] != "0":
        return False
    else:
        return seq[position + 1] == "x" or seq[position + 1] == "X"


def __check_float(ch: str, cnt_point, cnt_e) -> tuple[int, int]:
    if ch == ".":
        if cnt_point >= 1:
            raise LexerError("The decimal point(`.`) can only appear once.")
        return 1, cnt_e
    elif ch == "e" or ch == "E":
        if cnt_e >= 1:
            raise LexerError("The decimal point(`e`) can only appear once.")
        return cnt_point, 1
    else:
        return cnt_point, cnt_e
