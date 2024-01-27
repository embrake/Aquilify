from typing import Union, Literal
from .type import Type
from functools import wraps
from .constants import ConstantTypes

class Field(Type[str, str]):
    def __init__(self, *args: str | None, type: ConstantTypes = None, **kwargs):
        self.type = type
        self.args = args
        super().__init__(**kwargs)

    def sql_name(self) -> str:
        return f"{self.type}"

    def encode(self, decoded: str) -> str:
        return decoded

    def decode(self, encoded: str) -> str:
        return encoded

    def default_suggestion(self, encoded: str) -> str:
        return f"'{encoded}'"

    def default_declaration(self, decoded: str) -> str:
        return f"'{decoded}'"

    def default_encode(self, f):
        @wraps(f)
        def wrapper(decoded: str) -> Union[str, Literal["NULL"]]:
            if decoded is None:
                return "NULL"
            return f(decoded)

        return wrapper

    def encode(self, decoded: str) -> str:
        return decoded

    def decode(self, encoded: str) -> str:
        return encoded
