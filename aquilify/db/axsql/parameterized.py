"""
The module containing the logic behind Parameterized clauses.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from .statements import Statement
    
import inspect
from aquilify.utils.module_loading import import_string
from aquilify.settings.base import settings


class Parameterized(ABC):
    """
    The class containing the logic behind Parameterized clauses.

    Parameterized clauses are essentially clauses that may require use parameter sanitization, such as WHERE clauses.
    These are needed to transfer the parameters to the base statement while preserved their order,
    so that they can be passed to the internal sqlite3 engine in the correct order during execution,
    maintaining safety from SQL injection attacks.
    """
    @staticmethod
    def _check_vendor():
        database_settings = getattr(settings, 'DATABASE')
        default_settings = database_settings.get("default", {})
        engine = default_settings.get("ENGINE")
        engine_module = import_string(engine)
        
        return engine_module
        
    def parameter(self, parameter: object) -> Literal["?"]:
        from aquilify.db.axsql.backend import (
            Sqlite3,
            MySQLClient,
            PostgreSQLClient
        )
        
        """
        Registers a query parameter for this statement, and replaces it with a literal "?" for direct use in queries.

        :param parameter: The parameter to register
        :return: A "?" string literal for drop-in replacement when building queries
        """
        
        sqlite_module = inspect.getmodule(Parameterized._check_vendor()) == inspect.getmodule(Sqlite3)
        mysql_module = inspect.getmodule(Parameterized._check_vendor()) == inspect.getmodule(MySQLClient)
        postgresql_module = inspect.getmodule(Parameterized._check_vendor()) == inspect.getmodule(PostgreSQLClient)

        self.parameters.append(parameter)
        if sqlite_module:
            return "?"
        elif mysql_module:
            return "%s"
        elif postgresql_module:
            return "%s"

    @property
    @abstractmethod
    def parameters(self) -> list[object]:
        """
        The parameters of this parameterized clause as an abstract property.

        :return: The list of parameters
        """
        return []

    @abstractmethod
    def build_sql(self) -> str:
        """
        Builds a valid SQL string representing this clause, used when executing the statement this clause is a part of.

        :return: The valid SQL string representing this clause
        """
        return ""

    def __str__(self) -> str:
        """
        The string representation for this clause, used when it is being executed.

        :return: The valid SQL string representing this clause
        """
        return self.build_sql()

    def register(self, statement: Statement) -> None:
        """
        Registers each of the parameters of this clause with a given base statement.

        :param statement: The base statement this clause is a part of
        """
        statement.register_parameterized(self)
