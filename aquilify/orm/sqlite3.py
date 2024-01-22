import sqlite3

from .filters import MagicFilter
from .column import Column, ColumnType
from .constants import Types
from .exceptions import SessionExecuteError
from .table import Table, DynamicTable
from .utils.dict_factory import dict_factory
from .connection import DatabaseConnectionManager
from .transactions import TransactionContextManager, IsolationLevel

from typing import Callable, Union, Type


class Typing(object):

    """
    Namespace with type hints.
    """

    AnyTable = Union[MagicFilter, DynamicTable, Table, Type[Table]]
    NamespaceTable = Union[DynamicTable, Type[Table]]
    AnyColumn = Union[Column, ColumnType]

class Sqlite3:
    def __init__(self, path: str) -> None:
        self.path = path
        
    def get_path(self) -> str:
        return self.path
    
    def __str__(self) -> str:
        return self.path

class Session(object):
    def __init__(self, tables: list[Typing.NamespaceTable] = None, **kwargs) -> None:

        """
        Creates a new session to work with the database.

        :param path: Path to the database
        :param tables: List of tables to be created during session initialization
        :param kwargs: Other options for opening a database [ More details in `sqlite3.connect(...)` ]
        """
        
        self._connection = DatabaseConnectionManager()._get_connection()
        self._database = sqlite3.connect(self._connection.get_path(), **kwargs)
        self._tables = tables or []

        for table in self._tables:
            self.create(table)

    def create(self, table: Typing.NamespaceTable) -> None:

        """
        Creates a new table in the database.

        :param table: Table or dynamic table
        :return: Nothing
        """

        self._database.execute(f"CREATE TABLE IF NOT EXISTS {table.__tablename__} "
                               f"({', '.join([column.serialize() for column in table.columns().values()])})")
        self._database.commit()

    def clear(self, table: Typing.NamespaceTable) -> None:

        """
        Clears the selected table.

        :param table: Table or dynamic table
        :return: Nothing
        """

        self._database.execute(
            f"DELETE FROM {table.__tablename__}"
        )
        self._database.commit()

    def drop(self, table: Typing.NamespaceTable) -> None:

        """
        Completely removes the table from the database.

        :param table: Table or dynamic table
        :return: Nothing
        """

        self._database.execute(
            f"DROP TABLE IF EXISTS {table.__tablename__}"
        )
        self._database.commit()

    def insert(self, table: Table, replace: bool = False) -> None:

        """
        Adds a new row to the table.

        :param table: Initialized table object
        :param replace: Will replace an existing row
        :return: Nothing
        """

        values = table.values
        
        try:

            self._database.execute(
                f"INSERT {'OR REPLACE' if replace else ''} INTO {table.__tablename__} ({', '.join(values.keys())}) "
                f"VALUES ({', '.join(['?'] * len(values))})", list(values.values())
            )
            self._database.commit()
            return True
        except Exception:
            return False
        
    def update(self, data: Typing.AnyTable, table: Table) -> None:

        """
        Updates the selected rows in the table.

        :param data: Initialized table object
        :param table: Any type of table or magic filter
        :return: Nothing
        """

        if not isinstance(data, (MagicFilter, DynamicTable, Table, type(Table))):
            raise SessionExecuteError("The data is not a successor of MagicFilterData or Table!")

        update = ", ".join([f"{item} = ?" for item in table.values.keys()])

        if isinstance(data, (DynamicTable, Table, type(Table))):
            self._database.execute(
                f"UPDATE {data.__tablename__} SET {update}", (*table.values.values(), )
            )
            return self._database.commit()

        self._database.execute(
            f"UPDATE {data.parameters['table']} SET {update} WHERE {data.query}",
            (*table.values.values(), *data.variables)
        )
        return self._database.commit()

    def delete(self, data: Typing.AnyTable) -> None:

        """
        Removes all rows that match the specified conditions

        :param data: Any type of table or magic filter
        :return: Nothing
        """

        if not isinstance(data, (MagicFilter, DynamicTable, Table, type(Table))):
            raise SessionExecuteError("The data is not a successor of MagicFilterData or Table!")

        if isinstance(data, (DynamicTable, Table, type(Table))):
            self._database.execute(
                f"DELETE FROM {data.__tablename__}"
            )
            return self._database.commit()

        self._database.execute(
            f"DELETE FROM {data.parameters['table']} WHERE {data.query}", data.variables
        )
        return self._database.commit()

    def exists(self, data: Typing.AnyTable) -> bool:

        """
        Checks for the existence of rows satisfying given conditions.

        :param data: Any type of table or magic filter
        :return: Boolean
        """

        if not isinstance(data, (MagicFilter, DynamicTable, Table, type(Table))):
            raise SessionExecuteError("The data is not a successor of MagicFilterData or Table!")

        if isinstance(data, (DynamicTable, Table, type(Table))):
            return not not self._database.execute(
                f"SELECT EXISTS(SELECT * FROM {data.__tablename__})"
            ).fetchone()[-1]

        return not not self._database.execute(
            f"SELECT EXISTS(SELECT * FROM {data.parameters['table']} WHERE {data.query})", data.variables
        ).fetchone()[-1]

    def select(self, data: Typing.AnyTable, items: list[Typing.AnyColumn] = None) -> list[dict[str, object]]:

        """
        Selects certain data from a table that satisfies given conditions.

        :param data: Any type of table or magic filter
        :param items: Elements to select
        :return: List of tuples
        """

        if not isinstance(data, (MagicFilter, DynamicTable, Table, type(Table))):
            raise SessionExecuteError("The data is not a successor of MagicFilterData or Table!")

        select = "*" if not items else ", ".join(
            [f"{item.table}.{item.name}" for item in items]
        )

        if isinstance(data, (DynamicTable, Table, type(Table))):
            return dict_factory(self._database.execute(
                f"SELECT {select} FROM {data.__tablename__}"
            ))

        return dict_factory(self._database.execute(
            f"SELECT {select} FROM {data.parameters['table']} WHERE {data.query}", data.variables
        ))

    def count(self, data: Typing.AnyTable) -> int:

        """
        Counts the number of rows satisfying given conditions.

        :param data: Any type of table or magic filter
        :return: Integer
        """

        if not isinstance(data, (MagicFilter, DynamicTable, Table, type(Table))):
            raise SessionExecuteError("The data is not a successor of MagicFilterData or Table!")

        if isinstance(data, (DynamicTable, Table, type(Table))):
            return self._database.execute(
                f"SELECT COUNT(*) FROM {data.__tablename__}"
            ).fetchone()[-1]

        return self._database.execute(
            f"SELECT COUNT(*) FROM {data.parameters['table']} WHERE {data.query}", data.variables
        ).fetchone()[-1]

    def execute(self, sql: str, parameters: tuple | object = ()) -> sqlite3.Cursor:

        """
        Execute sql query. [ More details in `sqlite3.connect(...)` ]

        :param sql: Sql query
        :param parameters: Query parameters
        :return: SQLite database cursor
        """

        return self._database.execute(sql, parameters)
    
    def execute_many(self, sql: str, parameters: list[tuple] = ()) -> sqlite3.Cursor:
        """
        Execute an SQL query multiple times with different sets of parameters.

        :param sql: SQL query
        :param parameters: List of tuples representing query parameters for multiple executions
        :return: Nothing
        """
        if not isinstance(parameters, list) or not all(isinstance(param, tuple) for param in parameters):
            raise SessionExecuteError("Invalid parameters. Expecting a list of tuples.")

        try:
            with self._database:
                cursor = self._database.cursor()
                cursor.executemany(sql, parameters)
        except sqlite3.Error as e:
            raise SessionExecuteError(f"Error executing multiple queries: {e}")
        
    def fetch_all(self, sql: str, parameters: tuple | object = (), columns: list[str] | None = None) -> dict[str, object] | None:
        """
        Execute an SQL query and fetch all results.

        :param sql: SQL query
        :param parameters: Query parameters
        :param columns: Optional list of column names to fetch
        :return: List of dictionaries representing the rows
        """
        try:
            cursor = self._database.execute(sql, parameters)
            if columns:
                return dict_factory(dict(zip(columns, row)) for row in cursor)
            return dict_factory(cursor)
        except sqlite3.Error as e:
            raise SessionExecuteError(f"Error fetching all rows: {e}")
        
    def transaction(self, isolation_level=IsolationLevel.DEFERRED):
        """Context manager for transactions."""
        return TransactionContextManager(self._database, isolation_level)
    
    def commit(self):
        
        """
        Commits the changes to the database and closes the connection.

        If an error occurs during commit, it rolls back changes and closes the connection.
        """
        
        try:
            self._database.commit()
        except sqlite3.Error:
            self._database.rollback() 
        finally:
            self._database.close()
            
    def close(self) -> None:

        """
        Will close the session.

        :return: Nothing
        """

        self._database.close()

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.close()


def create_session(**kwargs) -> Callable[[], Session]:

    """
    Creates all tables in the selected database.

    :param path: Path to the database
    :param tables: List of tables to be created during session initialization
    :param kwargs: Other options for opening a database [ More details in `sqlite3.connect(...)` ]
    :return: Local session with given parameters
    """

    with Session(**kwargs) as _:
        return lambda: Session(**kwargs)