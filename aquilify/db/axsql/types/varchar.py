from typing import Optional, Union, Literal
from .type import Type
from functools import wraps

class VarcharField(Type[str, str]):
    def __init__(self, max_length: Optional[int] = 255, **kwargs):
        self.max_length = max_length
        super().__init__(**kwargs)
        
    @classmethod
    def construct_type(cls, max_length: int) -> str:
        return f"VARCHAR({max_length})"

    def sql_name(self) -> str:
        length_declaration = VarcharField.construct_type(self.max_length) if self.max_length else ""
        return f"{length_declaration}"

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
