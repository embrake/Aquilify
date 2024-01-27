import json

from typing import Any, Dict
from ...exception.base import ElectrusException
from .operators import ElectrusLogicalOperators, ElectrusUpdateOperators

class UpdateData:
    @classmethod
    def update(
        cls,
        collection_path: str,
        filter_query: Dict[str, Any],
        update_data: Dict[str, Any],
        multi: bool = False
    ) -> None:
        try:
            collection_data = cls._read_collection_data(collection_path)

            updated = False
            for item in collection_data:
                if ElectrusLogicalOperators().evaluate(item, filter_query):
                    ElectrusUpdateOperators().evaluate(item, update_data)
                    updated = True

                    if not multi:
                        break

            if updated:
                cls._write_collection_data(collection_path, collection_data)
                return True
            else:
                return False

        except FileNotFoundError:
            raise ElectrusException(f"File not found at path: {collection_path}")
        except json.JSONDecodeError as je:
            raise ElectrusException(f"Error decoding JSON: {je}")
        except Exception as e:
            raise ElectrusException(f"Error updating documents: {e}")

    @staticmethod
    def _read_collection_data(collection_path: str) -> list[Dict[str, Any]]:
        with open(collection_path, 'r') as file:
            return json.loads(file.read())

    @staticmethod
    def _write_collection_data(collection_path: str, collection_data: list[Dict[str, Any]]) -> None:
        with open(collection_path, 'w') as file:
            file.write(json.dumps(collection_data, indent=4))
