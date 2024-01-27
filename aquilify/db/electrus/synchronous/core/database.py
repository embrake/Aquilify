import os
import json

from typing import (
    List
)

from ...exception.base import ElectrusException

from .collection import Collection

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.base_path = os.path.expanduser('~/.electrus')
        self.db_path = os.path.join(self.base_path, self.db_name)

    def create(self) -> None:
        try:
            os.makedirs(self.db_path, exist_ok=True)
        except OSError as e:
            raise ElectrusException(f"Error creating database '{self.db_name}': {e}")

    def get_collections(self) -> List[str]:
        try:
            if not os.path.exists(self.db_path) or not os.path.isdir(self.db_path):
                raise ElectrusException(f"Database '{self.db_name}' does not exist or is not a valid directory.")

            collections = [name for name in os.listdir(self.db_path) if os.path.isdir(os.path.join(self.db_path, name))]
            return collections
        except OSError as e:
            raise ElectrusException(f"Error getting collections for database '{self.db_name}': {e}")

    def __getitem__(self, collection_name: str) -> 'Collection':
        return Collection(self.db_name, collection_name)

    def create_collection(self, collection_name: str) -> None:
        collection_path = os.path.join(self.db_path, collection_name)

        try:
            os.makedirs(collection_path, exist_ok=True)

            json_file_path = os.path.join(collection_path, f"{collection_name}.json")
            with open(json_file_path, 'w') as json_file:
                json.dump([], json_file)

        except FileExistsError:
            raise ElectrusException(f"Collection '{collection_name}' already exists in database '{self.db_name}'")
        except OSError as e:
            raise ElectrusException(f"Error creating collection '{collection_name}' in database '{self.db_name}': {e}")

        except Exception as e:
            raise ElectrusException(f"Unexpected error creating collection '{collection_name}': {e}")

    def drop_collection(self, collection_name: str) -> None:
        collection_path = os.path.join(self.db_path, collection_name)

        try:
            if os.path.exists(collection_path) and os.path.isdir(collection_path):
                os.rmdir(collection_path)
            else:
                raise ElectrusException(f"Collection '{collection_name}' does not exist or is not a valid directory.")
        except OSError as e:
            raise ElectrusException(f"Error dropping collection '{collection_name}' in database '{self.db_name}': {e}")
        except Exception as e:
            raise ElectrusException(f"Unexpected error dropping collection '{collection_name}': {e}")

    def rename_collection(self, old_name: str, new_name: str) -> None:
        old_path = os.path.join(self.db_path, old_name)
        new_path = os.path.join(self.db_path, new_name)

        try:
            if os.path.exists(old_path) and os.path.isdir(old_path):
                os.rename(old_path, new_path)
            else:
                raise ElectrusException(f"Collection '{old_name}' does not exist or is not a valid directory.")
        except OSError as e:
            raise ElectrusException(f"Error renaming collection '{old_name}' to '{new_name}' in database '{self.db_name}': {e}")
        except Exception as e:
            raise ElectrusException(f"Unexpected error renaming collection '{old_name}' to '{new_name}': {e}")

    def collection_exists(self, collection_name: str) -> bool:
        collection_path = os.path.join(self.db_path, collection_name)
        return os.path.exists(collection_path) and os.path.isdir(collection_path)