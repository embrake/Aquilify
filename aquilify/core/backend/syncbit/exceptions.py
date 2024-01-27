from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, List, Dict, Union, Literal, overload
from .utils import current_field_key, current_context, current_schema, MISSING

if TYPE_CHECKING:
    from .fields.base import Field
    from .schema import Schema

__all__ = (
    'SyncBitException',
    'FieldNotSet',
    'FrozenError',
    'FieldError',
    'ValidationError'
)


class SyncBitException(Exception):
    """Base class for all exceptions provided by SyncBit."""


class FieldNotSet(AttributeError, SyncBitException):
    """An exception raised when a field is accessed that has no value set.

    This is raised in following circumstances only:

    - For fields that have :attr:`~syncbit.fields.Field.required` set to ``False`` and don't
      have a value set.
    - Field accessed in a context when fields are not loaded yet. An example of this is the
      :meth:`Schema.preprocess_data` method.

    For a more Pythonic handling of this, this exception inherits the :exc:`AttributeError`
    exception.

    Attributes
    ----------
    name: :class:`str`
        The name that was used to address the field. This could be different from the
        field's attribute name if the field has a specific load key set.
    field: :class:`syncbit.fields.Field`
        The field that was accessed but had no value set.
    schema: :class:`Schema`
        The schema that accessed the field.
    """
    def __init__(self, field: Field[Any, Any], schema: Schema, field_name: str) -> None:
        self.field_name = field_name
        self.field = field
        self.schema = schema
        super().__init__(f'Field {field._name!r} has no value set', field._name, schema)


class FrozenError(SyncBitException):
    """An exception raised when a frozen field or schema is updated.

    Attributes
    ----------
    entity: Union[:class:`Schema`, :class:`Field`]
        The schema or field that was attempted to be updated.
    """
    def __init__(self, entity: Union[Schema, Field[Any, Any]]) -> None:
        from .schema import Schema  # circular import

        self.entity = entity

        name = f'{entity.__class__.__name__} schema' if isinstance(entity, Schema) else \
               f'{entity._schema.__name__}.{entity._name} field'

        super().__init__(f'{name} is frozen and cannot be updated')


class FieldError(SyncBitException):
    """An error raised when validation fails for a field.

    This error when raised in validators or other user-side code is accounted
    as validation error and is included in the subsequent raised :exc:`ValidationError`.

    For convenience, instead of raising this error directly, you should raise :exc:`ValueError`
    or :exc:`AssertionError` in your validators code which would automatically be wrapped
    as a field error.

    .. warning::

        It is recommended to raise :exc:`ValueError` if you intend to run your script using
        the Python's ``-O`` or ``-OO`` optimization flags. These flags remove the assertion
        statements from the code causing the validators to stop working properly.

    Parameters
    ----------
    message:
        The error message. If this is a sequence, each element of sequence is accounted
        as a separate error.
    state:
        The state to attach to this error. This parameter allows users to attach
        extra state that can be accessed later. Library will not be performing any
        manipulations on this value.

    Attributes
    ----------
    context: Optional[Union[:class:`LoadContext`, :class:`DumpContext`]]
        The current context in which the error was raised. Could be None if
        no context exists.
    schema: :class:`Schema`
        The schema that the error originates from.
    """
    def __init__(self, message: Any, /, state: Any = None) -> None:
        self.message = message
        self.state = state
        self.context = current_context.get(None)
        self.schema = current_schema.get()
        self._key = current_field_key.get()
        super().__init__(message)

    @classmethod
    def _from_standard_error(
        cls,
        err: Union[ValueError, AssertionError],
        schema: Schema,
        field: Field[Any, Any],
        value: Any = MISSING,
    ) -> FieldError:
        message = str(err)
        if not message:
            return field._call_format_error(field.ERR_VALIDATION_FAILED, schema, value)
        else:
            return cls(message)

    def _copy_with(self, message: Any) -> FieldError:
        copy = self.__class__.__new__(self.__class__)
        copy.message = message
        copy.state = self.state
        copy.context = self.context
        copy.schema = self.schema
        copy._key = self._key
        return copy

    @property
    def field(self) -> Optional[Field[Any, Any]]:
        """The :class:`~fields.Field` that caused the error.

        If this returns None, it means that the causative field doesn't
        exist. An example of this case is when an invalid field name is
        passed during schema initialization.

        :type: :class:`fields.Field`
        """
        return self.schema.__load_fields__.get(self._key, None)

    @property
    def key(self) -> str:
        """The key that points to the erroneous value in raw data.

        This is essentially the name of field that has the error but may
        not always be a valid field name.

        :type: :class:`str`
        """
        return self._key


