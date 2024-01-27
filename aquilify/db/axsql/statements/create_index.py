from __future__ import annotations
from typing import TYPE_CHECKING
from .statement import Statement
if TYPE_CHECKING:
    from ..entity import Column, Entity

from ..exception import FieldException

from aquilify.settings import settings
from aquilify.utils.module_loading import import_string

import inspect

class CreateIndex(Statement):
    """
    The class containing the logic for building and executing CREATE INDEX statements with AQUILIFY_SQLite_ORM.
    """

    def __init__(self, index_name: str, field_name, table: Entity, columns: list[Column], unique: bool = False):
        """

        :param index_name: The name of the index to be created.
        :param table: The table associated with the index.
        :param columns: The columns included in the index.
        :param unique: Indicates if the index should be unique.
        """
        super().__init__(table.database)
        self.index_name = index_name
        self.table = table
        self.columns = columns
        self.unique = unique
        self.field_name = field_name
        
    @staticmethod
    def _check_vendor():
        database_settings = getattr(settings, 'DATABASE')
        default_settings = database_settings.get("default", {})
        engine = default_settings.get("ENGINE")
        engine_module = import_string(engine)
        
        return engine_module

    def build_sql(self) -> str:
        
        from aquilify.db.axsql.backend import (
            Sqlite3,
            MySQLClient,
            PostgreSQLClient
        )

        unique_str = "UNIQUE " if self.unique else ""
        qlX00 = [column.name for column in self.columns if column.name.lower() == self.field_name]
        if not qlX00:
            raise FieldException("Field %s not found in __tablename__ %s" % (self.field_name, self.table))
        columns_section = ", ".join(qlX00)

        sqlite_module = inspect.getmodule(CreateIndex._check_vendor()) == inspect.getmodule(Sqlite3)
        mysql_module = inspect.getmodule(CreateIndex._check_vendor()) == inspect.getmodule(MySQLClient)
        postgresql_module = inspect.getmodule(CreateIndex._check_vendor()) == inspect.getmodule(PostgreSQLClient)

        if sqlite_module:
            return f"CREATE {unique_str}INDEX IF NOT EXISTS {self.index_name} ON {self.table} ({columns_section});"
        elif postgresql_module:
            return f"CREATE {unique_str}INDEX IF NOT EXISTS {self.index_name} ON {self.table} ({columns_section});"
        elif mysql_module:
            return f"CREATE {unique_str}INDEX {self.index_name} ON {self.table} ({columns_section})"
