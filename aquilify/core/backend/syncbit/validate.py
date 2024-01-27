from __future__ import annotations

from typing import TYPE_CHECKING, Union, TypeVar, Callable, Generic, Any, Literal, overload
from typing_extensions import Self
from .utils import MISSING
from .exceptions import FieldError

import collections.abc
import re

if TYPE_CHECKING:
    from .fields.base import Field
    from .schema import Schema
    from .contexts import LoadContext


__all__ = (
    'Validator',
    'field',
    'Range',
    'Length',
    'Exclude',
    'Or',
)

SchemaT = TypeVar('SchemaT', bound='Schema')
InputT = TypeVar('InputT')
ValidatorCallbackT = Callable[[SchemaT, InputT, 'LoadContext'], Any]


class Validator(Generic[InputT]):
    """The base class for validators.

    This class offers an alternative interface to the more commonly used
    :func:`aquilify.backends.syncbit.validate.field` decorator. Validators provided by `AQUILIFY` SyncBit inherit
    from this base class.

    Subclasses are required to override the :meth:`.validate` method.
    When subclassing, ``raw`` subclass parameter can be set to True to mark the
    validator as a :ref:`raw validator <guide-validators-raw-validators>`.

    .. tip::

        This class is a :class:`typing.Generic` and takes a single type argument, the
        type of value which will be validated.
    """
    __validator_is_raw__: bool

    def __init_subclass__(cls, raw: bool = False) -> None:
        cls.__validator_is_raw__ = raw

    def validate(self, value: InputT, context: LoadContext, /) -> Any:
        """Validates a value.

        This is an abstract method that must be implemented by the
        subclasses.

        If the validation fails, either one of :exc:`AssertionError`, :exc:`ValueError`
        or :exc:`aquilify.backends.syncbit.FieldError` should be raised.

        Parameters
        ----------
        value:
            The value to validate.
        context: :class:`LoadContext`
            The deserialization context.
        """
        raise NotImplementedError

    def __call__(self, schema: Schema, value: InputT, context: LoadContext, /) -> bool:
        return self.validate(value, context)


@overload
def field(
    field: Field[Any, InputT],
    *,
    raw: Literal[False] = False,
) -> Callable[[ValidatorCallbackT[SchemaT, InputT]], ValidatorCallbackT[SchemaT, InputT]]:
    ...

@overload
def field(
    field: Field[Any, Any],
    *,
    raw: Literal[True] = True,
) -> Callable[[ValidatorCallbackT[SchemaT, Any]], ValidatorCallbackT[SchemaT, Any]]:
    ...

@overload
def field(
    field: str,
    *,
    raw: bool = ...,
) -> Callable[[ValidatorCallbackT[SchemaT, Any]], ValidatorCallbackT[SchemaT, Any]]:
    ...


def field(
        field: Union[Field[Any, Any], str],
        *,
        raw: bool = False
    ) -> Callable[[ValidatorCallbackT[SchemaT, InputT]], ValidatorCallbackT[SchemaT, InputT]]:
    """A decorator to register a validator for a field.

    The decorated function takes three parameters, the schema (self), the
    value being validated and the :class:`aquilify.backends.syncbit.LoadContext` instance.

    Parameters
    ----------
    field: Union[:class:`aquilify.backends.syncbit.fields.Field`, :class:`str`]
        The field or name of field that the validator is for.
    raw: :class:`bool`
        Whether the validator is a :ref:`raw validator <guide-validators-raw-validators>`.
    """
    def __wrapper(func: ValidatorCallbackT[SchemaT, InputT]) -> ValidatorCallbackT[SchemaT, InputT]:
        func.__validator_field__ = field  # type: ignore
        func.__validator_is_raw__ = raw  # type: ignore
        return func

    return __wrapper


def _assert_value_error(condition: bool, msg: str = ''):
    if not condition:
        raise ValueError(msg)


class Range(Validator[int]):
    """Validates the range of a :class:`~fields.Integer` field.

    Initialization of this validator is similar to Python's :func:`range`
    function with an exception that upper bound is inclusive. That is:

    - ``Range(5)`` must be between 0-5 inclusive (equivalent to ``Range(0, 5)``)
    - ``Range(2, 10)`` must be between 2-10 inclusive

    .. versionadded:: 1.1

    Parameters
    ----------
    lb: :class:`int`
        The lower bound. This parameter acts as an upper bound if no ``ub`` is provided
        and lower bound is defaulted to 0.
    ub: :class:`int`
        The upper bound. If not provided, ``lb`` is considered upper bound and 0 as
        lower bound.
    """
    __slots__ = (
        '_range',
        '_msg',
    )

    def __init__(self, lb: int = MISSING, ub: int = MISSING, /) -> None:
        if lb is MISSING and ub is MISSING:
            raise TypeError('Range() must take at least one argument')  # pragma: no cover

        if ub is MISSING:
            ub = lb
            lb = 0

        if ub == lb:
            self._msg = f'Value must be equal to {lb}'
        else:
            self._msg = f'Value must be in range {lb} to {ub} inclusive'

        self._range = range(lb, ub + 1)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self._range.start}, {self._range.stop - 1})'  # pragma: no cover

    def validate(self, value: int, context: LoadContext) -> Any:
        _assert_value_error(value in self._range, self._msg)

    @classmethod
    def from_standard(cls, obj: range, /) -> Self:
        """Constructs a :class:`validate.Range` from the Python's :func:`range` object.

        When constructed with this function, the returned range validator instance
        would only include the integers accounted by the given standard :func:`range`
        (i.e upper bound not inclusive).
        """
        return cls(obj.start, obj.stop - 1)


