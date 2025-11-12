from __future__ import annotations

from interpreter import Lexer, TokenType
from interpreter.ast import (
    Expression,
    ExprStatement,
    Program,
    Statement,
)
from interpreter.parselets import (
    InfixParselet,
    PrefixParselet,
    standard_infix_parselets,
    standard_prefix_parselets,
)


class ParserError(Exception): ...


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.prefix_parselets = standard_prefix_parselets()
        self.infix_parselets = standard_infix_parselets()

    def register_parselet(self, token_type: TokenType, parselet: PrefixParselet | InfixParselet):
        if isinstance(parselet, PrefixParselet):
            self.prefix_parselets[token_type] = parselet
        elif isinstance(parselet, InfixParselet):
            self.infix_parselets[token_type] = parselet
        else:
            raise NotImplementedError()

    def parse(self, debug: bool = False) -> Program:
        self.__init_parser(debug)
        program = Program()

        while self.curr_token is not None and self.curr_token.type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt is not None:
                program.append(stmt)
            self.__consume_next()  # move `curr_token` to next statement
        return program

    def parse_statement(self) -> Statement:
        match self.curr_token.type:
            case TokenType.SEMICOLON:  # empty statement `;`
                return None
            # case TokenType.LET:
            #     return self.__let_stmt_parselet(it)
            # case TokenType.RETURN:
            #     return self.__return_stmt_parselet(it)
            # case TokenType.LBRACE:
            #     return self.__block_stmt_parselet(it)
            case _:
                return self._parse_expr_stmt()

    def parse_expression(self) -> Expression:
        prefix = self.prefix_parselets.get(self.curr_token.type, None)
        if prefix is None:
            raise ParserError(f"Could not parse {self.curr_token}")
        return prefix.parse(self, self.curr_token)

    def _parse_expr_stmt(self) -> ExprStatement:
        expr = self.parse_expression()

        self.__end_statement()  # move to end of statement
        return ExprStatement(expr)

    def __init_parser(self, debug):
        self.tokens = iter(self.lexer)
        self.curr_token = next(self.tokens, None)
        self.peek_token = next(self.tokens, None)

    def __consume_next(self):
        self.curr_token = self.peek_token
        self.peek_token = next(self.tokens, None)

    def __end_statement(self, expected: TokenType = TokenType.SEMICOLON):
        self.__consume_next()
        if self.curr_token is None or self.curr_token.type != expected:
            raise ParserError(f"Statement must end with `{expected.value}`.")
