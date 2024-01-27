import logging
from aquilify.settings.base import settings
from aquilify.utils.module_loading import import_string
from aquilify.exception.base import ImproperlyConfigured
from aquilify.db.axsql.backend.axsqlite3 import Sqlite3
from aquilify.db.axsql.backend import MySQLClient, PostgreSQLClient

import typing
import inspect

from enum import Enum

class DatabaseVendor(Enum):
    SQLITE = "aquilify.db.axsql.backend.Sqlite3"
    ELECTRUS = "aquilify.db.electrus"
    MYSQL = "aquilify.db.axsql.backend.MySQLClient"
    POSTGRESQL = "aquilify.db.axsql.backend.PostgreSQLClient"


class UnsupportedVendor(ImproperlyConfigured):
    pass


class DatabaseConnectionError(ImproperlyConfigured):
    pass

def _get_engine_module(engine):
    try:
        engine_module = import_string(engine)
        return engine_module
    except ImportError as e:
        raise ImproperlyConfigured(f"Invalid engine '{engine}' or Sqlite3 connection not configured properly: {e}")


def _establish_sqlite3_connection(engine_module, name, output: bool = False, auto_execute = False) -> Sqlite3:
    try:
        db_connection = engine_module(path = name, output = output, auto_execute = auto_execute)
        if not db_connection:
            raise DatabaseConnectionError("Failed to establish the database connection.")
        return db_connection
    except Exception as e:
        raise DatabaseConnectionError(f"Error while establishing database connection: {e}")
    
def _establish_mysql_connection(
    engine_module,
    name,
    host,
    username,
    password,
    port = 3306,
    output: bool = False,
    auto_execute = False
) -> MySQLClient:
    
    try:
        db_connection = engine_module(
            host,
            username,
            password,
            name,
            port,
            output,
            auto_execute
        )
        if not db_connection:
            raise DatabaseConnectionError("Failed to establish the database connection.")
        return db_connection
    except Exception as e:
        raise DatabaseConnectionError(f"Error while establishing database connection: {e}")
    
def _establish_postgresql_connection(
    engine_module,
    name,
    host,
    username,
    password,
    port = 5432,
    output: bool = False,
    auto_execute = False
) -> PostgreSQLClient:
    
    try:
        db_connection = engine_module(
            host,
            username,
            password,
            name,
            port,
            output,
            auto_execute
        )
        if not db_connection:
            raise DatabaseConnectionError("Failed to establish the database connection.")
        return db_connection
    except Exception as e:
        raise DatabaseConnectionError(f"Error while establishing database connection: {e}")


class DatabaseConnectionManager:
    def __init__(self, default_vendor: str = DatabaseVendor.SQLITE, default_name: str = 'db.db') -> None:
        self.default_vendor = default_vendor
        self.default_name = default_name
        self.logger = logging.getLogger(__name__)
        self.default_output = False

    def _validate_database_settings(self, settings_data):
        if not settings_data or not settings_data.get("default"):
            raise ImproperlyConfigured("The 'DATABASE' settings are missing or improperly configured.")
        engine = settings_data['default'].get("ENGINE", self.default_vendor)
        if engine not in DatabaseVendor._value2member_map_:
            raise UnsupportedVendor(f"Vendor '{engine}' isn't supported by aquilify by default.")

    def _get_connection(self) -> typing.Union[Sqlite3, MySQLClient, PostgreSQLClient]:
        try:
            database_settings = getattr(settings, 'DATABASE')
            self._validate_database_settings(database_settings)
            default_settings = database_settings.get("default", {})
            engine = default_settings.get("ENGINE", self.default_vendor)
            port = default_settings.get('PORT')
            output = default_settings.get('OUTPUT', self.default_output)
            auto_execute = default_settings.get('AUTO_EXECUTE', False)
            engine_module = _get_engine_module(engine)
            name = default_settings.get('NAME', self.default_name)
            
            if inspect.getmodule(engine_module) == inspect.getmodule(Sqlite3):   
                return _establish_sqlite3_connection(engine_module, name, output, auto_execute)
            
            elif inspect.getmodule(engine_module) == inspect.getmodule(MySQLClient):
                host = default_settings.get("HOST", 'localhost')
                username = default_settings.get("USERNAME", 'root')
                password = default_settings.get("PASSWORD", '')
                return _establish_mysql_connection(
                    engine_module,
                    name,
                    host,
                    username,
                    password,
                    port,
                    output,
                    auto_execute
                )
            
            elif inspect.getmodule(engine_module) == inspect.getmodule(PostgreSQLClient):
                host = default_settings.get("HOST", 'localhost')
                username = default_settings.get("USERNAME", 'root')
                password = default_settings.get("PASSWORD", '')
                return _establish_postgresql_connection(
                    engine_module,
                    name,
                    host,
                    username,
                    password,
                    port,
                    output,
                    auto_execute
                )
                
            else:
                raise UnsupportedVendor("Invalid database vendor found %s" % (engine))
            
        except (ImproperlyConfigured, UnsupportedVendor, DatabaseConnectionError) as e:
            self.logger.error(str(e))
            raise


connection: typing.Union[Sqlite3, MySQLClient, ] = DatabaseConnectionManager()._get_connection()
