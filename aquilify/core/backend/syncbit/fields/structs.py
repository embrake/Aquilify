from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Dict as DictT,
    List as ListT,
    Set as SetT,
    TypedDict as TypedDictT,
    Any,
    Union,
    TypeVar,
    Type,
)
from .base import Field
from ..exceptions import FieldError
from ..utils import MISSING
from ..type_validation import TypeValidator

if TYPE_CHECKING:
    from ..contexts import LoadContext, DumpContext, ErrorContext

__all__ = (
    'Dict',
    'TypedDict',
    'List',
    'Set',
)

TD = TypeVar('TD', bound=TypedDictT)
KT = TypeVar('KT')
VT = TypeVar('VT')


class _BaseStructField(Field[KT, VT]):
    _struct_name: str
    _friendly_struct_name: str

    ERR_INVALID_DATATYPE = 'struct.invalid_datatype'
    ERR_TYPE_VALIDATION_FAILED = 'struct.type_validation_failed'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.ERR_INVALID_DATATYPE = f'{self._struct_name}.invalid_datatype'  # type: ignore
        self.ERR_TYPE_VALIDATION_FAILED = f'{self._struct_name}.type_validation_failed'  # type: ignore
        super().__init__(*args, **kwargs)

    def _get_default_error_message(self, error_code: Any, context: ErrorContext) -> Union[FieldError, str]:
        if error_code == self.ERR_INVALID_DATATYPE:
            return f'Value must be a {self._friendly_struct_name}'
        if error_code == self.ERR_TYPE_VALIDATION_FAILED:
            return FieldError(context.metadata['type_validation_fail_errors'])

        return super()._get_default_error_message(error_code, context)  # pragma: no cover


class Dict(_BaseStructField[DictT[KT, VT], DictT[KT, VT]]):
    """A field that accepts a dictionary.

    When initialized without an argument, the field accepts any arbitrary
    dictionary. The two positional arguments correspond to the type of key
    of dictionary and type of value respectively.

    These arguments can take a type expression. For example, ``Dict(Union[str, int], bool)``
    accepts a dictionary with key of type either a string or integer and a boolean as a value.

    For more information type validation, see the :ref:`guide-type-validation` page.

    .. versionadded:: 1.1

    Attributes
    ----------
    ERR_INVALID_DATATYPE:
        Error raised when the given value is not a dictionary.
    ERR_TYPE_VALIDATION_FAILED:
        Error raised when the type validation fails. In this error's context,
        :attr:`ErrorContext.metadata` has a key ``type_validation_fail_errors``
        which is a list of error messages.

    Parameters
    ----------
    key_tp:
        The type of key of dictionary.
    value_tp:
        The type of value of dictionary.
    """
    _struct_name = 'dict'
    _friendly_struct_name = 'dictionary'

    def __init__(self, key_tp: Type[KT] = MISSING, value_tp: Type[VT] = MISSING, /, **kwargs: Any) -> None:
        self.key_tp = key_tp
        self.value_tp = value_tp

        if key_tp is not MISSING:
            if value_tp is MISSING:
                raise TypeError('Dict(T) is not valid, must provide a second argument for type of value')  # pragma: no cover
            self._tp = TypeValidator({'root': DictT[key_tp, value_tp]})
        else:
            self._tp = None

        super().__init__(**kwargs)

    def value_load(self, value: Any, context: LoadContext) -> DictT[KT, VT]:
        if not isinstance(value, dict):
            raise self._call_format_error(self.ERR_INVALID_DATATYPE, context.schema, value)
        if self._tp is not None:
            validated, errors = self._tp.validate('root', value)
            if not validated:
                metadata = {'type_validation_fail_errors': errors}
                raise self._call_format_error(self.ERR_TYPE_VALIDATION_FAILED, context.schema, value, metadata=metadata)
        return value  # type: ignore

    def value_dump(self, value: DictT[KT, VT], context: DumpContext) -> DictT[KT, VT]:
        return value


