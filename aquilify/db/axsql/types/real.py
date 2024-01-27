"""
The module containing logic for boolean types.
"""

from .type import Type
from typing import ClassVar


class RealField(Type[int, bool]):
    DEFAULT_PRECISION: ClassVar[int] = 10
    DEFAULT_SCALE: ClassVar[int] = 5
    MAX_PRECISION: ClassVar[int] = 38
    MAX_SCALE: ClassVar[int] = 38
    
    def __init__(self, precision: int = DEFAULT_PRECISION, scale: int = DEFAULT_SCALE, **kwargs) -> None:
        self.validate_precision_scale(precision, scale)
        super().__init__(**kwargs)
        self.precision = precision
        self.scale = scale

    def sql_name(self) -> str:
        return self.construct_column_type(self.precision, self.scale)

    def decode(self, encoded: int) -> bool:
        return bool(encoded)

    def encode(self, decoded: bool) -> int:
        return 1 if decoded else 0

    def default_suggestion(self, encoded: int) -> str:
        return str(bool(encoded))

    def default_declaration(self, decoded: bool) -> str:
        return super().default_declaration(decoded)
    
    classmethod
    def construct_column_type(cls, precision: int, scale: int) -> str:
        return f"REAL({precision}, {scale})"

    @staticmethod
    def validate_precision_scale(precision: int, scale: int) -> None:
        if not isinstance(precision, int) or not isinstance(scale, int):
            raise TypeError("Precision and scale must be integers.")
        if precision <= 0 or scale < 0:
            raise ValueError("Precision must be a positive integer and scale must be a non-negative integer.")
        if precision > RealField.MAX_PRECISION or scale > RealField.MAX_SCALE:
            raise ValueError(f"Precision and scale should not exceed: Precision <= {RealField.MAX_PRECISION}, "
                             f"Scale <= {RealField.MAX_SCALE}")
        if precision < scale:
            raise ValueError("Precision must be greater than or equal to the scale.")
