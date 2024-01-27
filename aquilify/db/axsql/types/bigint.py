"""
The module containing logic for bigint types.
"""

from .type import Type
from typing import ClassVar


class BigintField(Type[int, bool]):
    DEFAULT_MIN_VALUE: ClassVar[int] = -9223372036854775808  
    DEFAULT_MAX_VALUE: ClassVar[int] = 9223372036854775807 
    
    def __init__(self, min_value: int = DEFAULT_MIN_VALUE, max_value: int = DEFAULT_MAX_VALUE, **kwargs) -> None:
        self._validate_integer(min_value, "min_value")
        self._validate_integer(max_value, "max_value")
        self._validate_min_max_values(min_value, max_value)
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def sql_name(self) -> str:
        return "BIGINT"

    def decode(self, encoded: int) -> bool:
        return bool(encoded)

    def encode(self, decoded: bool) -> int:
        return 1 if decoded else 0

    def default_suggestion(self, encoded: int) -> str:
        return str(bool(encoded))

    def default_declaration(self, decoded: bool) -> str:
        return super().default_declaration(decoded)
    
    @staticmethod
    def _validate_integer(value: int, field_name: str) -> None:
        if not isinstance(value, int):
            raise TypeError(f"{field_name.capitalize()} should be an integer.")

    @staticmethod
    def _validate_min_max_values(min_value: int, max_value: int) -> None:
        if min_value >= max_value:
            raise ValueError("Minimum value should be less than maximum value.")

