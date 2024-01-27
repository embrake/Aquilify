import json
import aiofiles

from typing import Any, Dict
from .operators import ElectrusLogicalOperators
from ...exception.base import ElectrusException

class DeleteData:
    @staticmethod
    async def delete(collection_path: str, filter_query: Dict[str, Any], multi: bool = False) -> None:
        try:
            collection_data = await DeleteData._read_collection_data(collection_path)
            deleted_count = 0

            for index, item in enumerate(collection_data):
                if ElectrusLogicalOperators().evaluate(item, filter_query):
                    del collection_data[index]
                    deleted_count += 1
                    if not multi:
                        break

            if deleted_count > 0:
                await DeleteData._write_collection_data(collection_path, collection_data)
                return True
            else:
                return False
        
        except (FileNotFoundError, json.JSONDecodeError, TypeError, IndexError) as e:
            raise ElectrusException(f"Error in file operations: {e}")
        except Exception as e:
            raise ElectrusException(f"Error deleting documents: {e}")

    @staticmethod
    async def _read_collection_data(collection_path: str) -> list[Dict[str, Any]]:
        try:
            async with aiofiles.open(collection_path, 'r') as file:
                return json.loads(await file.read())
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            raise ElectrusException(f"Error reading collection data: {e}")
        except Exception as e:
            raise ElectrusException(f"Error reading collection data: {e}")

    @staticmethod
    async def _write_collection_data(collection_path: str, collection_data: list[Dict[str, Any]]) -> None:
        try:
            async with aiofiles.open(collection_path, 'w') as file:
                await file.write(json.dumps(collection_data, indent=4))
        except (FileNotFoundError, json.JSONDecodeError, TypeError) as e:
            raise ElectrusException(f"Error writing collection data: {e}")
        except Exception as e:
            raise ElectrusException(f"Error writing collection data: {e}")