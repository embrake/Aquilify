import os

from typing import (
    List
)

from ...exception.base import ElectrusException
from .database import Database

class Electrus:
    def __init__(self):
        self.base_path = os.path.expanduser('~/.electrus')

    def list_databases(self) -> List[str]:
        try:
            databases = [name for name in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, name))]
            return databases
        except OSError as e:
            raise ElectrusException(f"Error listing databases: {e}")

    def list_collections_in_database(self, db_name: str) -> List[str]:
        try:
            db_path = os.path.join(self.base_path, db_name)

            if not os.path.isdir(db_path):
                raise ElectrusException(f"Database '{db_name}' does not exist or is not a valid directory.")

            collections = [name for name in os.listdir(db_path) if os.path.isdir(os.path.join(db_path, name))]
            return collections
        except OSError as e:
            raise ElectrusException(f"Error getting collections for database '{db_name}': {e}")

    def create_database(self, db_name: str) -> tuple[bool, str]:
        try:
            db_path = os.path.join(self.base_path, db_name)
            os.makedirs(db_path, exist_ok=True)
            return (True, f"Database '{db_name}' created successfully")
        except OSError as e:
            return (False, f"Error creating database '{db_name}': {e}")

    def drop_database(self, db_name: str) -> None:
        try:
            db_path = os.path.join(self.base_path, db_name)
            if os.path.exists(db_path) and os.path.isdir(db_path):
                os.rmdir(db_path)
            else:
                raise ElectrusException(True, f"Database '{db_name}' does not exist or is not a valid directory.")
        except OSError as e:
            raise ElectrusException(False, f"Error dropping database '{db_name}': {e}")

    def rename_database(self, old_name: str, new_name: str) -> None:
        try:
            old_path = os.path.join(self.base_path, old_name)
            new_path = os.path.join(self.base_path, new_name)
            if os.path.exists(old_path) and os.path.isdir(old_path):
                os.rename(old_path, new_path)
            else:
                raise ElectrusException(True, f"Database '{old_name}' does not exist or is not a valid directory.")
        except OSError as e:
            raise ElectrusException(False, f"Error renaming database '{old_name}' to '{new_name}': {e}")

    def database_exists(self, db_name: str) -> bool:
        db_path = os.path.join(self.base_path, db_name)
        return os.path.exists(db_path) and os.path.isdir(db_path)
    
    def __getitem__(self, db_name: str) -> 'Database':
        return Database(db_name)