from typing import Generic, Optional, TypeVar


class Node:  # AST 节点，分为语句和表达式
    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(f'{attr[0]}={repr(attr[1])}' for attr in self.__dict__.items())})"


class Statement(Node): ...  # 语句


class Expression(Node): ...  # 表达式


class Program:  # 程序由语句组成
    def __init__(self, stmts: Optional[list[Statement]] = None):
        self.stmts = stmts or []

    def append(self, stmt: Statement):
        self.stmts.append(stmt)

    def __len__(self):
        return len(self.stmts)

    def __iter__(self):
        yield from self.stmts

    def __repr__(self):
        return f"Program(stmts={self.stmts!r})"

    def __str__(self):
        return "\n".join(str(stmt) for stmt in self.stmts)


class ExprStatement(Statement):  # 表达式语句: `<表达式>;`
    def __init__(self, expr: Expression):
        self.expr = expr

    def __str__(self):
        return f"{self.expr!s};"


class IdenExpression(Expression):  # 标识符表达式
    def __init__(self, iden: str):
        self.iden = iden

    def __str__(self):
        return self.iden


LiteralType = TypeVar("LiteralType", int, float, bool, str)


class LiteralExpression(Expression, Generic[LiteralType]):
    def __init__(self, literal: LiteralType):
        self.literal = literal

    def __str__(self):
        return str(self.literal)


class IntLiteralExpression(LiteralExpression[int]): ...


class FloatLiteralExpression(LiteralExpression[float]): ...


class BoolLiteralExpression(LiteralExpression[bool]): ...


class StrLiteralExpression(LiteralExpression[str]): ...
