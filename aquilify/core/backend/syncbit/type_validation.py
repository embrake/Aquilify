from __future__ import annotations

from typing import (
    Any,
    Union,
    List,
    Set,
    Tuple,
    Literal,
    Dict,
    Mapping,
    get_origin,
    get_args,
)
from typing_extensions import Required, NotRequired, is_typeddict, get_type_hints
from .exceptions import SyncBitException

import types
import warnings
import sys
import collections.abc

__all__ = (
    'validate_types',
    'TypeValidationError',
)

PY_310 = sys.version_info >= (3, 10)

class TypeValidationError(SyncBitException):
    """An error raised when type validation fails.

    This is raised by :func:`aquilify.backends.syncbit.validate_types` method.

    Attributes
    ----------
    errors: Dict[:class:`str`, List[:class:`str`]]
        A dictionary with values representing list of type validation error
        messages for given key.
    """
    def __init__(self, errors: Dict[str, List[str]]) -> None:
        self.errors = errors
        super().__init__(f'Type validation failed for following keys: {", ".join(errors)}')


def validate_types(
        types: Mapping[str, type],
        values: Mapping[str, Any],
        *,
        ignore_extra: bool = False,
        ignore_missing: bool = False,
    ) -> None:

    """Validates the types of given values.

    The first parameter is the mapping with values representing the
    type for given key. Second parameter is mapping for the values for
    each key in the first parameter.

    For more information on supported types and limitations of this
    function, see the :ref:`guide-type-validation` section.

    Example::

        import typing
        from aquilify.backends import syncbit

        types = {
            'name': str,
            'id': typing.Union[int, str],
        }

        syncbit.validate_types(types, {'name': 'John', 'id': 2})  # no error

    Example error::

        try:
            syncbit.validate_types(types, {'name': 12})
        except syncbit.TypeValidationError as err:
            print(err.errors)
            # > {'name': ['Must be of type str'], 'id': ['This key is missing.']}

    Parameters
    ----------
    types: Mapping[:class:`str`, :class:`type`]
        The types to validate from.
    values: Mapping[:class:`str`, Any]
        The values to be validated.
    ignore_extra: :class:`bool`
        Whether to ignore extra keys in values mapping. Defaults to False.
    ignore_missing: :class:`bool`
        Whether to ignore missing keys in values mapping.

    Raises
    ------
    TypeValidationError
        The type validation failed.
    """
    key_errors: Mapping[str, Any] = {}
    validator = TypeValidator(dict(types))

    for key, value in values.items():
        if key not in validator.types and ignore_extra:
            continue
        validated, errors = validator.validate(key, value)
        if not validated:
            key_errors[key] = errors
        validator.types.pop(key, None)

    if not ignore_missing:
        for key in validator.types:
            key_errors[key] = ['This key is missing.']

    if key_errors:
        raise TypeValidationError(key_errors)


