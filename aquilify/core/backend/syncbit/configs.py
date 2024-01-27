from __future__ import annotations


from typing import Callable, Any, Type, Generic, TypeVar, Dict, Optional
from .exceptions import ValidationError

import os

__all__ = (
    'config',
    'GlobalConfig',
    'SchemaConfig',
)

_T = TypeVar('_T')
_SPHINX_BUILD = os.environ.get('SPHINX_BUILD', False)


class _ConfigOption(Generic[_T]):
    __slots__ = (
        '_default',
        '_func',
        '_name',
        '_setter',
        '__doc__',
    )

    def __init__(self, func: Callable[[GlobalConfig], _T]) -> None:
        self._default = func(None)  # type: ignore
        self._func = func
        self._name = func.__name__
        self.__doc__ = func.__doc__
        self._setter = None

    def setter(self, func: Callable[[GlobalConfig, Any], _T]) -> None:
        self._setter = func

    def __get__(self, instance: Optional[GlobalConfig], owner: Type[GlobalConfig]) -> _T:
        if instance is None:
            # Sphinx needs access to the self.__doc__ attribute to properly document
            # the cfg_option decorated function. This is, unfortunately, not possible
            # without this hacky special casing. If sphinx is building, we need to return
            # self so sphinx can access __doc__. Otherwise, it would use __doc__ of self._default
            if _SPHINX_BUILD:
                return self  # type: ignore  # pragma: no cover
            return self._default
        try:
            return instance._values[self._name]
        except KeyError:  # pragma: no cover
            return self._default

    def __set__(self, instance: GlobalConfig, value: _T) -> None:
        if self._setter:
            value = self._setter(instance, value)

        instance._values[self._name] = value

def cfg_option(func: Callable[[GlobalConfig], _T]) -> _ConfigOption[_T]:
    return _ConfigOption(func)


class GlobalConfig:
    """The global configuration of SyncBit.

    Global configuration applies to globally to each defined schema instead
    of being per-schema. The instance of this class is availabe as :data:`syncbit.config`.
    The attributes of this class are available config options that can be customized.

    For more information on working with configurations, see user guide :ref:`guide-config`.
    """
    __slots__ = (
        '_values',
    )

    __config_options__ = (
        'validation_error_cls',
    )

    def __init__(
            self,
            *,
            warn_unsupported_types: bool = True,
            validation_error_cls: Type[ValidationError] = ValidationError,
        ) -> None:

        self._values: Dict[str, Any] = {}

        self.warn_unsupported_types = warn_unsupported_types
        self.validation_error_cls = validation_error_cls

    @cfg_option
    def validation_error_cls(self) -> Type[ValidationError]:
        """The :class:`ValidationError` exception class which will be raised on validation failure.

        :type: Type[:class:`ValidationError`]
        """
        return ValidationError

    @validation_error_cls.setter
    def _set_validation_error_cls(self, value: Type[ValidationError]):
        if not issubclass(value, ValidationError):
            raise TypeError('validation_error_cls must be a subclass of ValidationError')
        return value

    @cfg_option
    def warn_unsupported_types(self) -> bool:
        """Whether to warn about usage of unsupported types in type validation.

        This dictates whether to issue a warning if a type is used in a type
        expression in fields involving type validation that cannot be validated
        by SyncBit.

        .. versionadded:: 1.1

        :type: :class:`bool`
        """
        return True

    @warn_unsupported_types.setter
    def _set_warn_unsupported_types(self, value: bool):
        if not isinstance(value, bool):  # pragma: no cover
            raise TypeError('warn_unsupported_types must be a boolean')
        return value  # pragma: no cover


config = GlobalConfig()
"""The global configuration of SyncBit."""


class SchemaConfig:
    """The configuration for a schema.

    This is a base class for defining configuration of a schema. In order to
    define configuration for a schema, this class is subclassed inside a :class:`Schema`::

        class User(syncbit.Schema):
            id = fields.Integer()

            class Config(syncbit.SchemaConfig):
                ...  # override config options
    """
    add_repr = True
    """Whether to add a :meth:`__repr__` for detailing schema fields when printed."""

    slotted = True
    """Whether to add a :attr:`__slots__` to the schema class.

    This could improve the performance but also limits the ability to
    set any extra attributes on the schema. This is ignored when the
    schema has already defined ``__slots__``.
    """

    ignore_extra = False
    """Whether to ignore extra (invalid) field names when initializing schema.

    This configuration can be overriden per initialization/update using the
    ``ignore_extra`` parameter in :class:`Schema` initialization.
    """

    frozen = False
    """Whether the schema is read only.

    When set to True, the schema cannot be updated once initialized. Defaults
    to False.
    """
