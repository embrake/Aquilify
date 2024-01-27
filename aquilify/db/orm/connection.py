import logging
from aquilify.settings.base import settings
from aquilify.utils.module_loading import import_string
from aquilify.exception.base import ImproperlyConfigured

class DatabaseVendor:
    SQLITE = "aquilify.db.orm.Sqlite3"

class UnsupportedVendor(ImproperlyConfigured):
    pass

class DatabaseConnectionError(ImproperlyConfigured):
    pass

class DatabaseConnectionManager:
    def __init__(self, default_vendor: str = DatabaseVendor.SQLITE, default_name: str = 'db.sqlite3') -> None:
        self.default_vendor = default_vendor
        self.default_name = default_name
        self.logger = logging.getLogger(__name__)

    def _validate_database_settings(self, settings_data):
        if not settings_data or not settings_data.get("default"):
            raise ImproperlyConfigured("The 'DATABASE' settings are missing or improperly configured.")
        engine = settings_data['default'].get("ENGINE", self.default_vendor)
        if engine != DatabaseVendor.SQLITE:
            raise UnsupportedVendor(f"Vendor '{engine}' isn't supported by aquilify by default.")

    def _get_engine_module(self, engine):
        try:
            engine_module = import_string(engine)
            return engine_module
        except ImportError as e:
            raise ImproperlyConfigured(f"Invalid engine '{engine}' or Database connection not configured properly: {e}")

    def _establish_connection(self, engine_module, name):
        try:
            db_connection = engine_module(name)
            if not db_connection:
                raise DatabaseConnectionError("Failed to establish the database connection.")
            return db_connection
        except Exception as e:
            raise DatabaseConnectionError(f"Error while establishing database connection: {e}")

    def _get_connection(self):
        try:
            database_settings = getattr(settings, 'DATABASE')
            self._validate_database_settings(database_settings)
            default_settings = database_settings.get("default", {})
            engine = default_settings.get("ENGINE", self.default_vendor)
            name = default_settings.get('NAME', self.default_name)

            engine_module = self._get_engine_module(engine)
            return self._establish_connection(engine_module, name)
        except (ImproperlyConfigured, UnsupportedVendor, DatabaseConnectionError) as e:
            self.logger.error(str(e))
            raise
