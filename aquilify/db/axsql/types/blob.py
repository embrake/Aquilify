"""
The module containing logic for BLOB types.
"""

from .type import Type
from typing import ClassVar

class BlobField(Type[str, bytes]):
    DEFAULT_MAX_LENGTH: ClassVar[int] = 16777216 
    
    """
    Large-Binary-Object-Type - Converts between SQLite BLOB and Python bytes.
    """
    
    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH, **kwargs) -> None:
        self.validate_max_length(max_length)
        super().__init__(**kwargs)
        self.max_length = max_length

    def sql_name(self) -> str:
        return f"BLOB({self.max_length})"

    def decode(self, encoded: str) -> bytes:
        return encoded.encode()

    def encode(self, decoded: bytes) -> str:
        return decoded.decode()

    def default_suggestion(self, encoded: bytes) -> str:
        return f"b{encoded}"

    def default_declaration(self, decoded: bytes) -> str:
        return f"\"{decoded.decode()}\""
    
    @classmethod
    def validate_max_length(cls, max_length: int) -> None:
        cls._validate_positive_integer(max_length)
        if max_length <= 0:
            raise ValueError("Max length should be greater than 0.")

    @staticmethod
    def _validate_positive_integer(value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Max length should be a positive integer.")
