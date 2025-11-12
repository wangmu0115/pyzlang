from __future__ import annotations

from typing import Generic, Optional, Type, TypeVar

from _interpreter import Token


class Node: ...  # AST 节点，分为语句和表达式


class Statement(Node): ...  # 语句


class Expression(Node): ...  # 表达式


class Program:
    def __init__(self, statements: Optional[list[Type[Statement]]] = None):
        self.__statements = statements or []

    def append(self, statement: Type[Statement]):
        self.__statements.append(statement)

    @property
    def stmts(self):
        return self.statements

    @property
    def statements(self):
        return self.__statements

    def __repr__(self):
        return f"Program(statements={self.statements!r})"

    def __str__(self):
        return "\n".join(str(stmt) for stmt in self.statements)


class IdenExpression(Expression):  # 标识符表达式
    def __init__(self, iden: str):
        self.iden = iden

    def __repr__(self):
        return f"IdenExpression(iden={self.iden!r})"

    def __str__(self):
        return f"{self.iden}"


LiteralType = TypeVar("LiteralType", int, float, bool, str)


class LiteralExpression(Expression, Generic[LiteralType]):
    def __init__(self, literal: LiteralType):
        self.literal = literal

    def __repr__(self):
        return f"{self.__class__.__name__}(literal={self.literal!r})"

    def __str__(self):
        return f"{str(self.literal)}"


class IntLiteralExpression(LiteralExpression[int]): ...


class FloatLiteralExpression(LiteralExpression[float]): ...


class BoolLiteralExpression(LiteralExpression[bool]): ...


class StrLiteralExpression(LiteralExpression[str]): ...


class PrefixOpExpression(Expression):  # 前缀运算符表达式: -1, +1, !True
    def __init__(self, operator: Token, right: Type[Expression]):
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"{self.__class__.__name__}(operator={self.operator!r}, right={self.right!r})"

    def __str__(self):
        return f"({self.operator.literal}{str(self.right)})"


class BinaryOpExpression(Expression):  # 二元运算符表达式: 1+2, 1/100, 10 > 2, ...
    def __init__(self, left: Type[Expression], operator: Token, right: Type[Expression]):
        self.operator = operator
        self.left = left
        self.right = right

    def __repr__(self):
        return f"{self.__class__.__name__}(left={self.left!r}, operator={self.operator!r}, right={self.right!r})"

    def __str__(self):
        return f"({str(self.left)} {self.operator.literal} {str(self.right)})"


class AssignOpExpression(Expression):  # 赋值表达式: a=b, a+=b
    def __init__(self, iden: IdenExpression, operator: Token, right: Type[Expression]):
        self.iden = iden
        self.operator = operator
        self.right = right

    def __repr__(self):
        return f"{self.__class__.__name__}(iden={self.iden!r}, operator={self.operator!r}, right={self.right!r})"

    def __str__(self):
        return f"({self.iden.iden} {self.operator.literal} {self.right!s})"


class ConditionalExpression(Expression):
    def __init__(self, condition: Expression, then_arm: BlockStatement, else_arm: Optional[BlockStatement] = None):
        self.condition = condition
        self.then_arm = then_arm
        self.else_arm = else_arm

    def __repr__(self):
        return f"{self.__class__.__name__}(condition={self.condition!r}, then_arm={self.then_arm!r}, else_arm={self.else_arm!r})"

    def __str__(self):
        expr_str = f"if{self.condition}{self.then_arm}"
        if self.else_arm is not None:
            expr_str += f"else{self.else_arm}"
        return expr_str


class FuncExpression(Expression):
    """函数表达式: fn <参数列表> <块语句>"""

    def __init__(self, parameters: list[IdenExpression], body: BlockStatement):
        self.__parameters = list(parameters)
        self.__body = body

    @property
    def params(self) -> list[IdenExpression]:
        return self.paramters

    @property
    def paramters(self) -> list[IdenExpression]:
        return self.__parameters

    @property
    def body(self) -> BlockStatement:
        return self.__body

    def __repr__(self):
        return f"FuncExpression(parameters={self.paramters!r}, body={self.body!r})"

    def __str__(self):
        params = ", ".join(str(p) for p in self.params)
        return f"fn({params}){self.body}"


class CallExpression(Expression):
    def __init__(self, callable: Expression, arguments: list[Expression]):
        self.__callable = callable
        self.__arguments = arguments

    @property
    def callable(self):
        return self.__callable

    @property
    def args(self):
        return self.arguments

    @property
    def arguments(self):
        return self.__arguments

    def __repr__(self):
        return f"CallExpression(callable={self.callable!r}, arguments={self.arguments!r})"

    def __str__(self):
        return f"{self.callable}({', '.join(str(arg) for arg in self.arguments)})"


class LetStatement(Statement):  # 声明语句: `let <赋值表达式>;`
    def __init__(self, assign: AssignOpExpression):
        self.assign = assign

    def __repr__(self):
        return f"{self.__class__.__name__}(assign={self.assign!r})"

    def __str__(self):
        return f"let {self.assign!s};"


class ReturnStatement(Statement):  # 返回值语句: `return <表达式>;`
    def __init__(self, value: Type[Expression]):
        self.value = value

    def __repr__(self):
        return f"{self.__class__.__name__}(value={self.value!r})"

    def __str__(self):
        return f"return {self.value!s};"


class ExprStatement(Statement):  # 表达式语句: `<表达式>;`
    def __init__(self, expr: Type[Expression]):
        self.expr = expr

    def __repr__(self):
        return f"{self.__class__.__name__}(expr={self.expr!r})"

    def __str__(self):
        return f"{self.expr!s};"


class BlockStatement(Statement):  # 块语句: `{<语句>, <语句>, ...}`
    def __init__(self, statements: Optional[list[Type[Statement]]] = None):
        self.statements = statements or []

    def append(self, statement: Type[Statement]):
        self.statements.append(statement)

    def __len__(self):
        return len(self.statements)

    def __repr__(self):
        return f"BlockStatment(statements={self.statements!r})"

    def __str__(self):
        return "{ " + " ".join(str(stmt) for stmt in self.statements) + " }"
