from typing import Optional, Generator, List
from dataclasses import dataclass, field
from contextlib import contextmanager

try:
    import pymysql.cursors
except ModuleNotFoundError:  # pragma: nocover
    pymysql.cursors = None
    
from aquilify.db.axsql.entity import Entity 
from aquilify.db.axsql.statements import Statement
from aquilify.db.axsql.result import Result
from aquilify.db.axsql.exception import ModelException, ConnectionError, SQLExecutionError

@dataclass(eq=True, slots=True)
class MySQLClient:
    host: str
    user: str
    password: str
    database: str
    port: int = 3306
    output: bool = False
    auto_execute: bool = False
    charcet = "utf8mb4"
    collate = "utf8mb4_unicode_ci"
    
    foreign_keys = True
    tables: set[Entity] = field(init=False, default_factory=set)
    db_connection: Optional[pymysql.connections.Connection] = field(init=False, default=None)
    cursor: Optional[pymysql.cursors.Cursor] = field(init=False, default=None)
    connections: list[bool] = field(init=False, default_factory=list)

    def add_table(self, table: Entity) -> None:
        self.tables.add(table)

    @property
    def commit_mode(self) -> bool:
        return self.connections[-1]

    @property
    def connected(self) -> bool:
        return bool(self.connections)

    def connect(self, commit: bool = True) -> pymysql.connections.Connection:
        if self.connected:
            self.connections.append(commit)
            return self.db_connection

        self.db_connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            port=self.port,
            cursorclass=pymysql.cursors.DictCursor
        )

        self.connections.append(commit)
        self.cursor = self.db_connection.cursor()

        try:
            self.create_database(self.db_connection)
            self.db_connection.select_db(self.database)
        except pymysql.Error as err:
            raise RuntimeError(f"Error connecting to or creating database: {err}") from None

        if self.foreign_keys:
            self.enable_foreign_keys()
        return self.db_connection

    def create_database(self, connection: pymysql.connections.Connection) -> None:
        """
        Creates the specified database if it does not exist.

        :param connection: MySQL database connection object.
        :raise RuntimeError: If there is an issue creating the database.
        """
        try:
            with connection.cursor() as cursor:
                create_db_query = f"CREATE DATABASE IF NOT EXISTS {self.database} " \
                                  "CHARACTER SET {} COLLATE {}".format(
                                      self.charcet,
                                      self.collate
                                  )
                cursor.execute(create_db_query)
        except pymysql.Error as err:
            raise RuntimeError(f"Error creating database: {err}") from None

    def disconnect(self) -> None:
        if not self.connected:
            raise ConnectionError(f"Could not disconnect without a pre-established connection")
        self.connections.pop()
        if not self.connected:
            self.db_connection.close()
            self.db_connection = None

    def close(self) -> None:
        self.db_connection.close()

    def commit(self) -> None:
        if not self.connected:
            raise ConnectionError("Could not commit without first being connected")
        self.db_connection.commit()

    @contextmanager
    def connection(self, commit: bool = True) -> Generator[pymysql.connections.Connection, None, None]:
        self.connect(commit=commit)
        try:
            yield self.db_connection
        finally:
            if self.commit_mode:
                self.commit()
            self.disconnect()

    def enable_foreign_keys(self) -> Result:
        if not self.connected:
            raise ModelException(f"Could not enable FKs without a pre-established connection") from None

        return Result([], self.execute("SET foreign_key_checks = 1"))

    def disable_foreign_keys(self) -> Result:
        if not self.connected:
            raise ModelException(f"Could not disable FKs without a pre-established connection") from None

        return Result([], self.execute("SET foreign_key_checks = 0"))

    def execute(self, statement: Statement, query_parameters: Optional[list[object]] = None) -> pymysql.cursors.Cursor:
        to_execute = str(statement)
        if query_parameters is None:
            query_parameters = statement.query_parameters if isinstance(statement, Statement) else []
        if not self.connected:
            statement = statement if isinstance(statement, str) else f"'{statement.__class__.__name__}' statement"
            raise SQLExecutionError(f"Could not execute {statement} without connection")
        if self.output:
            print(statement)
        self.cursor.execute(to_execute, query_parameters)
        return self.cursor

    def __enter__(self) -> "MySQLClient":
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.disconnect()
