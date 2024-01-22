from .column import Column
from typing import ClassVar, Optional

class PrimaryKeyField(Column):
    ALLOWED_PRIMARY_TYPES = {"INTEGER", "BIGINT", "UUID", "VARCHAR", "CHAR", "TEXT"}

    def __init__(
        self,
        type: str = "INTEGER",
        key_length: Optional[int] = None,
        autoincrement: bool = True,
        **kwargs
    ) -> None:
        self.validate_primary_key_type(type)
        self.validate_primary_key_length(type, key_length)
        
        super().__init__(
            type=self.construct_primary_key_type(type, key_length),
            primary_key=True,
            autoincrement=autoincrement,
            **kwargs
        )

    @staticmethod
    def validate_primary_key_type(primary_key_type: str) -> None:
        if primary_key_type.upper() not in PrimaryKeyField.ALLOWED_PRIMARY_TYPES:
            raise ValueError(
                f"Invalid primary key type: '{primary_key_type}'. Allowed types: {', '.join(PrimaryKeyField.ALLOWED_PRIMARY_TYPES)}"
            )

    @staticmethod
    def validate_primary_key_length(primary_key_type: str, primary_key_length: Optional[int]) -> None:
        if primary_key_length is not None and primary_key_type.upper() not in {"VARCHAR", "CHAR"}:
            raise ValueError(
                f"Primary key length is only applicable for 'VARCHAR' and 'CHAR' types, not for '{primary_key_type}'"
            )

    @staticmethod
    def construct_primary_key_type(primary_key_type: str, primary_key_length: Optional[int]) -> str:
        if primary_key_length is not None:
            return f"{primary_key_type.upper()}({primary_key_length})"
        return primary_key_type.upper()


class VarCharField(Column):
    DEFAULT_MAX_LENGTH: ClassVar[int] = 255
    MAX_ALLOWED_LENGTH: ClassVar[int] = 1000000

    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH, **kwargs) -> None:
        self.max_length: int = self.validate_max_length(max_length)
        super().__init__(type=self.construct_type(self.max_length), **kwargs)

    @classmethod
    def construct_type(cls, max_length: int) -> str:
        return f"VARCHAR({max_length})"

    @staticmethod
    def validate_max_length(max_length: int) -> int:
        VarCharField._validate_positive_integer(max_length)
        VarCharField._validate_within_allowed_limit(max_length)
        return max_length

    @staticmethod
    def _validate_positive_integer(value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"Max length should be a positive integer. Received: {value}")

    @classmethod
    def _validate_within_allowed_limit(cls, value: int) -> None:
        if value > cls.MAX_ALLOWED_LENGTH:
            raise ValueError(
                f"Max length exceeds the allowed limit of {cls.MAX_ALLOWED_LENGTH}. Received: {value}"
            )
            
class CharField(Column):
    DEFAULT_MAX_LENGTH: ClassVar[int] = 255
    MAX_ALLOWED_LENGTH: ClassVar[int] = 1000000

    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH, **kwargs) -> None:
        validated_length: int = self._validate_max_length(max_length)
        column_type: str = self._construct_column_type(validated_length)
        super().__init__(type=column_type, **kwargs)
        self.max_length: int = validated_length

    @classmethod
    def _construct_column_type(cls, max_length: int) -> str:
        return f"CHAR({max_length})"

    @staticmethod
    def _validate_max_length(max_length: int) -> int:
        CharField._validate_positive_integer(max_length)
        CharField._validate_within_allowed_limit(max_length)
        return max_length

    @staticmethod
    def _validate_positive_integer(value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"Max length should be a positive integer. Received: {value}")

    @classmethod
    def _validate_within_allowed_limit(cls, value: int) -> None:
        if value > cls.MAX_ALLOWED_LENGTH:
            raise ValueError(
                f"Max length exceeds the allowed limit of {cls.MAX_ALLOWED_LENGTH}. Received: {value}"
            )

