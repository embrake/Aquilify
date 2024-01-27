"""
The module containing the logic for entities (tables) in AQUILIFY_SQLite_ORM
"""

from __future__ import annotations
from typing import TypeVar, Literal, Iterable, Optional, Callable, Iterator, TYPE_CHECKING
from pprint import pformat
from inspect import getmembers, isroutine
from .column import Column
from ..types import Type, IndexField
from ..statements import InsertInto, Set, CreateTable, Select, DeleteFrom, DropTable, CreateIndex
from ..wildcards import Wildcards
from ..foreign_key import ForeignKey

import typing

if TYPE_CHECKING:
    from ..backend.axsqlite3 import Sqlite3
    from ..backend import MySQLClient
    from .. import Result

from ..exception import FieldException, SQLExecutionError

TableT = TypeVar("TableT")
ColumnT = TypeVar("ColumnT", bound=Column)


def entity() -> Callable[[type[TableT]], Entity | TableT]:
    from ...connection import connection
    """
    The decorator used to declare a table in a schema.

    :param database: The database the table belongs to
    :param auto_create: Whether the table should be created in the database automatically, after it is declared
    :return: A wrapper function to convert a valid class into an Entity
    """

    def wrapper(table_: type[TableT]) -> Entity | type[TableT]:
        """
        The wrapper method in the decorator, which returns an Entity from a valid class.

        :param table_: The class to convert
        :return: An entity object with all the declared data
        """

        return Entity(table_, connection)

    return wrapper


