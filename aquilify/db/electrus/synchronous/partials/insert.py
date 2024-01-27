import json
import os
import random
import string

from typing import (
    Any,
    Dict,
    List,
    Union,
    Optional
)

from .objectID import ObjectId
from ...exception.base import ElectrusException

class InsertData:
    def __init__(self, collection_path: str) -> None:
        self.collection_path: str = collection_path

    def _generate_unique_id(self) -> str:
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    def _process_auto_inc(self, data: Dict[str, Union[int, str]], collection_data: List[Dict[str, Any]]) -> None:
        auto_inc_keys: List[str] = [key for key, value in data.items() if value == 'auto_inc']
        for key in auto_inc_keys:
            existing_ids: List[int] = [item.get(key, 0) for item in collection_data if isinstance(item.get(key), int)]
            data[key] = max(existing_ids, default=0) + 1

    def _process_unique_id(self, data: Dict[str, Union[int, str]]) -> None:
        unique_id_keys: List[str] = [key for key, value in data.items() if value == 'unique_id']
        for key in unique_id_keys:
            data[key] = self._generate_unique_id()

    def _write_collection_data(self, collection_data: List[Dict[str, Any]]) -> None:
        with open(self.collection_path, 'w') as file:
            file.write(json.dumps(collection_data, indent=4))

    def _read_collection_data(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.collection_path):
            with open(self.collection_path, 'r') as file:
                return json.loads(file.read())
        return []

    def _update_collection_data(self, data: Dict[str, Any], overwrite_duplicate: bool = False) -> bool:
        try:
            collection_data: List[Dict[str, Any]] = self._read_collection_data()
            data['_id']: str = ObjectId.generate()

            if overwrite_duplicate:
                index: Optional[int] = next((i for i, item in enumerate(collection_data) if item == data), None)
                if index is not None:
                    collection_data[index] = data
                else:
                    self._process_unique_id(data)
                    self._process_auto_inc(data, collection_data)
                    collection_data.append(data)
            else:
                if data not in collection_data:
                    self._process_unique_id(data)
                    self._process_auto_inc(data, collection_data)
                    collection_data.append(data)

            self._write_collection_data(collection_data)
            return True

        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ElectrusException(f"Error handling file or JSON data: {e}")
        except Exception as e:
            raise ElectrusException(f"Error updating data: {e}")

    def _obl_one(self, data: Dict[str, Any], overwrite_duplicate: bool = False) -> bool:
        return self._update_collection_data(data, overwrite_duplicate)

    def _obl_many(self, data_list: List[Dict[str, Any]], overwrite_duplicate: bool = False) -> bool:
        try:
            for data in data_list:
                self._update_collection_data(data, overwrite_duplicate)

            return True

        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ElectrusException(f"Error handling file or JSON data: {e}")
        except Exception as e:
            raise ElectrusException(f"Error updating multiple data: {e}")
