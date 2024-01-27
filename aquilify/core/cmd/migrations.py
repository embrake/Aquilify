import argparse
from aquilify.settings.base import settings
from aquilify.exception.base import ImproperlyConfigured
from aquilify.utils.module_loading import import_string

import inspect

from aquilify.db.axsql.backend import Sqlite3
from aquilify.db.axsql.backend import MySQLClient

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CommandChoices:
    MAKE_MIGRATION = 'makemigration'


def get_models_from_settings():
    try:
        database_settings = getattr(settings, "DATABASE")
        default_settings = database_settings.get('default', {})
        return default_settings.get('MODALS', [])
    except AttributeError:
        raise ImproperlyConfigured("Database settings not configured properly!")


def load_models(models):
    loaded_models = []
    for index, model in enumerate(models, start=1):
        loaded_model = import_string(model)
        if not loaded_model:
            raise ImproperlyConfigured(f"Model '{model}' not found")
        loaded_models.append(loaded_model)
    return loaded_models

def _check_vendor():
    database_settings = getattr(settings, 'DATABASE')
    default_settings = database_settings.get("default", {})
    engine = default_settings.get("ENGINE")
    engine_module = import_string(engine)
    
    return engine_module


def create_migration(models):
    try:
        print('')
        for index, model in enumerate(models, start=1):
            with model.database.connection() as session:
                
                if inspect.getmodule(_check_vendor()) == inspect.getmodule(MySQLClient): 
                    query = model.database.execute(f"SHOW TABLES LIKE '{model.table_.__tablename__}'")
                elif inspect.getmodule(_check_vendor()) == inspect.getmodule(Sqlite3):
                    query = session.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{model.table_.__tablename__}'")
                    
                table_exists = query.fetchone()
                if not table_exists:
                    model.create_table().execute()
                    model.create_indexes()
                    statement = (
                        f"{Colors.BOLD}- {Colors.OKGREEN}Modal {model.table_().__class__.__name__} Migration:{Colors.ENDC}\n"
                        f"    {Colors.OKGREEN}✔ Success: All user data migrated successfully.{Colors.ENDC}\n"
                        f"    {Colors.WARNING}Note: Verify the migrated data for accuracy. Additional data integrity checks "
                        f"recommended.{Colors.ENDC}\n"
                        f"    {Colors.WARNING}Run automated tests to ensure seamless functionality.{Colors.ENDC}\n"
                        f"{Colors.BOLD}- {Colors.OKGREEN}Table '{model.table_.__tablename__}' Creation:{Colors.ENDC}\n"
                        f"    {Colors.OKGREEN}✔ Success: 'users' table created in the database.{Colors.ENDC}\n"
                        f"    {Colors.WARNING}Note: Check the table structure and constraints. Make sure indices and "
                        f"relationships are set correctly.{Colors.ENDC}\n"
                        f"    {Colors.WARNING}Document the schema for future reference.{Colors.ENDC}\n"
                    )
                    print(statement)
                else:
                    statement = (
                        f"{Colors.BOLD}- {Colors.OKGREEN}Modal {model.table_().__class__.__name__} Migration:{Colors.ENDC}\n"
                        f"    {Colors.FAIL}✘ Migration Error: 'Modal Users' has already been successfully migrated.{Colors.ENDC}\n"
                        f"    {Colors.FAIL}Error: Please verify the migration status to avoid redundant processes.{Colors.ENDC}\n"
                        f"    {Colors.WARNING}Warning: Please remove the Modals from `settings.py` DATABASE -> dict[dict["
                        f"str, str]] to avoid the Migration error.{Colors.ENDC}\n"
                        f"{Colors.BOLD}- {Colors.OKGREEN}Table '{model.table_.__tablename__}' Creation:{Colors.ENDC}\n"
                        f"    {Colors.FAIL}✘ Migration Error: 'users' table already exists in the database.{Colors.ENDC}\n"
                        f"    {Colors.FAIL}Migration Error: The table creation process was unsuccessful due to an "
                        f"existing '{model.table_.__tablename__}' table.{Colors.ENDC}\n"
                    )
                    print(statement)
    except Exception as e:
        raise ImproperlyConfigured(f"Error creating porting: {e}")


def make_migration(parser: argparse.ArgumentParser):
    parser.add_argument('command', choices=[CommandChoices.MAKE_MIGRATION],
                        help='Migrate your `Modals` to SQL Database.')
    args = parser.parse_args()

    if args.command == CommandChoices.MAKE_MIGRATION:
        try:
            models = get_models_from_settings()
            loaded_models = load_models(models)
            create_migration(loaded_models)
        except ImproperlyConfigured as e:
            raise