class ValidationError(SyncBitException):
    """An error raised when validation fails with one or more :class:`FieldError`.

    Parameters
    ----------
    errors: List[:class:`FieldError`]
        The errors that caused the validation failure.
    schema: :class:`Schema`
        The schema this error originates from.
    """
    def __init__(self, errors: List[FieldError]) -> None:
        self.errors = errors.copy()
        self.schema = current_schema.get()
        self._flatten_errors(errors)
        super().__init__(self._make_message())

    def _flatten_errors(self, errors: List[FieldError]) -> None:
        for error in errors:
            if not isinstance(error.message, (list, tuple, set)):
                continue

            self.errors.remove(error)
            for message in error.message:  # type: ignore
                self.errors.append(error._copy_with(message))

    def _make_message(self, field_errors: Optional[Dict[str, List[FieldError]]] = None, level: int = 0) -> str:
        if field_errors is None:
            field_errors = self._raw_std(include_message=False)

        builder: List[str] = []
        if level == 0:
            schema_name = self.schema.__class__.__qualname__
            builder.append(f'│ {len(field_errors)} validation {"errors" if len(field_errors) > 1 else "error"} in schema {schema_name!r}')

        indent = level*4
        for name, errors in field_errors.items():
            builder.append(f'{" "*indent}│')
            message = f'{" "*indent}└── In field {name}:'
            if errors:
                field = errors[0].field
                if field and name != field._name:
                    message = f'{" "*indent}└── In field {name} ({field._name}):'

            builder.append(message)
            for idx, error in enumerate(errors):
                if isinstance(error.message, dict):
                    builder.append(self._make_message(error.message, level=level+1))  # type: ignore
                    continue

                prefix = '└──' if idx == len(errors) - 1 else '├──' 
                builder.append(f'{" "*(indent+4)}{prefix} {error.message}')

        if level != 0:
            return '\n'.join(builder)

        return '\n│\n' + '\n'.join(builder)

    def _ensure_string(self, obj: Any) -> Any:
        if isinstance(obj, FieldError):
            return self._ensure_string(obj.message)
        elif isinstance(obj, dict):
            new_dict: Dict[str, Any] = {}
            for k, v in obj.items():  # type: ignore
                new_dict[k] = self._ensure_string(v)  # type: ignore
            return new_dict
        elif isinstance(obj, list):
            new_list: List[Any] = []
            for item in obj:  # type: ignore
                new_list.append(self._ensure_string(item))
            return new_list
        return str(obj)

    @overload
    def _raw_std(
        self,
        *,
        include_message: Literal[True] = True
    ) -> Dict[str, List[str]]:
        ...

    @overload
    def _raw_std(
        self,
        *,
        include_message: Literal[False] = False
    ) -> Dict[str, List[FieldError]]:
        ...

    def _raw_std(self, *, include_message: bool = True) -> Any:
        out: Dict[str, Any] = {}
        for error in self.errors:
            if include_message:
                value = self._ensure_string(error.message)
            else:
                value = error

            if error.key in out:
                out[error.key].append(value)
            else:
                out[error.key] = [value]

        return out

    def raw(self) -> Any:
        """Converts the error into raw format.

        The standard format returned by this method is a dictionary containing
        field names as keys and list of error messages as the value.

        This method can be overriden to implement a custom format.
        """
        return self._raw_std()
