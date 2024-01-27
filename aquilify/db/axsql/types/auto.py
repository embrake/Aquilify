from .type import Type

from typing import Optional, Literal

from ..exception import FieldException

class AutoField(Type[Optional[int], Optional[int]]):
    ALLOWED_PRIMARY_TYPES = {"INTEGER", "BIGINT", "UUID", "VARCHAR", "CHAR", "TEXT"}
    
    """
    AutoField represents an auto-incrementing integer field.

    Parameters:
    - primary_key (bool): Indicates if the field is a primary key.
    - nullable (bool): Indicates if the field is nullable.
    - kwargs: Additional keyword arguments.

    Attributes:
    - auto_increment (bool): Indicates if the field is auto-incremented.

    Examples:
    ```python
    field = AutoField(primary_key=True, nullable=False)
    ```

    """
    def __init__(self, type: str = "INTEGER", key_length: int | None = None, primary_key: bool = True, **kwargs):
        self.key_length = key_length
        self.type = type
        self.validate_primary_key_type(type)
        self.validate_primary_key_length(type, key_length)
        super().__init__(primary_key=primary_key, auto_increment=True, **kwargs)
        
    @staticmethod
    def validate_primary_key_type(primary_key_type: str) -> None:
        if primary_key_type.upper() not in AutoField.ALLOWED_PRIMARY_TYPES:
            raise FieldException(
                f"Invalid primary key type: '{primary_key_type}'. Allowed types: {', '.join(AutoField.ALLOWED_PRIMARY_TYPES)}"
            )

    @staticmethod
    def validate_primary_key_length(primary_key_type: str, primary_key_length: Optional[int]) -> None:
        if primary_key_length is not None and primary_key_type.upper() not in {"VARCHAR", "CHAR"}:
            raise FieldException(
                f"Primary key length is only applicable for 'VARCHAR' and 'CHAR' types, not for '{primary_key_type}'"
            )

    @staticmethod
    def construct_primary_key_type(primary_key_type: str, primary_key_length: Optional[int]) -> str:
        if primary_key_length is not None:
            return f"{primary_key_type.upper()}({primary_key_length})"
        return primary_key_type.upper()

    def sql_name(self) -> str:
        """
        Returns the SQL type representation of the field.

        Returns:
        - str: SQL type representation of the field.

        """
        return self.construct_primary_key_type(self.type, self.key_length)

    def encode(self, decoded: Optional[int]) -> Optional[int]:
        """
        Encodes the given value.

        Parameters:
        - decoded (Optional[int]): The value to be encoded.

        Returns:
        - Optional[int]: Encoded value.

        """
        return decoded

    def decode(self, encoded: Optional[int] | Literal["NULL"]) -> Optional[int]:
        """
        Decodes the given value.

        Parameters:
        - encoded (Optional[int] | Literal["NULL"]): The value to be decoded.

        Returns:
        - Optional[int]: Decoded value.

        """
        return encoded if encoded != "NULL" else None

    def default_suggestion(self, encoded: int) -> str:
        """
        Provides a default suggestion for the field.

        Parameters:
        - encoded (int): The encoded value.

        Returns:
        - str: Default suggestion.

        """
        return str(encoded)

    def default_declaration(self, decoded: int) -> str:
        """
        Generates the default declaration for the field.

        Parameters:
        - decoded (int): The decoded value.

        Returns:
        - str: Default declaration.

        """
        return super().default_declaration(decoded)