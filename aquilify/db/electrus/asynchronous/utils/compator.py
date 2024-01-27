import os
import json
import aiofiles

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ...exception.base import ElectrusException

class DataHandler(ABC):
    @abstractmethod
    async def import_data(self, file_path: str, append: bool = False) -> None:
        pass

    @abstractmethod
    async def export_data(self, file_path: str) -> None:
        pass

    @abstractmethod
    async def read_json(self, file_path: str) -> Any:
        pass

    @abstractmethod
    async def write_json(self, data: Any, file_path: str) -> None:
        pass

class FileHandler:
    @staticmethod
    async def read_json(file_path: str) -> Any:
        try:
            async with aiofiles.open(file_path, 'r') as file:
                return json.loads(await file.read())
        except FileNotFoundError:
            raise ElectrusException(f"File '{file_path}' not found.")
        except Exception as e:
            raise ElectrusException(f"Error reading from file '{file_path}': {e}")

    @staticmethod
    async def write_json(data: Any, file_path: str) -> None:
        try:
            async with aiofiles.open(file_path, 'w') as file:
                await file.write(json.dumps(data, indent=4))
        except Exception as e:
            raise ElectrusException(f"Error writing to file '{file_path}': {e}")

class DataComparator(DataHandler, FileHandler):
    async def import_data(self, file_path: str, collection_path: str, append: bool = False) -> None:
        try:
            if not os.path.exists(file_path):
                raise ElectrusException(f"File '{file_path}' does not exist.")

            collection_data = await self.read_json(collection_path)
            with open(file_path, 'r') as file:
                data = json.load(file)
                if append and collection_data:
                    collection_data.extend(data)
                else:
                    collection_data = data
                await self.write_json(collection_data, collection_path)
        except Exception as e:
            raise ElectrusException(f"Error importing data: {e}")

    async def export_data(self, file_path: str, collection_data: List[Dict[str, Any]]) -> None:
        try:
            await self.write_json(collection_data, file_path)
        except Exception as e:
            raise ElectrusException(f"Error exporting data: {e}")