class Entity:
    """
    The class containing the logic for Entities in AQUILIFY_SQLite_ORM.
    """

    __tablename__ = None

    class Meta:
        indexes = []

    def __init__(self, table_: Type[TableT], database: typing.Union[Sqlite3, MySQLClient], auto_create: bool = False):
        """
        :param table_: The decorated table class
        :param database: The database the table belongs to
        :param auto_create: Whether the table should be created in the database automatically, after it is declared
        """
        self.database = database
        self.auto_create = auto_create
        self.table_name = None
        self.columns = []
        self.indexes = []
        self.table_ = table_
        self.integrate_with_structure(table_)

    def integrate_with_structure(self, table_: Type[TableT]) -> None:
        """
        Creates and registers the table with the database as necessary and declared.

        :param table_: The decorated table class
        """

        self.database.add_table(self)
        self.__tablename__ = table_.__tablename__ if hasattr(table_, "__tablename__") else table_().__class__.__name__
        self.table_name = self.__tablename__
        for column in self.extract_columns(table_):
            if hasattr(self, column.name) and isinstance(self, self.Meta):
                raise NameError(f"Column name '{column.name}' cannot exist within a table") from None
            setattr(self, column.name, column)
            self.columns.append(column)
        if hasattr(table_, 'Meta') and hasattr(table_.Meta, 'indexes'):
            for index_cls in table_.Meta.indexes:
                if not isinstance(index_cls, IndexField):
                    raise FieldException("Index field must be pass on from IndexField cls")

                self.indexes.append(index_cls._rtx_001data)

        if self.auto_create:
            with self.database.connection():
                try:
                    self.create_table().execute()
                    self.create_indexes()
                except NameError:
                    raise FieldException("Cannot lazy-load foreign key with auto_create=True") from None

    def create_indexes(self) -> None:
        """
        Create indexes on the table based on the defined indexes in the Meta class.
        """
        for index_name, field_name, unique in self.indexes:
            self.create_index(index_name, field_name, unique)

    def __repr__(self) -> str:
        """
        An internal string representation of the table.

        :return: The columns of this table formatted as a string
        """
        return pformat(self.columns)

    def __str__(self) -> str:
        """
        A string representation of the table.

        :return: The name of the table
        """
        return self.table_name

    def extract_columns(self, table_: Type[TableT]) -> Iterator[Column]:
        """
        Extracts the declared columns from a valid class definition of a class in the schema.

        :param table_: The decorated table class
        :return: A generator which iterates each of the created Column objects
        """

        members = table_.__ordered_members__.items() if hasattr(table_, "__ordered_members__") else getmembers(table_)
        filtered_list = list(filter(lambda tup: tup[0] != 'Meta', members))
        for name, member in filtered_list:
            if name.startswith("__") or isroutine(member):
                continue
            yield self.amend_column(name, member)

    def amend_column(self, column_name: str, column_type: Type | type | ForeignKey) -> Column:
        """
        Converts a column as defined in the schema into a valid Column object.

        :param column_name: The defined name of the column
        :param column_type: The defined type of the column
        :return: The valid column object to be used by AQUILIFY_SQLite_ORM
        """
        if isinstance(column_type, type):  # Plain Key
            column_type = column_type()
        return Column(self, column_name, column_type)

    def sort(self, columns: Iterable[Column | Wildcards],
             base_columns_override: Optional[list[Column]] = None) -> list[Column]:
        """
        Returns the given columns in the correct order as per the schema.

        This is used in SELECT statements to ensure that the column order
        matches with the order of columns in the returned data.

        :param columns: The columns to sort
        :param base_columns_override: An override mechanism for the columns to base the ordering off of
        :return: The sorted list of columns
        """
        base_columns = self.columns if base_columns_override is None else base_columns_override
        if Wildcards.All in columns:
            return base_columns
        return sorted(columns, key=lambda column: base_columns.index(column))

    def set(self, data: dict[ColumnT, ColumnT.type.decoded_type]) -> Set:
        """
        Create a SET statement which runs on this table.

        :param data: The data to set into this table as a valid mapping
        :return: A Set statement object, which can be operated on further.
        """

        for column in data:
            if not column.is_nullable and data[column] is None:
                raise FieldException(f"Non-nullable column '{column.name}' passed NULL") from None
        return Set(self, data)

    def insert(self, data: dict[ColumnT, ColumnT.type.decoded_type]) -> InsertInto:
        """
        Create an INSERT INTO statement which runs on this table.

        :param data: The data to set into this table as a valid mapping
        :return: An InsertInto statement object, which can be operated on further.
        """

        for column in data:
            if not column.is_nullable and data[column] is None:
                if not column.is_auto_increment:
                    raise FieldException(f"Non-nullable column '{column.name}' passed NULL") from None
        for column in set(self.columns) - set(data):
            if not column.is_nullable and column.default is None:
                if not column.is_auto_increment:
                    raise FieldException(f"Non-nullable column '{column.name}' passed NULL") from None
            data[column] = None
        return InsertInto(self, data)

    def select(self, *columns: Column | Literal[Wildcards.All], distinct: bool = False) -> Select:
        """
        Create an SELECT statement which runs on this table.

        :param columns: The column(s) to select
        :param distinct: Whether to select only distinct (non-duplicate) data
        :return: A Select statement object, which can be operated on further.
        """

        if not "*" in columns and not isinstance(*columns, Column):
            raise SQLExecutionError("The data is not a successor of Columns Entity or Table!")

        if Wildcards.All in columns:
            columns = [Wildcards.All]
        return Select(self, list(columns), distinct=distinct)

    def delete(self) -> DeleteFrom:
        """
        Create an DELETE FROM statement which runs on this table.

        :return: A DeleteFrom statement object, which can be operated on further.
        """

        return DeleteFrom(self)

    def drop(self) -> DropTable:
        """
        Create an DROP TABLE statement which runs on this table.

        :return: A DropTable statement object, which can be operated on further.
        """

        return DropTable(self)

    def __getitem__(self, item: ColumnT.type.decoded_type) -> ColumnT.type.decoded_type:
        """
        Entity[data] --> data

        This is method which serves only to create a more declarative API - it can be used when inserting
        or setting data into a foreign key column, to explicitly show which table the data being input
        is intended to be coming from.

        :param item: The data in the primary key column of this table
        :return: The same data input as a parameter
        """

        return item

    def create_index(self, index_name: str, field_name: str, unique=False) -> Result:
        """
        Create an CREATE INDEX statement which runs on this table.

        :param unique:
        :param field_name:
        :param index_name: The name of the index
        :return: A CreateIndex statement object, which can be operated on further.
        """
        return CreateIndex(index_name, field_name, self, self.columns, unique=unique).execute()

    def create_table(self) -> CreateTable:
        """
        Create an CREATE TABLE statement which runs on this table.

        :return: A CreateTable statement object, which can be operated on further.
        """
        return CreateTable(self, self.columns)
