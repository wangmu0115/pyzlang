from typing import TYPE_CHECKING

from _import_utils import import_attr

if TYPE_CHECKING:
    from tokens import BUILTIN_KEYWORDS, BUILTIN_SYMBOLS, Token, TokenType

__all__ = [
    "BUILTIN_KEYWORDS",
    "BUILTIN_SYMBOLS",
    "Token",
    "TokenType",
]

_dynamic_imports = {
    "BUILTIN_KEYWORDS": "tokens",
    "BUILTIN_SYMBOLS": "tokens",
    "Token": "tokens",
    "TokenType": "tokens",
}


def __getattr__(attr_name: str) -> object:
    module_name = _dynamic_imports.get(attr_name)
    result = import_attr(attr_name, module_name, __spec__.parent)
    globals()[attr_name] = result
    return result


def __dir__() -> list[str]:
    return __all__