class RealField(Column):
    DEFAULT_PRECISION: ClassVar[int] = 10
    DEFAULT_SCALE: ClassVar[int] = 5
    MAX_PRECISION: ClassVar[int] = 38
    MAX_SCALE: ClassVar[int] = 38

    def __init__(self, precision: int = DEFAULT_PRECISION, scale: int = DEFAULT_SCALE, **kwargs) -> None:
        self.validate_precision_scale(precision, scale)
        column_type = self.construct_column_type(precision, scale)
        super().__init__(type=column_type, **kwargs)
        self.precision = precision
        self.scale = scale

    @classmethod
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

class TextField(Column):
    DEFAULT_MAX_LENGTH: ClassVar[int] = 65535
    MIN_LENGTH: ClassVar[int] = 1
    MAX_ALLOWED_LENGTH: ClassVar[int] = 1000000 

    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH, **kwargs) -> None:
        self.validate_max_length(max_length)
        super().__init__(type=f"TEXT({max_length})", **kwargs)
        self.max_length = max_length

    @classmethod
    def validate_max_length(cls, max_length: int) -> None:
        cls._validate_positive_integer(max_length)
        if max_length < cls.MIN_LENGTH:
            raise ValueError(f"Max length must be at least {cls.MIN_LENGTH}.")
        if max_length > cls.MAX_ALLOWED_LENGTH:
            raise ValueError(f"Max length exceeds the allowed limit of {cls.MAX_ALLOWED_LENGTH}.")

    @staticmethod
    def _validate_positive_integer(value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Max length should be a positive integer.")

class BigintField(Column):
    DEFAULT_MIN_VALUE: ClassVar[int] = -9223372036854775808  
    DEFAULT_MAX_VALUE: ClassVar[int] = 9223372036854775807   

    def __init__(self, min_value: int = DEFAULT_MIN_VALUE, max_value: int = DEFAULT_MAX_VALUE, **kwargs) -> None:
        self._validate_integer(min_value, "min_value")
        self._validate_integer(max_value, "max_value")
        self._validate_min_max_values(min_value, max_value)
        super().__init__(type="BIGINT", **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    @staticmethod
    def _validate_integer(value: int, field_name: str) -> None:
        if not isinstance(value, int):
            raise TypeError(f"{field_name.capitalize()} should be an integer.")

    @staticmethod
    def _validate_min_max_values(min_value: int, max_value: int) -> None:
        if min_value >= max_value:
            raise ValueError("Minimum value should be less than maximum value.")
        
class BlobField(Column):
    DEFAULT_MAX_LENGTH: ClassVar[int] = 16777216 

    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH, **kwargs) -> None:
        self.validate_max_length(max_length)
        super().__init__(type=f"BLOB({max_length})", **kwargs)
        self.max_length = max_length

    @classmethod
    def validate_max_length(cls, max_length: int) -> None:
        cls._validate_positive_integer(max_length)
        if max_length <= 0:
            raise ValueError("Max length should be greater than 0.")

    @staticmethod
    def _validate_positive_integer(value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Max length should be a positive integer.")
        
class BooleanField(Column):
    def __init__(self, **kwargs) -> None:
        super().__init__(type="BOOLEAN", **kwargs)
        
class IntegerField(Column):
    ALLOWED_INTEGER_TYPES = {"INTEGER", "BIGINT", "SMALLINT"}

    def __init__(
        self,
        type: str = "INTEGER",
        **kwargs
    ) -> None:
        validated_type = self.validate_integer_type(type)
        
        super().__init__(
            type=validated_type,
            **kwargs
        )

    @classmethod
    def validate_integer_type(cls, integer_type: str) -> str:
        validated_type = integer_type.upper() if integer_type.upper() in cls.ALLOWED_INTEGER_TYPES else "INTEGER"
        
        return cls.get_valid_integer_type(validated_type)

    @staticmethod
    def get_valid_integer_type(validated_type: str) -> str:
        return validated_type if validated_type in IntegerField.ALLOWED_INTEGER_TYPES else IntegerField.default_integer_type()

    @staticmethod
    def default_integer_type() -> str:
        return "INTEGER"