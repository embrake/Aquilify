from __future__ import annotations

from typing import TYPE_CHECKING, Any
from contextvars import ContextVar

if TYPE_CHECKING:
    from .contexts import _BaseValueContext
    from .schema import Schema

__all__ = (
    'MissingType',
    'MISSING',
    'current_context',
    'current_field_key',
    'current_schema',
)


class MissingType:
    """Type for representing unaltered/default/missing values.

    Used as sentinel to differentiate between default and None values.
    utils.MISSING is a type safe instance of this class.
    """
    def __repr__(self) -> str:
        return '...'  # pragma: no cover

    def __bool__(self) -> bool:
        return False  # pragma: no cover


MISSING: Any = MissingType()


### Context variables ###

current_context: ContextVar[_BaseValueContext] = ContextVar('current_context')
current_field_key: ContextVar[str] = ContextVar('current_field_key')
current_schema: ContextVar[Schema] = ContextVar('current_schema')
