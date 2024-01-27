from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Dict,
    Any,
    Mapping,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)
from typing_extensions import Self
from .contexts import SchemaContext, LoadContext, DumpContext
from .utils import MISSING, current_field_key, current_context, current_schema
from .exceptions import FieldError, FieldNotSet, FrozenError
from .configs import config, SchemaConfig

import collections.abc
import inspect
import copy

if TYPE_CHECKING:
    from .fields.base import Field

__all__ = (
    'Schema',
)

T = TypeVar('T')

def _schema_repr(self: Schema) -> str:
    attrs = ', '.join((f'{name}={value}' for name, value in self._field_values.items()))  # pragma: no cover
    return f'{self.__class__.__name__}({attrs})'  # pragma: no cover


class _SchemaMeta(type):
    def __new__(cls, clsname: str, bases: Tuple[type, ...], attrs: Dict[str, Any]):
        config = SchemaConfig
        found = False
        for _, value in attrs.items():
            # Search for Config subclass in the class being created
            if inspect.isclass(value) and issubclass(value, SchemaConfig):
                found = True
                config = value
                break

        if not found:
            # If class doesn't have a Config defined, look it up in
            # the bases of class
            for base in bases:
                if issubclass(base, Schema) and hasattr(base, '__config__'):
                    config = base.__config__

        if config.slotted:
            attrs.setdefault('__slots__', ())

        attrs['__config__'] = config
        return super().__new__(cls, clsname, bases, attrs)


