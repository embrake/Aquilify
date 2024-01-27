from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Sequence, Union
from .base import Field
from ..exceptions import FieldError

if TYPE_CHECKING:
    from ..contexts import LoadContext, DumpContext, ErrorContext

__all__ = (
    'String',
    'Integer',
    'Float',
    'Boolean',
)

class String(Field[str, str]):
    """Field representing a string (:class:`str`) value.

    This class is a subclass of :class:`Field` and supports the features
    documented in that class.

    Attributes
    ----------
    ERR_INVALID_DATATYPE:
        Error code raised when invalid data type is given in raw data.
    ERR_COERCION_FAILED:
        Error code raised when strict mode is disabled and given raw value
        cannot be converted to relevant data type.

    Parameters
    ----------
    strict: :class:`bool`
        Whether to only allow string data types. If this is set to False,
        any value is type casted to string. Defaults to True.
    """
    ERR_INVALID_DATATYPE = 'string.invalid_datatype'

    def __init__(self, strict: bool = True, **kwargs: Any) -> None:
        self.strict = strict
        super().__init__(**kwargs)

    def _process_value(self, value: Any, ctx: LoadContext) -> str:
        if not isinstance(value, str):
            if self.strict:
                raise self._call_format_error(self.ERR_INVALID_DATATYPE, ctx.schema, value)
            return str(value)
        else:
            return value

    def _get_default_error_message(self, error_code: Any, context: ErrorContext) -> Union[FieldError, str]:
        if error_code == self.ERR_INVALID_DATATYPE:
            return 'Value must be a string'

        return super()._get_default_error_message(error_code, context)

    def value_load(self, value: str, context: LoadContext) -> str:
        return self._process_value(context.value, context)

    def value_dump(self, value: str, context: DumpContext) -> str:
        return value


class Integer(Field[int, int]):
    """Field representing an integer (:class:`int`) value.

    This class is a subclass of :class:`Field` and supports the features
    documented in that class.

    Attributes
    ----------
    ERR_INVALID_DATATYPE:
        Error code raised when invalid data type is given in raw data.
    ERR_COERCION_FAILED:
        Error code raised when strict mode is disabled and given raw value
        cannot be converted to relevant data type.

    Parameters
    ----------
    strict: :class:`bool`
        Whether to only allow integer data types. If this is set to False,
        any integer-castable value is type casted to integer. Defaults to True.
    """
    ERR_INVALID_DATATYPE = 'integer.invalid_datatype'
    ERR_COERCION_FAILED  = 'integer.coercion_failed'

    def __init__(self, strict: bool = True, **kwargs: Any) -> None:
        self.strict = strict
        super().__init__(**kwargs)

    def _process_value(self, value: Any, ctx: LoadContext) -> int:
        if not isinstance(value, int):
            if self.strict:
                raise self._call_format_error(self.ERR_INVALID_DATATYPE, ctx.schema, value)
            try:
                return int(value)
            except Exception:
                raise self._call_format_error(self.ERR_COERCION_FAILED, ctx.schema, value) from None
        else:
            return value

    def _get_default_error_message(self, error_code: Any, context: ErrorContext) -> Union[FieldError, str]:
        if error_code == self.ERR_INVALID_DATATYPE:
            return 'Value must be an integer'
        if error_code == self.ERR_COERCION_FAILED:
            return f'Failed to coerce {context._value!r} to integer'

        return super()._get_default_error_message(error_code, context)

    def value_load(self, value: int, context: LoadContext) -> int:
        return self._process_value(context.value, context)

    def value_dump(self, value: int, context: DumpContext) -> int:
        return value


