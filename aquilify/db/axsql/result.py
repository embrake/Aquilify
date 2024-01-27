"""
A module containing the logic for AQUILIFY_SQLite_ORM Result objects.
"""

from __future__ import annotations
from typing import Iterator, TypeVar, TYPE_CHECKING, Any
from sqlite3 import Cursor
if TYPE_CHECKING:
    from .entity import Column
    ColumnT = TypeVar("ColumnT", bound=Column)

from .dict_factory import dict_factory

class Result:
    """
    The class that contains result data from any executed AQUILIFY_SQLite_ORM queries.
    """

    UNKNOWN_COLUMN = "?"

    def __init__(self, columns: list[Column], result: Cursor, indeterminate: bool = False):
        self.columns = columns
        self.result = result
        self.indeterminate_columns = indeterminate

    def __iter__(self) -> Iterator[dict[ColumnT, ColumnT.type.decoded_type] | tuple]:
        """
        Allows for records to be accessed from a Result via simple iteration (e.g. for record in result).

        :return: An iterator containing each record, usually as a mapping ({column: data})
        """
        for record in self.result:
            if self.indeterminate_columns:
                yield record
            else:
                yield {column: column.type.decode(field) for column, field in zip(self.columns, record)}
    
    @property          
    def factory(self) -> list[dict[str, object]]:
        return dict_factory(self.result)
    
    @property
    def lastrowid(self) -> int | None:
        if not self.result.lastrowid == 0:
            return self.result.lastrowid
        return self.result.fetchone()[0]
    
    @property
    def description(self) -> tuple[tuple[str, None, None, None, None, None, None], ...] | Any:
        return self.result.description
    
    @property
    def row_factory(self) -> object | None:
        return self.result.row_factory
    
    @property
    def fetchone(self) -> Any:
        return self.result.fetchone()
    
    @property
    def fetchall(self) -> list[Any]:
        return self.result.fetchall()