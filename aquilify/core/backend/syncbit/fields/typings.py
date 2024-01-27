from __future__ import annotations

from .base import Field
from ..exceptions import FieldError
from ..type_validation import TypeValidator

# typing imported as t to avoid name conflict with classes
# defined in this module
import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from ..contexts import LoadContext, DumpContext, ErrorContext

__all__ = (
    'Any',
    'Literal',
    'Union',
    'TypeExpr',
)

_T = t.TypeVar('_T')

def _generic_type_with_args(tp: _T, args: t.Sequence[t.Any]) -> _T:
    # Before Python 3.11, T[*v] notation isn't supported and raises
    # syntax error so this is a very hacky approach to get the desired
    # generic type with given type arguments at runtime.
    return tp.__getitem__(tuple(args))  # type: ignore

class Any(Field[t.Any, t.Any]):
    """A field that accepts any arbitrary value.

    This field acts as a "raw field" that performs no validation on the
    given value.
    """
    def value_load(self, value: Any, context: LoadContext) -> Any:
        return value

    def value_dump(self, value: Any, context: DumpContext) -> Any:
        return value


class Literal(Field[_T, _T]):
    """A field that accepts only exact literal values.

    This works in a similar fashion as :class:`typing.Literal`.

    .. versionadded:: 1.1

    Attributes
    ----------
    ERR_INVALID_VALUE:
        Error raised when the given value is not from the provided literal value.

    Parameters
    ----------
    *values:
        The literal values.
    """
    ERR_INVALID_VALUE = 'literal.invalid_value'

    def __init__(self, *values: _T, **kwargs: t.Any) -> None:
        self.values = values
        self._tp = TypeValidator({'root': _generic_type_with_args(t.Literal, values)})
        super().__init__(**kwargs)

    def _get_default_error_message(self, error_code: t.Any, context: ErrorContext) -> t.Union[FieldError, str]:
        if error_code == self.ERR_INVALID_VALUE:
            return FieldError(context.metadata['type_validation_fail_errors'])

        return super()._get_default_error_message(error_code, context)  # pragma: no cover

    def value_load(self, value: t.Any, context: LoadContext) -> _T:
        validated, errors = self._tp.validate('root', value)  # type: ignore
        if not validated:
            metadata = {'type_validation_fail_errors': errors}
            raise self._call_format_error(self.ERR_INVALID_VALUE, context.schema, value, metadata)
        return value

    def value_dump(self, value: _T, context: DumpContext) -> t.Any:
        return value


class Union(Field[_T, _T]):
    """A field that accepts values of any of the given data types.

    This is similar to the :class:`typing.Union` type. Note that this field
    only performs simple :func:`isinstance` check on the given value.

    .. versionadded:: 1.1

    Attributes
    ----------
    ERR_INVALID_VALUE:
        Error raised when the given value is not from the provided types.

    Parameters
    ----------
    *types: :class:`type`
        The list of types to accept.
    """
    ERR_INVALID_VALUE = 'union.invalid_value'

    def __init__(self, *types: t.Type[_T], **kwargs: t.Any):
        if len(types) < 2:
            raise TypeError('fields.Union() accepts at least two arguments')  # pragma: no cover

        self.types = types
        self._tp = TypeValidator({'root': _generic_type_with_args(t.Union, types)})
        super().__init__(**kwargs)

    def _get_default_error_message(self, error_code: t.Any, context: ErrorContext) -> t.Union[FieldError, str]:
        if error_code == self.ERR_INVALID_VALUE:
            return FieldError(context.metadata['type_validation_fail_errors'])

        return super()._get_default_error_message(error_code, context)  # pragma: no cover

    def value_load(self, value: t.Any, context: LoadContext) -> _T:
        validated, errors = self._tp.validate('root', value)  # type: ignore
        if not validated:
            metadata = {'type_validation_fail_errors': errors}
            raise self._call_format_error(self.ERR_INVALID_VALUE, context.schema, value, metadata)
        return value

    def value_dump(self, value: _T, context: DumpContext) -> _T:
        return value


class TypeExpr(Field[_T, _T]):
    """A field that accepts value compatible with given type expression.

    For the list of supported types and limitations of this field, please see
    the :ref:`guide-type-validation` section.

    .. note::

        This uses :func:`aquilify.backends.syncbit.validate_types` under the hood.

    .. versionadded:: 1.1

    Parameters
    ----------
    expr:
        The type expression that should be used to validate the type of
        given value.
    """
    ERR_TYPE_VALIDATION_FAILED = 'type_expr.type_validation_failed'

    def __init__(self, expr: t.Type[_T], **kwargs: t.Any):
        self.expr = expr
        self._tp = TypeValidator({'root': expr})
        super().__init__(**kwargs)

    def _get_default_error_message(self, error_code: t.Any, context: ErrorContext) -> t.Union[FieldError, str]:
        if error_code == self.ERR_TYPE_VALIDATION_FAILED:
            return FieldError(context.metadata['type_validation_fail_errors'])

        return super()._get_default_error_message(error_code, context)  # pragma: no cover

    def value_load(self, value: t.Any, context: LoadContext) -> _T:
        validated, errors = self._tp.validate('root', value)
        if not validated:
            metadata = {'type_validation_fail_errors': errors}
            raise self._call_format_error(self.ERR_TYPE_VALIDATION_FAILED, context.schema, value, metadata)
        return value

    def value_dump(self, value: _T, context: DumpContext) -> _T:
        return value
