from typing import Optional, Generator, List
from dataclasses import dataclass, field
from contextlib import contextmanager
import psycopg2
from aquilify.db.axsql.entity import Entity 
from aquilify.db.axsql.statements import Statement
from aquilify.db.axsql.exception import ConnectionError, SQLExecutionError

from psycopg2 import sql

@dataclass(eq=True, slots=True)
class PostgreSQLClient:
    host: str
    user: str
    password: str
    database: str
    port: int = 5432
    output: bool = False
    auto_execute: bool = False
    encoding ='UTF8'
    collate = 'en_IN'
    ctype = "en_IN"
    
    tables: set[Entity] = field(init=False, default_factory=set)
    db_connection: Optional[psycopg2.extensions.connection] = field(init=False, default=None)
    cursor: Optional[psycopg2.extensions.cursor] = field(init=False, default=None)
    connections: list[bool] = field(init=False, default_factory=list)

    def add_table(self, table: Entity) -> None:
        self.tables.add(table)

    @property
    def commit_mode(self) -> bool:
        return self.connections[-1]

    @property
    def connected(self) -> bool:
        return bool(self.connections)

    def connect(self, commit=True):
        if self.connected:
            self.connections.append(commit)
            return self.db_connection

        connection_string = f"host={self.host} user={self.user} password={self.password} dbname=postgres port={self.port}"
        admin_connection = psycopg2.connect(connection_string)
        admin_connection.autocommit = True

        try:
            self.create_database(admin_connection)
        except psycopg2.Error as err:
            admin_connection.close()
            raise RuntimeError(f"Error creating database: {err}") from None

        admin_connection.close()

        connection_string = f"host={self.host} user={self.user} password={self.password} dbname={self.database} port={self.port}"
        self.db_connection = psycopg2.connect(connection_string)

        self.connections.append(commit)
        self.cursor = self.db_connection.cursor()

        return self.db_connection

    def create_database(self, connection: psycopg2.extensions.connection) -> None:
        """
        Creates the specified database if it does not exist.

        :param connection: PostgreSQL database connection object.
        :raise RuntimeError: If there is an issue creating the database.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s;", (self.database,))
                database_exists = cursor.fetchone()

                if not database_exists:
                    create_db_query = sql.SQL(
                        "CREATE DATABASE {database} ENCODING {encoding} LC_COLLATE {collate} LC_CTYPE {ctype};"
                    ).format(
                        database=sql.Identifier(self.database),
                        encoding=sql.Identifier(self.encoding),
                        collate=sql.Identifier(self.collate),
                        ctype = sql.Identifier(self.ctype)
                    )
                    cursor.execute(create_db_query)
        except psycopg2.Error as err:
            raise RuntimeError(f"Error creating database: {err}") from None

    def disconnect(self) -> None:
        if not self.connected:
            raise ConnectionError("Could not disconnect without a pre-established connection")

        self.connections.pop()

        if not self.connected:
            self.cursor.close()
            self.db_connection.close()
            self.db_connection = None

    def close(self) -> None:
        self.db_connection.close()

    def commit(self) -> None:
        if not self.connected:
            raise ConnectionError("Could not commit without first being connected")
        self.db_connection.commit()

    @contextmanager
    def connection(self, commit: bool = True) -> Generator[psycopg2.extensions.connection, None, None]:
        self.connect(commit=commit)
        try:
            yield self.db_connection
        finally:
            if self.commit_mode:
                self.commit()
            self.disconnect()

    def execute(self, statement: Statement, query_parameters: Optional[list[object]] = None) -> psycopg2.extensions.cursor:
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

    def __enter__(self) -> "PostgreSQLClient":
        return self

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        self.disconnect()