class TypedDict(_BaseStructField[TD, TD]):
    """A field that validates from a :class:`typing.TypedDict`.

    This class provides type validation on the values of given :class:`TypedDict`,
    For more information type validation, see the :ref:`guide-type-validation` page.

    .. versionadded:: 1.1

    Attributes
    ----------
    ERR_INVALID_DATATYPE:
        Error raised when the given value is not a dictionary.
    ERR_TYPE_VALIDATION_FAILED:
        Error raised when the type validation fails. In this error's context,
        :attr:`ErrorContext.metadata` has a key ``type_validation_fail_errors``
        which is a list of error messages.

    Parameters
    ----------
    typed_dict: :class:`typing.TypedDict`
        The typed dictionary to validate from.
    """
    _struct_name = 'typed_dict'
    _friendly_struct_name = 'dictionary'

    def __init__(self, typed_dict: Type[TD], /, **kwargs: Any):
        self.typed_dict = typed_dict
        self._validator = TypeValidator({'root': typed_dict})
        super().__init__(**kwargs)

    def value_load(self, value: Any, context: LoadContext) -> TD:
        if not isinstance(value, dict):
            raise self._call_format_error(self.ERR_INVALID_DATATYPE, context.schema, value)

        validated, errors = self._validator.validate('root', value)
        if not validated:
            metadata = {'type_validation_fail_errors': errors}
            raise self._call_format_error(self.ERR_TYPE_VALIDATION_FAILED, context.schema, value, metadata=metadata)

        return value  # type: ignore

    def value_dump(self, value: TD, context: DumpContext) -> TD:
        return value


class List(_BaseStructField[ListT[KT], ListT[KT]]):
    """A field that accepts a :class:`list`.

    .. versionadded:: 1.1

    Attributes
    ----------
    ERR_INVALID_DATATYPE:
        Error raised when the given value is not a dictionary.
    ERR_TYPE_VALIDATION_FAILED:
        Error raised when the type validation fails. In this error's context,
        :attr:`ErrorContext.metadata` has a key ``type_validation_fail_errors``
        which is a list of error messages.

    Parameters
    ----------
    type:
        The type of list elements. This parameter corresponds to ``T``
        in ``typing.List[T]``.
    """
    _struct_name = 'list'
    _friendly_struct_name = 'list'

    def __init__(self, type: Type[KT] = MISSING, /, **kwargs: Any):
        self.type = type
        self._tp = None if type is MISSING else TypeValidator({'root': ListT[type]})
        super().__init__(**kwargs)

    def value_load(self, value: Any, context: LoadContext) -> ListT[KT]:
        if not isinstance(value, list):
            raise self._call_format_error(self.ERR_INVALID_DATATYPE, context.schema, value)
        if self._tp is not None:
            validated, errors = self._tp.validate('root', value)
            if not validated:
                metadata = {'type_validation_fail_errors': errors}
                raise self._call_format_error(self.ERR_TYPE_VALIDATION_FAILED, context.schema, value, metadata=metadata)
        return value  # type: ignore

    def value_dump(self, value: ListT[KT], context: DumpContext) -> ListT[KT]:
        return value


class Set(_BaseStructField[SetT[KT], SetT[KT]]):
    """A field that accepts a :class:`set`.

    .. versionadded:: 1.1

    Attributes
    ----------
    ERR_INVALID_DATATYPE:
        Error raised when the given value is not a dictionary.
    ERR_TYPE_VALIDATION_FAILED:
        Error raised when the type validation fails. In this error's context,
        :attr:`ErrorContext.metadata` has a key ``type_validation_fail_errors``
        which is a list of error messages.

    Parameters
    ----------
    type:
        The type of set elements. This parameter corresponds to ``T``
        in ``typing.Set[T]``.
    """
    _struct_name = 'set'
    _friendly_struct_name = 'set'

    def __init__(self, type: Type[KT] = MISSING, /, **kwargs: Any):
        self.type = type
        self._tp = None if type is MISSING else TypeValidator({'root': SetT[type]})
        super().__init__(**kwargs)

    def value_load(self, value: Any, context: LoadContext) -> SetT[KT]:
        if not isinstance(value, set):
            raise self._call_format_error(self.ERR_INVALID_DATATYPE, context.schema, value)
        if self._tp is not None:
            validated, errors = self._tp.validate('root', value)
            if not validated:
                metadata = {'type_validation_fail_errors': errors}
                raise self._call_format_error(self.ERR_TYPE_VALIDATION_FAILED, context.schema, value, metadata=metadata)
        return value  # type: ignore

    def value_dump(self, value: SetT[KT], context: DumpContext) -> SetT[KT]:
        return value