class Schema(metaclass=_SchemaMeta):
    """The base class for all schemas.

    All user defined schemas must inherit from this class. When initializing
    the raw data is passed in form of dictionary or other mapping as a
    positional argument.

    Parameters
    ----------
    data: Mapping[:class:`str`, Any]
        The raw data to initialize the schema with.
    state:
        The initial value for :attr:`SchemaContext.state` attribute. This can
        be used to store and propagate custom stateful information which may be
        useful in deserialization of data.
    ignore_extra: :class:`bool`
        Whether to ignore extra (invalid) fields in the data.

        This parameter overrides the :attr:`SchemaConfig.ignore_extra`
        configuration.
    """
    __fields__: Dict[str, Field[Any, Any]]
    __load_fields__: Dict[str, Field[Any, Any]]
    __config__: Type[SchemaConfig] = SchemaConfig

    __slots__ = (
        '_field_values',
        '_context',
    )

    def __init__(
            self,
            data: Mapping[str, Any],
            /,
            *,
            state: Any = None,
            ignore_extra: bool = MISSING,
        ):

        if not isinstance(data, collections.abc.Mapping):
            raise TypeError(f'data must be a mapping, not {type(data)}')

        token = current_schema.set(self)
        try:
            self._field_values: Dict[str, Any] = {}
            self._context = SchemaContext(self, state=state)
            self._prepare_from_data(data, ignore_extra=ignore_extra)
        finally:
            current_schema.reset(token)

    def __init_subclass__(cls) -> None:
        # circular import
        from .fields.base import Field

        if hasattr(cls, '__fields__'):
            # When a schema is subclassed, the fields have to be copied so
            # the parent schema's fields are not modified
            cls.__fields__ = cls.__fields__.copy()
            cls.__load_fields__ = cls.__load_fields__.copy()
        else:
            cls.__fields__ = {}
            cls.__load_fields__ = {}

        members = vars(cls).copy()
        for name, member in members.items():
            if isinstance(member, Field):
                member._bind(name, cls)
                cls.__fields__[name] = member  # type: ignore
                cls.__load_fields__[member.load_key] = member  # type: ignore
            elif callable(member) and hasattr(member, '__validator_field__'):
                field = member.__validator_field__
                if isinstance(field, str):
                    try:
                        field = members[field]
                    except KeyError:  # pragma: no cover
                        pass
                if not isinstance(field, Field):
                    raise TypeError(f'Validator {member.__name__} got an unknown field {field}')  # pragma: no cover

                field.add_validator(member)

        if cls.__config__.add_repr and '__repr__' not in members:
            cls.__repr__ = _schema_repr  # type: ignore

    def _prepare_from_data(self, data: Mapping[str, Any], *, ignore_extra: bool = MISSING) -> None:
        data = self.preprocess_data(data)
        if not isinstance(data, collections.abc.Mapping):
            raise TypeError(f'{self.__class__.__qualname__}.preprocess_data must return a ' \
                            f'mapping, not {type(data)}')

        if ignore_extra is MISSING:
            ignore_extra = self.__config__.ignore_extra

        fields = self.__load_fields__.copy()
        validators: List[Tuple[Field[Any, Any], Any, LoadContext, bool]] = []
        errors: List[FieldError] = []

        for key, value in data.items():
            token = current_field_key.set(key)
            try:
                field = fields.pop(key)
            except KeyError:
                if not ignore_extra:
                    errors.append(FieldError(f'Invalid or unknown field.'))
            else:
                # See comment in _process_field_values() for explanation on how
                # validators are handled.
                process_errors = self._process_field_value(field, value, validators)
                errors.extend(process_errors)
            finally:
                current_field_key.reset(token)

        for key, field in fields.items():
            token = current_field_key.set(key)
            try:
                if field.required:
                    errors.append(field._call_format_error(field.ERR_FIELD_REQUIRED, self, MISSING))
                if field._default is not MISSING:
                    self._field_values[field._name] = field._default(self._context, field) \
                                                      if callable(field._default) else field._default
            finally:
                current_field_key.reset(token)

        for field, value, context, raw in validators:
            ctx_token = current_context.set(context)
            field_token = current_field_key.set(field.load_key)
            schema_token = current_schema.set(self)
            try:
                errors.extend(field._run_validators(value, context, raw=raw))
            finally:
                current_context.reset(ctx_token)
                current_field_key.reset(field_token)
                current_schema.reset(schema_token)

        if errors:
            raise config.validation_error_cls(errors)

        self._context._initialized = True
        self.__schema_post_init__()

    def _process_field_value(
            self,
            field: Field[Any, Any],
            value: Any,
            validators: Optional[List[Tuple[Field[Any, Any], Any, LoadContext, bool]]] = None,
        ) -> List[FieldError]:

        # A little overview of how external validations are handled by
        # this method:
        #
        # If the validators parameter is not provided (None), the validators
        # are ran directly and any errors raised by them are appended to the
        # list of returned errors. (e.g. Field.__set__ does this)
        #
        # In contrary case, if the validators parameter is provided, it is a
        # list of 4 element tuples: the field to validate, the value validated,
        # the load context, and a boolean indicating whether the validation is
        # performed by raw validators. This validation data appended to the given
        # validators list by this method and the validators are ran lazily later
        # using this data. This is done when validators are ran on initialization
        # of schema. (e.g. Schema._prepare_from_data does this)

        name = field._name
        lazy_validation = validators is not None
        errors: List[FieldError] = []
        validator_errors: List[FieldError] = []
        context = LoadContext(field=field, value=value, schema=self)
        token = current_context.set(context)

        if field._raw_validators and lazy_validation:
            validators.append((field, value, context, True))

        if value is None:
            if field.none:
                self._field_values[name] = None
            else:
                errors.append(field._call_format_error(field.ERR_NONE_DISALLOWED, self, None))
            return errors

        if not lazy_validation:
            validator_errors.extend(field._run_validators(value, context, raw=True))
        try:
            final_value = field.value_load(value, context)
        except (ValueError, AssertionError, FieldError) as err:
            if not isinstance(err, FieldError):
                err = FieldError._from_standard_error(err, schema=self, field=field, value=value)
            errors.append(err)
        else:
            if not lazy_validation:
                validator_errors.extend(field._run_validators(final_value, context, raw=False))
            else:
                validators.append((field, final_value, context, False))
            if not validator_errors:
                self._field_values[name] = final_value
            errors.extend(validator_errors)
        finally:
            current_context.reset(token)

        return errors

    def _get_field(self, name: str) -> Field[Any, Any]:
        try:
            return self.__fields__[name]
        except KeyError:
            try:
                return self.__load_fields__[name]
            except KeyError:
                raise RuntimeError(f'Invalid field name {name!r}') from None

    def preprocess_data(self, data: Mapping[str, Any], /) -> Mapping[str, Any]:
        """Preprocesses the input data.

        This method is called before the raw data is serialized. The
        processed data must be returned. By default, this method returns
        the data as-is.

        .. warning::

            The ``data`` parameter to schema constructor is passed directly
            to this method without any validation so the data may be invalid.

        Parameters
        ----------
        data: Mapping[:class:`str`, Any]
            The input data.

        Returns
        -------
        Mapping[:class:`str`, Any]
            The processed data.
        """
        return data

    def __schema_post_init__(self):
        """The post initialization hook.

        This method is called when the schema is done initializing. This
        method is meant to be overriden by subclasses and does nothing
        by default.

        .. versionadded:: 1.1
        """

    @property
    def context(self) -> SchemaContext:
        """The context for this schema.

        Schema context holds the information about schema and its state.

        :type: :class:`SchemaContext`
        """
        return self._context

    def copy(self) -> Self:
        """Copies the current schema.

        Returns
        -------
        :class:`Schema`
            The copied schema instance.
        """
        schema = copy.copy(self)
        schema._field_values = self._field_values.copy()
        schema._context = self._context._copy(schema=schema)
        return schema

    def get_value_for(self, field_name: str, default: Any = MISSING, /) -> Any:
        """Returns the value for a field.

        If field has no value set, a :class:`ValueError` is raised
        unless a ``default`` is provided.

        Parameters
        ----------
        field_name: :class:`str`
            The name of field to get value for. This can either be field (attribute)
            name or the value of :attr:`fields.Field.load_key`.
        default:
            The default value to return if field has no value.

        Returns
        -------
        The field value.

        Raises
        ------
        RuntimeError
            Invalid field name.
        FieldNotSet
            Field value is not set.
        """
        field = self._get_field(field_name)
        try:
            return self._field_values[field._name]
        except KeyError:
            if default is not MISSING:
                return default
            raise FieldNotSet(field, self, field_name) from None

    def update(self, data: Mapping[str, Any], /, *, ignore_extra: bool = MISSING) -> None:
        """Updates the schema with the given data.

        If the update fails i.e one or more fields fail to validate, the
        schema's state (field values) is rolled back to previous state.

        Parameters
        ----------
        data: Mapping[:class:`str`, Any]
            The data to update with.
        ignore_extra: :class:`bool`
            Whether to ignore extra (invalid) fields in the data.

            This parameter overrides the :attr:`SchemaConfig.ignore_extra`
            configuration.

        Raises
        ------
        FrozenError
            The schema is read only or one of the fields attempted to
            be updated is read only and cannot be updated.
        ValidationError
            The validation failed.
        """
        if self.__config__.frozen:
            raise FrozenError(self)

        if ignore_extra is MISSING:
            ignore_extra = self.__config__.ignore_extra

        fields = self.__load_fields__
        errors: List[FieldError] = []
        old_values = self._field_values.copy()

        for key, value in data.items():
            token = current_field_key.set(key)
            try:
                field = fields[key]
            except KeyError:
                if not ignore_extra:
                    errors.append(FieldError(f'Invalid or unknown field.'))
            else:
                if field.frozen:
                    raise FrozenError(field)
                errors.extend(self._process_field_value(field, value))
            finally:
                current_field_key.reset(token)

        if errors:
            # fallback to original state in case update fails
            self._field_values = old_values
            raise config.validation_error_cls(errors)

    def dump(self, *, include: Sequence[str] = MISSING, exclude: Sequence[str] = MISSING) -> Dict[str, Any]:
        """Serializes the schema to raw form.

        The returned value is serialized data in dictionary form. The
        ``include`` and ``exclude`` parameters are mutually exclusive.

        Parameters
        ----------
        include: Sequence[:class:`str`]
            The fields to include in the returned data.
        exclude: Sequence[:class:`str`]
            The fields to exclude from the returned data.

        Returns
        -------
        Dict[:class:`str`, Any]
            The serialized data.

        Raises
        ------
        TypeError
            Both include and exclude provided.
        ValidationError
            Validation failed while serializing one or more fields.
        """
        fields = set(self.__fields__.keys())
        if include is not MISSING and exclude is not MISSING:
            raise TypeError('include and exclude are mutually exclusive parameters.')
        if include is not MISSING:
            fields = fields.intersection(set(include))
        if exclude is not MISSING:
            fields = fields.difference(set(exclude))

        current_schema.set(self)
        out: Dict[str, Any] = {}
        errors: List[FieldError] = []

        for name in fields:
            field = self.__fields__[name]
            try:
                value = self._field_values[name]
            except KeyError:  # pragma: no cover
                continue

            context = DumpContext(
                schema=self,
                field=field,
                value=value,
                included_fields=fields,
            )
            field_token = current_field_key.set(field.load_key)
            context_token = current_context.set(context)
            try:
                out[field.dump_key] = field.value_dump(value, context)
            except (ValueError, AssertionError, FieldError) as err:
                if not isinstance(err, FieldError):
                    err = FieldError._from_standard_error(err, schema=self, field=field, value=value)
                errors.append(err)
            finally:
                current_field_key.reset(field_token)
                current_context.reset(context_token)

        if errors:
            raise config.validation_error_cls(errors)

        return out