class TypeValidator:
    """A class that provides and handles type validation."""
    _warning_unsupported_type = "Validation of {type} type is not supported. No type validation will " \
                                "be performed for this type by SyncBit."

    _warnings_issued: Set[Any] = set()

    __slots__ = ('types',)

    def __init__(self, types: Dict[str, Any]) -> None:
        self.types = types

    @classmethod
    def _is_origin_union(cls, origin: Any) -> bool:
        return origin is Union or (PY_310 and origin is types.UnionType)

    @classmethod
    def _warn_unsupported(cls, tp: Any) -> None:
        from .configs import config  # circular import

        if tp in cls._warnings_issued or not config.warn_unsupported_types:
            return  # pragma: no cover

        cls._warnings_issued.add(tp)
        warnings.warn(
            cls._warning_unsupported_type.format(type=getattr(tp, '__name__', tp)),
            UserWarning,
            stacklevel=2,
        )

    @classmethod
    def _handle_type_any(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        return True, []

    @classmethod
    def _handle_type_typed_dict(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        if not isinstance(value, dict):
            return False, [f'Must be a {tp.__name__} dictionary']  # pragma: no cover

        typehints = get_type_hints(tp, include_extras=True)
        errors: List[str] = []

        for key, value in value.items():  # type: ignore
            try:
                attr_tp = typehints.pop(key)  # type: ignore
            except KeyError:
                errors.append(f'Invalid key {key!r}')
            else:
                validated, msg = cls._process_value(value, attr_tp)
                if not validated:
                    errors.append(f'Validation failed for {key!r}: {msg[0]}')

        for key, value in typehints.items():
            origin = get_origin(value)
            if (origin is None and not tp.__total__) or (origin is NotRequired):
                # either no marker and total=False -> field is not required
                # or NotRequired marker and total=True/False -> field is not required
                continue

            errors.append(f'Key {key!r} is required')

        return not errors, errors

    @classmethod
    def _handle_origin_required(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        args = get_args(tp)
        origin = get_origin(args[0])
        return cls._handle_origin(value, tp, origin)

    _handle_origin_not_required = _handle_origin_required

    @classmethod
    def _handle_origin_literal(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        args = get_args(tp)
        if value not in args:
            if len(args) == 1:
                return False, [f'Value must be equal to {args[0]!r}']
            return False, [f'Value must be one of: {", ".join(repr(v) for v in args)}']
        return True, []

    @classmethod
    def _handle_origin_union(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        args = get_args(tp)
        for tp in args:
            validated, _ = cls._process_value(value, tp)
            if validated:
                return True, []
        return False, [f'Type of {value!r} ({type(value).__name__}) is not compatible with types ({", ".join(tp.__name__ for tp in args)})']

    @classmethod
    def __process_mapping(cls, value: Any, tp: Any, name: str, origin: Any) -> Tuple[bool, List[str]]:
        if not isinstance(value, origin):
            return False, [f'Must be a valid {name.lower()}']

        args = get_args(tp)
        errors: List[str] = []
        validated = True
        ktp = args[0]
        vtp = args[1]

        for idx, (k, v) in enumerate(value.items()):  # type: ignore
            item_validated, fail_msg = cls._process_value(k, ktp)
            if not item_validated:
                validated = False
                errors.append(f'{name} key at index {idx}: {fail_msg[0]}')
            else:
                item_validated, fail_msg = cls._process_value(v, vtp)
                if not item_validated:
                    validated = False
                    errors.append(f'{name} value for key {k!r}: {fail_msg[0]}')

        return validated, errors

    @classmethod
    def _handle_origin_dict(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        return cls.__process_mapping(value, tp, 'Dictionary', dict)

    @classmethod
    def _handle_origin_mapping(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        return cls.__process_mapping(value, tp, 'Mapping', collections.abc.Mapping)  # pragma: no cover

    @classmethod
    def _handle_origin_list(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        if not isinstance(value, list):
            return False, [f'Must be a valid list']

        args = get_args(tp)
        errors: List[str] = []
        validated = True
        vtp = args[0]

        for idx, v in enumerate(value):  # type: ignore
            item_validated, fail_msg = cls._process_value(v, vtp)
            if not item_validated:
                validated = False
                errors.append(f'Sequence item at index {idx}: {fail_msg[0]}')

        return validated, errors

    @classmethod
    def _handle_origin_set(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        if not isinstance(value, set):
            return False, [f'Must be a valid set']

        args = get_args(tp)
        errors: List[str] = []
        validated = True
        vtp = args[0]

        for v in value:  # type: ignore
            item_validated, fail_msg = cls._process_value(v, vtp)
            if not item_validated:
                validated = False
                errors.append(f'Set includes an invalid item: {fail_msg[0]}')

        return validated, errors

    @classmethod
    def _handle_origin_tuple(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        if not isinstance(value, tuple):
            return False, [f'Must be a valid tuple']

        args = get_args(tp)
        errors: List[str] = []
        validated = True

        if len(args) == 2 and args[1] is Ellipsis:
            # Tuple[T, ...] -> tuple of any length of type T
            vtp = args[0]
            for idx, v in enumerate(value):  # type: ignore
                item_validated, fail_msg = cls._process_value(v, vtp)
                if not item_validated:
                    validated = False
                    errors.append(f'Tuple item at index {idx}: {fail_msg[0]}')
        else:
            for idx, tp in enumerate(args):
                try:
                    v = value[idx]  # type: ignore
                except IndexError:
                    validated = False
                    errors.append(f'Tuple length must be {len(args)} (current length: {len(value)})')  # type: ignore
                    break
                else:
                    item_validated, fail_msg = cls._process_value(v, tp)
                    if not item_validated:
                        validated = False
                        errors.append(f'Tuple item at index {idx}: {fail_msg[0]}')  # pragma: no cover

        return validated, errors

    @classmethod
    def _handle_origin_sequence(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        value_tp = type(value)
        if value_tp is list:
            return cls._handle_origin_list(value, tp)
        if value_tp is set:
            return cls._handle_origin_set(value, tp)
        if value_tp is tuple:
            return cls._handle_origin_tuple(value, tp)

        return cls._handle_origin_list(value, tp)  # pragma: no cover

    @classmethod
    def _process_struct(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        origin = get_origin(tp)

        if origin is collections.abc.Sequence:
            return cls._handle_origin_sequence(value, tp)
        if origin is dict:
            return cls._handle_origin_dict(value, tp)
        if origin is list:
            return cls._handle_origin_list(value, tp)
        if origin is set:
            return cls._handle_origin_set(value, tp)
        if origin is tuple:
            return cls._handle_origin_tuple(value, tp)

        if origin is not None:  # pragma: no cover
            cls._warn_unsupported(origin)

        return True, []  # pragma: no cover

    @classmethod
    def _handle_origin(cls, value: Any, tp: Any, origin: Any) -> Tuple[bool, List[str]]:
        if cls._is_origin_union(origin):
            return cls._handle_origin_union(value, tp)
        if origin is Required:
            return cls._handle_origin_required(value, tp)
        if origin is NotRequired:
            return cls._handle_origin_not_required(value, tp)
        if origin in (list, set, dict, tuple, collections.abc.Sequence):
            return cls._process_struct(value, tp)
        if origin is Literal:
            return cls._handle_origin_literal(value, tp)

        if origin is not None:
            cls._warn_unsupported(origin)

        return True, []

    @classmethod
    def _process_value(cls, value: Any, tp: Any) -> Tuple[bool, List[str]]:
        if tp is Any:
            return cls._handle_type_any(value, tp)

        origin = get_origin(tp)

        if origin is None:
            if is_typeddict(tp):
                return cls._handle_type_typed_dict(value, tp)
            return isinstance(value, tp), [f'Must be of type {tp.__name__}']

        return cls._handle_origin(value, tp, origin)

    def validate(self, key: str, value: Any) -> Tuple[bool, List[str]]:
        try:
            tp = self.types[key]
        except KeyError:
            return False, ['Invalid key']
        validated, errors = self._process_value(value, tp)
        return validated, errors