class Length(Validator[collections.abc.Sized]):
    """Validates the length of a sized structure.

    This validator could be applied on any structure compatible with the
    :class:`collections.abc.Sized` protocol.

    Initialization examples:

    - ``Length(min=10)``: minimum length 10 characters
    - ``Length(max=10)``: maximum length 10 characters
    - ``Length(min=10, max=20)``: length between 10 to 20 characters
    - ``Length(exact=10)``: length exactly 10 characters

    .. versionadded:: 1.1

    Parameters
    ----------
    min: :class:`int`
        The minimum length.
    max: :class:`int`
        The maximum length.
    exact: :class:`int`
        The exact length. Cannot be mixed with other two parameters.
    """
    def __init__(self, *, min: int = MISSING, max: int = MISSING, exact: int = MISSING) -> None:
        if exact is not MISSING:
            if min is not MISSING or max is not MISSING:
                raise TypeError('exact cannot be mixed with min or max')  # pragma: no cover
            min = max = exact

        if min is MISSING and max is MISSING:
            raise TypeError('One of min, max or both parameters must be provided')  # pragma: no cover

        self._min = min
        self._max = max

        if min == max:
            self._msg = f'Value length must be exactly {min} characters'
        elif min is MISSING and max is not MISSING:
            self._msg = f'Value length must be less than {max} characters'
        elif min is not MISSING and max is MISSING:
            self._msg = f'Value length must be greater than {min} characters'
        else:
            self._msg = f'Value length must be between {min} to {max} characters'

    def validate(self, value: collections.abc.Sized, context: LoadContext) -> Any:
        length = len(value)
        min, max = self._min, self._max

        if max is MISSING:
            _assert_value_error(length >= min, self._msg)
        elif min is MISSING:
            _assert_value_error(length <= max, self._msg)
        else:
            _assert_value_error(length >= min and length <= max, self._msg)


class Regex(Validator[str]):
    """Validates a value using the given regular expression.

    By default, this uses :meth:`re.Pattern.match` to match the pattern
    in given value. Use ``full_match`` or ``search`` parameters to change
    this behaviour.

    .. versionadded:: 1.1

    Parameters
    ----------
    pattern: Union[:class:`str`, :class:`re.Pattern`]
        The pattern to validate from.
    flags: :class:`int`
        The ``re`` flags to pass to pattern. Only applicable when ``pattern``
        is a string.
    fail_message: :class:`str`
        The error message if the given value doesn't match the pattern. This
        can be formatted by using following values:

        - ``{value}``: The value being validated
        - ``{pattern}``: The pattern used for validation
    full_match: :class:`bool`
        If true, uses :meth:`re.Pattern.fullmatch` on the string. This checks
        that string is exact as the pattern. Defaults to False.
    search: :class:`bool`
        If true, uses :meth:`re.Pattern.search` on the string. This simply checks
        if the pattern is in the string at any location. Defaults to False.
    """
    def __init__(
        self,
        pattern: Union[str, re.Pattern[str]],
        flags: int = 0,
        fail_message: str = 'Value failed pattern validation',
        full_match: bool = False,
        search: bool = False,
    ) -> None:

        if full_match and search:
            raise TypeError('full_match and search parameters cannot be mixed')  # pragma: no cover

        self._pattern = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        self._fail_message = fail_message

        if full_match:
            self._match = self._pattern.fullmatch
        elif search:
            self._match = self._pattern.search
        else:
            self._match = self._pattern.match

    def validate(self, value: str, context: LoadContext) -> Any:
        if self._match(value) is None:
            raise ValueError(self._fail_message.format(value=value, pattern=self._pattern))


class Exclude(Validator[Any]):
    """A validator that specifies the values that cannot be passed to a field.

    .. versionadded:: 1.1

    Parameters
    ----------
    *values:
        The values to exclude.
    """
    def __init__(self, *values: Any) -> None:
        self._values = values
        if len(values) == 1:
            self._msg = f'Value cannot be {values[0]!r}'
        else:
            self._msg = f'Value cannot be one from: {", ".join(repr(v) for v in values)}'

    def validate(self, value: Any, context: LoadContext) -> Any:
        _assert_value_error(value not in self._values, self._msg)


class Or(Validator[Any]):
    """A validator that passes if any one of the given validators pass.

    The validators being passed can either be :class:`validate.Validator`
    subclasses or function based validators. In both cases, if any of the
    validator pass, this validator passes.

    .. versionadded:: 1.1

    Parameters
    ----------
    *validators:
        The validators to run.
    """
    def __init__(self, *validators: Union[Validator[Any], ValidatorCallbackT[Any, Any]]) -> None:
        self._validators = validators

    def validate(self, value: Any, context: LoadContext) -> Any:
        passed = False
        for validator in self._validators:
            try:
                validator(context.schema, value, context)
            except (AssertionError, ValueError, FieldError):
                continue
            else:
                passed = True
                break

        if not passed:
            raise ValueError('All validations failed for the given value')
