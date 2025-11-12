from enum import IntEnum
from typing import Callable, Iterator, Optional, Type, Union

from _interpreter import Lexer, Token, TokenType
from _interpreter.ast import (
    AssignOpExpression,
    BinaryOpExpression,
    BlockStatement,
    BoolLiteralExpression,
    CallExpression,
    ConditionalExpression,
    Expression,
    ExprStatement,
    FloatLiteralExpression,
    FuncExpression,
    IdenExpression,
    IfExpression,
    IntLiteralExpression,
    LetStatement,
    LiteralExpression,
    PrefixOpExpression,
    Program,
    ReturnStatement,
    Statement,
    StrLiteralExpression,
)
from _interpreter.debug import Trace, parse_trace


class ParseletMissError(Exception): ...


class ParserError(Exception): ...


class Precedence(IntEnum):  # 语言优先级
    DEFAULT = 0
    ASSIGNMENT = 1  # =, +=, -=, *=, /=, |=, &=
    EQUALS = 2  # ==, !=
    LEGE = 3  # <, <=, >, >=
    ADDSUB = 4  # +, -
    MULDIV = 5  # *, /
    PREFIX = 6  # !, -
    CALL = 7  # callable(x)


def token_precedence(tk: Union[Token | TokenType]) -> Precedence:  # 运算符对应的优先级
    token_type = tk.type if isinstance(tk, Token) else tk
    match token_type:
        case TokenType.ASSIGN:
            return Precedence.ASSIGNMENT
        case TokenType.IADD | TokenType.ISUB | TokenType.IMUL | TokenType.IDIV:
            return Precedence.ASSIGNMENT
        case TokenType.IAND | TokenType.IOR:
            return Precedence.ASSIGNMENT
        case TokenType.EQ | TokenType.NEQ:
            return Precedence.EQUALS
        case TokenType.LT | TokenType.LE | TokenType.GT | TokenType.GE:
            return Precedence.LEGE
        case TokenType.ADD | TokenType.SUB:
            return Precedence.ADDSUB
        case TokenType.MUL | TokenType.DIV:
            return Precedence.MULDIV
        case TokenType.NOT | TokenType.SUB:
            return Precedence.PREFIX
        case TokenType.LPAREN:  # 调用对象运算符 `callable(*arguments)`
            return Precedence.CALL
        case _:
            return Precedence.DEFAULT


