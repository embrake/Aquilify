from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    TypeVar,
    Generic,
    Any,
    Type,
    Literal,
    Optional,
    Union,
    List,
    Sequence,
    Iterator,
    Dict,
    overload,
)
from typing_extensions import Self
from ..schema import Schema
from ..validate import Validator, ValidatorCallbackT, InputT
from ..utils import MISSING, current_field_key, current_schema
from ..exceptions import FieldError, FrozenError
from ..contexts import ErrorContext
from ..configs import config

import copy

if TYPE_CHECKING:
    from ..contexts import LoadContext, DumpContext


__all__ = (
    'Field',
)

SchemaT = TypeVar('SchemaT', bound='Schema')
RawValueT = TypeVar('RawValueT')
FinalValueT = TypeVar('FinalValueT')
ValidatorT = Union[Validator[InputT], ValidatorCallbackT[SchemaT, InputT]]

class Field(Generic[RawValueT, FinalValueT]):
    """The base class for all fields.

    All fields provided by SyncBit inherit from this class. If you intend to create
    a custom field, you must use this class to inherit the field from. Subclasses
    must implement the following methods:

    - :meth:`.value_load`
    - :meth:`.value_dump`

    .. tip::

        This class is a :class:`typing.Generic` and takes two type arguments. The
        raw value type i.e the type of raw value which will be deserialized to final
        value and the type of deserialized value.

    Attributes
    ----------
    ERR_FIELD_REQUIRED:
        Error code raised when a required field is not given in raw data.
    ERR_NONE_DISALLOWED:
        Error code raised when a field with ``none=False`` is given a value of ``None``.
    ERR_VALIDATION_FAILED:
        Error code raised when a validator fails for a field without an explicit
        error message.

    Parameters
    ----------
    none: :class:`bool`
        Whether this field allows None values to be set.
    required: :class:`bool`
        Whether this field is required.
    frozen: :class:`bool`
        Whether the field is frozen. Frozen fields are read only fields
        that cannot be updated once initialized.
    default:
        The default value for this field. If this is passed, the field is automatically
        marked as optional i.e ``required`` parameter gets ignored.

        A callable can also be passed in this parameter that returns the default
        value. The callable takes two parameters, that is the current :class:`SchemaContext`
        instance and the current :class:`Field` instance.
    validators: List[Union[callable, :class:`Validator`]]
        The list of validators for this field.
    extras: Dict[:class:`str`, Any]
        A dictionary of extra data that can be attached to this field. This parameter is
        useful when you want to attach your own extra metadata to the field. Library does
        not perform any manipulation on the data.
    load_key: :class:`str`
        The key that points to value of this field in raw data. Defaults to the :attr:`name`
        of field.
    dump_key: :class:`str`
        The key that points to value of this field in serialized data returned by
        :meth:`Schema.dump`. Defaults to the :attr:`name` of field.
    data_key: :class:`str`
        A shorthand parameter to control the value of both ``load_key`` and ``dump_key``
        parameters.
    """
    ERR_FIELD_REQUIRED = 'field.field_required'
    ERR_NONE_DISALLOWED = 'field.none_disallowed'
    ERR_VALIDATION_FAILED = 'field.validation_failed'

    __slots__ = (
        'none',
        'required',
        'frozen',
        'extras',
        '_default',
        '_name',
        '_schema',
        '_validators',
        '_raw_validators',
        '_load_key',
        '_dump_key',
    )

    def __init__(
            self,
            *,
            none: bool = False,
            required: bool = True,
            frozen: bool = False,
            default: Any = MISSING,
            validators: Sequence[ValidatorT[Any, Any]] = MISSING,
            extras: Dict[str, Any] = MISSING,
            dump_key: str = MISSING,
            load_key: str = MISSING,
            data_key: str = MISSING,
        ) -> None:

        self.none = none
        self.frozen = frozen
        self.required = required and (default is MISSING)
        self.extras = extras if extras is not MISSING else {}
        self._load_key = data_key if data_key is not MISSING else load_key
        self._dump_key = data_key if data_key is not MISSING else dump_key
        self._default = default
        self._validators: List[ValidatorT[FinalValueT, Any]] = []
        self._raw_validators: List[ValidatorT[Any, Any]] = []
        self._unbind()

        if validators is not MISSING:
            for validator in validators:
                self.add_validator(validator)

    @overload
    def __get__(self, instance: Literal[None], owner: Type[Schema]) -> Self:
        ...

    @overload
    def __get__(self, instance: Schema, owner: Type[Schema]) -> FinalValueT:
        ...

    def __get__(self, instance: Optional[Schema], owner: Type[Schema]) -> Union[FinalValueT, Self]:
        if instance is None:
            return self

        return instance.get_value_for(self._name)

    def __set__(self, instance: Schema, value: RawValueT) -> None:
        if instance.__config__.frozen:
            raise FrozenError(instance)
        if self.frozen:
            raise FrozenError(self)

        schema_token = current_schema.set(instance)
        field_name = current_field_key.set(self._name)
        try:
            errors = instance._process_field_value(self, value)
            if errors:
                raise config.validation_error_cls(errors)
        finally:
            current_schema.reset(schema_token)
            current_field_key.reset(field_name)

    def _unbind(self) -> None:
        self._name: str = MISSING
        self._schema: Type[Schema] = MISSING

    def _is_bound(self) -> bool:
        return self._name is not MISSING and self._schema is not MISSING

    def _bind(self, name: str, schema: Type[Schema]) -> None:
        if self._is_bound():
            raise RuntimeError(f"Field {schema.__name__}.{name} is already bound to {self._schema.__name__}.{self._name}")

        self._name = name
        self._schema = schema

    def _run_validators(self, value: Any, context: LoadContext, raw: bool = False) -> List[FieldError]:
        validators = self._raw_validators if raw else self._validators
        errors: List[FieldError] = []

        for validator in validators:
            try:
                validator(context.schema, value, context)
            except (FieldError, AssertionError, ValueError) as err:
                if isinstance(err, (AssertionError, ValueError)):
                    err = FieldError._from_standard_error(err, schema=context.schema, field=self, value=value)
                errors.append(err)

        return errors

    def _get_default_error_message(self, error_code: str, context: ErrorContext, /) -> Union[FieldError, str]:
        if error_code == self.ERR_VALIDATION_FAILED:
            return 'Validation failed for this field.'
        if error_code == self.ERR_NONE_DISALLOWED:
            return 'This field must not be None.'
        if error_code == self.ERR_FIELD_REQUIRED:
            return 'This field is required.'

        return 'An unknown error occurred while validating this field.'  # pragma: no cover

    def _call_format_error(
            self,
            error_code: str,
            schema: Schema,
            value: Any = MISSING,
            metadata: Dict[str, Any] = MISSING,
        ) -> FieldError:

        ctx = ErrorContext(
            error_code=error_code,
            value=value,
            field=self,
            schema=schema,
            metadata=metadata,
        )

        error = self.format_error(error_code, ctx)

        if error is None:
            # if format_error returns None, error code is not covered
            # by the overriden implementation so fallback to default errors
            error = self._get_default_error_message(error_code, ctx)

        if isinstance(error, str):
            return FieldError(error)
        if isinstance(error, FieldError):
            return error
        else:
            raise TypeError('format_error() must return a FieldError or a str')  # pragma: no cover

    @property
    def load_key(self) -> str:
        return self._name if self._load_key is MISSING else self._load_key

    @property
    def dump_key(self) -> str:
        return self._name if self._dump_key is MISSING else self._dump_key

    @property
    def default(self) -> Any:
        return self._default if self._default is not MISSING else None

    @property
    def schema(self) -> Type[Schema]:
        """The schema that the field belongs to.

        .. versionadded:: 1.1

        :type: :class:`Schema`
        """
        if self._schema is MISSING:  # pragma: no cover
            raise RuntimeError('Field has no schema set')
        return self._schema  # pragma: no cover

    @property
    def name(self) -> str:
        """The name of attribute that the field is assigned to.
        
        .. versionadded:: 1.1

        :type: :class:`str`
        """
        if self._name is MISSING:  # pragma: no cover
            raise RuntimeError('Field has no name set')
        return self._name  # pragma: no cover

    def has_default(self) -> bool:
        """Indicates whether the field has a default value."""
        return self._default is not MISSING

    def copy(self) -> Field[RawValueT, FinalValueT]:
        """Copies a field.

        This method is useful when you want to reuse fields from other
        schemas. For example::

            class User(syncbit.Schema):
                id = fields.Integer(strict=False)
                username = fields.String()

            class Game(syncbit.Schema):
                id = User.id.copy()
                name = fields.String()

        Returns
        -------
        :class:`Field`
            The new field.
        """
        field = copy.copy(self)
        field._unbind()
        return field

    def add_validator(self, validator: ValidatorT[Any, Any], *, raw: bool = False) -> None:
        """Registers a validator for this field.

        Parameters
        ----------
        validator: Union[callable, :class:`validate.Validator`]
            The validator to register. This can be a callable function or a 
            :class:`validate.Validator` instance.
        raw: :class:`bool`
            Whether a raw validator is being registered. This parameter is only
            taken into account when a callable is passed instead of a 
            :class:`validate.Validator` instance.
        """
        if not callable(validator):
            raise TypeError('validator must be a callable or Validator class instance')  # pragma: no cover

        raw = getattr(validator, '__validator_is_raw__', raw)
        self._raw_validators.append(validator) if raw else self._validators.append(validator)

    def remove_validator(self, validator: ValidatorT[Any, Any], *, raw: bool = False) -> None:
        """Removes a validator from this field.

        No error is raised if the given validator is not already registered.

        Parameters
        ----------
        validator: Union[callable, :class:`validate.Validator`]
            The validator to remove. This can be a callable function or a 
            :class:`validate.Validator` instance.
        raw: :class:`bool`
            Whether the validator being removed is raw. This parameter is only
            taken into account when a callable is passed instead of a 
            :class:`validate.Validator` instance.
        """
        if not callable(validator):
            raise TypeError('validator must be a callable or Validator class instance')  # pragma: no cover

        raw = getattr(validator, '__validator_is_raw__', raw)
        try:
            self._raw_validators.remove(validator) if raw else self._validators.remove(validator)
        except ValueError:  # pragma: no cover
            pass

    def clear_validators(self, *, raw: bool = MISSING) -> None:
        """Removes all validator from this field.

        Parameters
        ----------
        raw: :class:`bool`
            Whether to remove raw validators only. If this is not passed, all validators
            are removed. If this is True, only raw validators are removed and when False,
            only non-raw validators are removed.
        """
        if raw is MISSING:
            self._validators.clear()
            self._raw_validators.clear()
        elif raw:
            self._raw_validators.clear()
        else:
            self._validators.clear()

    def walk_validators(self, *, raw: bool = MISSING) -> Iterator[ValidatorCallbackT[Any, Any]]:
        """Iterates through the validator from this field.

        Parameters
        ----------
        raw: :class:`bool`
            Whether to iterate through raw validators only. If this is not passed,
            all validators are iterated. If this is True, only raw validators
            are iterated  and when False, only non-raw validators are iterated.
        """
        if raw is MISSING:
            validators = self._validators.copy()
            validators.extend(self._raw_validators)
        elif raw:
            validators = self._raw_validators
        else:
            validators = self._validators

        for validator in validators:
            yield validator

    def format_error(self, error_code: Any, context: ErrorContext, /) -> Optional[Union[FieldError, str]]:
        """Formats the error.

        This method can be overriden to add custom error messages for default
        errors. It should return a :class:`FieldError` or :class:`str`.

        .. versionchanged:: 1.1

            This method no longer requires super call. Default error messages
            are now automatically resolved.

        Parameters
        ----------
        error_code: :class:`str`
            The error code indicating the error that was raised.
        context: :class:`ErrorContext`
            The context holding useful information about error.

        Returns
        -------
        Optional[Union[:class:`FieldError`, :class:`str`]]
            The formatted error.
        """
        return self._get_default_error_message(error_code, context)

    def value_load(self, value: Any, context: LoadContext, /) -> FinalValueT:
        """Deserializes a raw value.

        This is an abstract method that must be implemented by subclasses. This
        method is called by the library when a field is being loaded.

        The instances when this method is called are:

        - Initializing a :class:`Schema`
        - Updating a field value on an existing :class:`Schema` instance

        The returned value is the value assigned to :class:`Schema` field
        attribute.

        Parameters
        ----------
        value:
            The value to deserialize.
        context: :class:`LoadContext`
            The deserialization context.

        Returns
        -------
        The serialized value.
        """
        raise NotImplementedError

    def value_dump(self, value: FinalValueT, context: DumpContext, /) -> Any:
        """Serializes the value to raw form.

        This is an abstract method that must be implemented by subclasses. This
        method is called by the library when a field is being dumped.

        The only time this method is called when the :meth:`Schema.dump` method
        is called. The returned value is the value included in serialized data.

        Parameters
        ----------
        value:
            The value to serialize.
        context: :class:`DumpContext`
            The serialization context.

        Returns
        -------
        The serialized value.
        """
        raise NotImplementedError