class Boolean(Field[bool, bool]):
    """Representation of a boolean (:class:`bool`) field.

    This class is a subclass of :class:`Field` and supports the features
    documented in that class.

    Attributes
    ----------
    TRUE_VALUES: Tuple[:class:`str`, ...]
        The true values used when strict validation is disabled.
    FALSE_VALUES: Tuple[:class:`str`, ...]
        The false values used when strict validation is disabled.
    ERR_INVALID_DATATYPE:
        Error code raised when invalid data type is given in raw data.
    ERR_COERCION_FAILED:
        Error code raised when strict mode is disabled and given raw value
        cannot be converted to relevant data type.


    Parameters
    ----------
    true_values: Sequence[:class:`str`]
        The values to use for true boolean conversion. These are only respected
        when :ref:`strict validation <guide-fields-strict-mode>` is disabled.

        Defaults to :attr:`.TRUE_VALUES` if not provided.
    false_values: Sequence[:class:`str`]
        The values to use for false boolean conversion. These are only respected
        when :ref:`strict validation <guide-fields-strict-mode>` is disabled.

        Defaults to :attr:`.FALSE_VALUES` if not provided.
    """
    TRUE_VALUES: Sequence[str] = (
        'TRUE', 'True', 'true',
        'YES', 'Yes', 'yes', '1'
    )

    FALSE_VALUES: Sequence[str] = (
        'FALSE', 'False', 'false',
        'NO', 'No', 'no', '0'
    )

    ERR_INVALID_DATATYPE = 'boolean.invalid_datatype'
    ERR_COERCION_FAILED  = 'boolean.coercion_failed'

    def __init__(
            self,
            *,
            strict: bool = True,
            true_values: Optional[Sequence[str]] = None,
            false_values: Optional[Sequence[str]] = None,
            **kwargs: Any,
        ) -> None:

        super().__init__(**kwargs)

        self.strict = strict
        self._true_values = true_values if true_values is not None else self.TRUE_VALUES
        self._false_values = false_values if false_values is not None else self.FALSE_VALUES

    def _process_value(self, value: Any, ctx: LoadContext) -> bool:
        if not isinstance(value, bool):
            if self.strict:
                raise self._call_format_error(self.ERR_INVALID_DATATYPE, ctx.schema, value)
            value = str(value)
            if value in self._true_values:
                return True
            if value in self._false_values:
                return False
            else:
                raise self._call_format_error(self.ERR_COERCION_FAILED, ctx.schema, value)
        else:
            return value

    def _get_default_error_message(self, error_code: Any, context: ErrorContext) -> Union[FieldError, str]:
        if error_code == self.ERR_INVALID_DATATYPE:
            return 'Value must be a boolean'
        if error_code == self.ERR_COERCION_FAILED:
            return f'Failed to coerce {context._value!r} to boolean'

        return super()._get_default_error_message(error_code, context)  # pragma: no cover

    def value_load(self, value: bool, context: LoadContext) -> bool:
        return self._process_value(context.value, context)

    def value_dump(self, value: bool, context: DumpContext) -> bool:
        return value


class Float(Field[float, float]):
    """Representation of a float (:class:`float`) field.

    This class is a subclass of :class:`Field` and supports the features
    documented in that class.

    Attributes
    ----------
    ERR_INVALID_DATATYPE:
        Error code raised when invalid data type is given in raw data.
    ERR_COERCION_FAILED:
        Error code raised when strict mode is disabled and given raw value
        cannot be converted to relevant data type.

    Parameters
    ----------
    strict: :class:`bool`
        Whether to only allow float data types. If this is set to False,
        any float-castable value is type casted to float. Defaults to True.
    """
    ERR_INVALID_DATATYPE = 'float.invalid_datatype'
    ERR_COERCION_FAILED  = 'float.coercion_failed'

    def __init__(self, strict: bool = True, **kwargs: Any) -> None:
        self.strict = strict
        super().__init__(**kwargs)

    def _process_value(self, value: Any, ctx: LoadContext) -> float:
        if not isinstance(value, float):
            if self.strict:
                raise self._call_format_error(self.ERR_INVALID_DATATYPE, ctx.schema, value)
            try:
                return float(value)
            except Exception:
                raise self._call_format_error(self.ERR_COERCION_FAILED, ctx.schema, value) from None
        else:
            return value

    def _get_default_error_message(self, error_code: Any, context: ErrorContext) -> Union[FieldError, str]:
        if error_code == self.ERR_INVALID_DATATYPE:
            return 'Value must be a floating point number'
        if error_code == self.ERR_COERCION_FAILED:
            return f'Failed to coerce {context._value!r} to float'

        return super()._get_default_error_message(error_code, context)  # pragma: no cover

    def value_load(self, value: float, context: LoadContext) -> float:
        return self._process_value(context.value, context)

    def value_dump(self, value: float, context: DumpContext) -> float:
        return value