def check_endfile_token(token: Token) -> bool:
    return token is None or token.type == TokenType.EOF


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer

    def parse(self, debug: bool = False) -> Program:
        it = self.__init_parser(debug)
        program = Program()
        while not check_endfile_token(self.curr_token):
            stmt = self._parse_statement(it)
            if stmt is not None:  # not empty statment
                program.append(stmt)
            self.__next_token(it)  # 移动 curr_token 到下一条语句
        return program

    def _parse_statement(self, it: Iterator[Token]) -> Optional[Type[Statement]]:
        match self.curr_token.type:
            case TokenType.SEMICOLON:  # empty statement `;`
                return None
            case TokenType.LET:
                return self.__let_stmt_parselet(it)
            case TokenType.RETURN:
                return self.__return_stmt_parselet(it)
            case TokenType.LBRACE:
                return self.__block_stmt_parselet(it)
            case _:
                return self.__expr_stmt_parselet(it)

    @parse_trace("Expression")
    def _parse_expression(self, it: Iterator[Token], precedence: Precedence = Precedence.DEFAULT) -> Type[Expression]:
        if self.curr_token is None:
            raise ParserError("The expression token can not be none.")
        prefix_parselet = self.__prefix_parselet(self.curr_token)
        if prefix_parselet is None:
            raise ParseletMissError(f"Token `{self.curr_token}` parselet does not exist.")
        left = prefix_parselet(it)
        while self.peek_token is not None and precedence < token_precedence(self.peek_token):
            infix_parselet = self.__infix_parselet(self.peek_token)
            if infix_parselet is None:
                return left
            self.__next_token(it)  # move to operator
            left = infix_parselet(left, it)

        return left

    @parse_trace("Let Statement")
    def __let_stmt_parselet(self, it: Iterator[Token]) -> LetStatement:
        self.__next_token(it)  # move to start of expression
        assign_expr = self._parse_expression(it, Precedence.DEFAULT)
        if not isinstance(assign_expr, AssignOpExpression):
            raise ParserError("The let statement must assign value to variable.")
        if assign_expr.operator.type != TokenType.ASSIGN:
            raise ParserError("The let statement assign operater must be `=`.")
        self.__next_token(it)  # move to end of statement
        if self.curr_token is None or self.curr_token.type != TokenType.SEMICOLON:
            raise ParserError("The let statement must end with a semicolon.")
        return LetStatement(assign_expr)

    @parse_trace("Return Statement")
    def __return_stmt_parselet(self, it: Iterator[Token]) -> ReturnStatement:
        self.__next_token(it)  # move to start of expression
        value_expr = self._parse_expression(it)
        self.__next_token(it)  # move to end of statement
        if self.curr_token is None or self.curr_token.type != TokenType.SEMICOLON:
            raise ParserError("The return statement must end with a semicolon.")
        return ReturnStatement(value_expr)

    @parse_trace("Expression Statement")
    def __expr_stmt_parselet(self, it: Iterator[Token]) -> ExprStatement:
        expr = self._parse_expression(it)
        self.__next_token(it)  # move to end of statement
        if self.curr_token is None or self.curr_token.type != TokenType.SEMICOLON:
            raise ParserError("The expression statement must end with a semicolon.")

        return ExprStatement(expr)

    @parse_trace("Block Statement")
    def __block_stmt_parselet(self, it: Iterator[Token]) -> BlockStatement:  # {1+2;}
        self.__next_token(it)  # move to start of statement
        statements = []
        while not check_endfile_token(self.curr_token):
            if self.curr_token.type == TokenType.RBRACE:
                break
            stmt = self._parse_statement(it)
            if stmt is not None:
                statements.append(stmt)
            self.__next_token(it)  # move to next statement
        if self.curr_token is None or self.curr_token.type != TokenType.RBRACE:
            raise ParserError("The block statement must end with a right brace.")
        return BlockStatement(statements)

    @parse_trace("Identifier Expression")
    def __iden_expr_parselet(self, *args) -> IdenExpression:
        return IdenExpression(self.curr_token.literal)

    @parse_trace("Literal Expression")
    def __literal_expr_parselet(self, *args) -> Type[LiteralExpression]:
        literal = self.curr_token.literal
        match self.curr_token.type:
            case TokenType.STRING:
                return StrLiteralExpression(literal)
            case TokenType.TRUE:
                return BoolLiteralExpression(True)
            case TokenType.FALSE:
                return BoolLiteralExpression(False)
            case TokenType.NUMBER:
                try:
                    if "." in literal or "e" in literal or "E" in literal:
                        return FloatLiteralExpression(float(literal))
                    else:
                        if literal.startswith("0x") or literal.startswith("0X"):
                            base = 16
                        else:
                            base = 10
                        return IntLiteralExpression(int(literal, base))
                except ValueError as err:
                    raise ParserError(str(err))
            case _:
                raise ParserError(f"Unknown literal type: {self.curr_token!s}")

    @parse_trace("Prefix Operator Expression")
    def __prefix_op_expr_parselet(self, it: Iterator[Token], *args) -> PrefixOpExpression:
        operator = self.curr_token
        self.__next_token(it)
        operand = self._parse_expression(it, token_precedence(operator))
        return PrefixOpExpression(operator, operand)

    @parse_trace("Assign Operator Expression")
    def __assign_op_expr_parselet(self, left: Type[Expression], it: Iterator[Token], *args) -> AssignOpExpression:
        if not isinstance(left, IdenExpression):
            raise ParserError("The assign expression left operand must be identifier.")
        operator = self.curr_token
        precedence = token_precedence(operator)
        self.__next_token(it)
        right = self._parse_expression(it, precedence)
        return AssignOpExpression(left, operator, right)

    @parse_trace("Binary Operator Expression")
    def __binary_op_expr_parselet(self, left: Type[Expression], it: Iterator[Token], *args) -> BinaryOpExpression:  # 解析 `二元运算符表达式`
        operator = self.curr_token
        precedence = token_precedence(operator)
        self.__next_token(it)
        right = self._parse_expression(it, precedence)
        return BinaryOpExpression(left, operator, right)

    @parse_trace("Grouped Expression")
    def __parse_grouped_expression(self, it: Iterator[Token], *args) -> Type[Expression]:  # 解析 `分组()表达式`
        self.__next_token(it)  # 将 curr_token 移动到括号内的表达式
        expr = self._parse_expression(it, Precedence.DEFAULT)
        self.__next_token(it)  # 将 curr_token 移动到右括号`)`处
        if self.curr_token is None or self.curr_token.type != TokenType.RPAREN:
            raise ParserError("Grouped Expression must end with a right parenthesis(`)`).")
        return expr

    @parse_trace("Conditional Expression")
    def __conditional_expr_parselet(self, it: Iterator[Token], *args) -> ConditionalExpression:  # if (<条件表达式>) {<结果>} else {<可替代的结果>}
        if self.peek_token is None or self.peek_token.type != TokenType.LPAREN:
            raise ParserError("The `if` keyword must be followed by a conditional expression.")
        self.__next_token(it)
        self.__next_token(it)  # 将 curr_token 移动到`(`后面的表达式开头处
        cond_expr = self._parse_expression(it, Precedence.DEFAULT)
        self.__next_token(it)  # 将 curr_token 移动到右括号`)`处
        if self.curr_token is None or self.curr_token.type != TokenType.RPAREN:
            raise ParserError("The conditional expression in if statement must be enclosed in parentheses.")
        self.__next_token(it)  # 将 curr_token 移动到 <结果> 的块语句处
        conseq_stmt = self.__parse_block_statement(it)
        if self.peek_token is not None and self.peek_token.type == TokenType.ELSE:  # 是否存在else语句块
            self.__next_token(it)
            self.__next_token(it)  # 将 curr_token 移动到 <可替代的结果> 的块语句处
            return IfExpression(cond_expr, conseq_stmt, self.__parse_block_statement(it))
        return IfExpression(cond_expr, conseq_stmt)

    @parse_trace("Function Expression")
    def __parse_func_expression(self, it: Iterator[Token], *args) -> FuncExpression:  # fn(<参数列表>) {函数体}
        self.__next_token(it)  # 将 curr_token 移动到参数列表处
        params = self.__parse_func_params(it)
        self.__next_token(it)  # 将 curr_token 移动到函数体处
        body = self.__parse_block_statement(it)
        return FuncExpression(params, body)

    @parse_trace("Call Expression")
    def __parse_call_expression(self, callable: Type[Expression], it: Iterator[Token], *args) -> CallExpression:  # add(<实参列表>)
        return CallExpression(callable, self.__parse_call_arguments(it))

    @parse_trace("Function Parameters")
    def __parse_func_params(self, it: Iterator[Token]) -> list[IdenExpression]:  # (<参数列表>)
        if self.curr_token is None or self.peek_token is None or self.curr_token.type != TokenType.LPAREN:
            raise ParserError("Function parameters must be enclosed in parentheses.")
        parameters = []  # 参数列表
        self.__next_token(it)
        while self.curr_token is not None and self.curr_token.type != TokenType.RPAREN:
            if self.curr_token.type != TokenType.IDENTIFIER:
                raise ParserError("Function parameters can only be identifiers.")
            parameters.append(self.__parse_iden_expression())
            self.__next_token(it)  # curr_token 移动到 `,` 或 `)` 处
            if self.curr_token is None or self.curr_token.type == TokenType.RPAREN:
                break
            if self.curr_token.type != TokenType.COMMA:
                raise ParserError("Function parameters must split by comma.")
            self.__next_token(it)  # 跳过 `,`
        if self.curr_token is None or self.curr_token.type != TokenType.RPAREN:
            raise ParserError("Function parameters must be enclosed in parentheses.")
        return parameters

    @parse_trace("Callable Arguments")
    def __parse_call_arguments(self, it: Iterator[Token]) -> list[Expression]:  # (<实参列表>)
        if self.curr_token is None or self.peek_token is None or self.curr_token.type != TokenType.LPAREN:
            raise ParserError("Callable arguments must be enclosed in parentheses.")
        arguments = []  # 实参列表
        self.__next_token(it)
        while self.curr_token is not None and self.curr_token.type != TokenType.RPAREN:
            arguments.append(self._parse_expression(it, Precedence.DEFAULT))
            self.__next_token(it)  # 移动到 `,` 或 `)` 处
            if self.curr_token is None or self.curr_token.type == TokenType.RPAREN:
                break
            if self.curr_token.type != TokenType.COMMA:
                raise ParserError("Callable arguments must split by comma.")
            self.__next_token(it)  # 跳过 `,`

        if self.curr_token is None or self.curr_token.type != TokenType.RPAREN:
            raise ParserError("Callable arguments must be enclosed in parentheses.")

        return arguments

    def __prefix_parselet(self, tok: Union[Token | TokenType]) -> Optional[Callable]:
        token_type = tok.type if isinstance(tok, Token) else tok
        match token_type:
            case TokenType.IDENTIFIER:
                return self.__iden_expr_parselet
            case TokenType.NUMBER | TokenType.STRING | TokenType.TRUE | TokenType.FALSE:
                return self.__literal_expr_parselet
            case TokenType.ADD | TokenType.SUB | TokenType.NOT:  # 前缀运算符: -, +, !
                return self.__prefix_op_expr_parselet

            case TokenType.LPAREN:  # `(`
                return self.__parse_grouped_expression
            case TokenType.IF:
                return self.__conditional_expr_parselet
            case TokenType.FUNCTION:
                return self.__parse_func_expression
            case _:
                return None

    def __infix_parselet(self, tok: Union[Token | TokenType]) -> Optional[Callable]:
        token_type = tok.type if isinstance(tok, Token) else tok
        match token_type:
            case TokenType.ADD | TokenType.SUB | TokenType.MUL | TokenType.DIV:
                return self.__binary_op_expr_parselet
            case TokenType.LT | TokenType.LE | TokenType.GT | TokenType.GE | TokenType.EQ | TokenType.NEQ:
                return self.__binary_op_expr_parselet
            case TokenType.AND | TokenType.OR:
                return self.__binary_op_expr_parselet
            case TokenType.ASSIGN:
                return self.__assign_op_expr_parselet
            case TokenType.IADD | TokenType.ISUB | TokenType.IMUL | TokenType.IDIV:
                return self.__assign_op_expr_parselet
            case TokenType.IAND | TokenType.IOR:
                return self.__assign_op_expr_parselet

            case TokenType.LPAREN:
                return self.__parse_call_expression
            case _:
                return None

    def __init_parser(self, debug: bool) -> Iterator[Token]:
        self.debug = debug
        self.trace = Trace()
        it = iter(self.lexer)
        self.curr_token = next(it, None)
        self.peek_token = next(it, None)
        return it

    def __next_token(self, it: Iterator[Token]):
        self.curr_token = self.peek_token
        self.peek_token = next(it, None)
