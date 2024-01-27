import os
import json
import aiofiles
from typing import Any, Dict, List
from ...exception.base import ElectrusException
from ..partials import ElectrusLogicalOperators, ElectrusUpdateOperators

class BulkOperation:
    def __init__(self, collection_path: str):
        self.collection_path = collection_path

    async def _bulk_write(self, operations: List[Dict[str, Any]]) -> None:
        try:
            collection_data = await self._read_collection_data()

            for operation in operations:
                op_type = operation.get('type')
                data = operation.get('data')
                filter_query = operation.get('filter_query')

                if op_type == 'insert':
                    await self._insert_data(collection_data, data)
                elif op_type == 'update':
                    await self._update_data(collection_data, filter_query, data)
                elif op_type == 'delete':
                    await self._delete_data(collection_data, filter_query)
                else:
                    raise ElectrusException(f"Invalid operation type: {op_type}")

            await self._write_collection_data(collection_data)
        except Exception as e:
            raise ElectrusException(f"Error performing bulk write: {e}")

    async def _read_collection_data(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.collection_path):
                async with aiofiles.open(self.collection_path, 'r') as file:
                    return json.loads(await file.read())
            return []
        except Exception as e:
            raise ElectrusException(f"Error reading collection data: {e}")

    async def _write_collection_data(self, data: List[Dict[str, Any]]) -> None:
        try:
            async with aiofiles.open(self.collection_path, 'w') as file:
                await file.write(json.dumps(data, indent=4))
        except Exception as e:
            raise ElectrusException(f"Error writing collection data: {e}")

    async def _insert_data(self, collection_data: List[Dict[str, Any]], data: Dict[str, Any]) -> None:
        try:
            collection_data.append(data)
        except Exception as e:
            raise ElectrusException(f"Error inserting data: {e}")

    async def _update_data(
        self, collection_data: List[Dict[str, Any]], filter_query: Dict[str, Any], update_data: Dict[str, Any]
    ) -> None:
        try:
            updated_data = []
            operator_evaluator = ElectrusLogicalOperators()
            update_operator = ElectrusUpdateOperators()

            for item in collection_data:
                if operator_evaluator.evaluate(item, filter_query):
                    updated_item = update_operator.evaluate(item, update_data)
                    updated_data.append(updated_item)
                else:
                    updated_data.append(item)

            await self._write_collection_data(updated_data)
        except Exception as e:
            raise ElectrusException(f"Error updating data: {e}")

    async def _delete_data(self, collection_data: List[Dict[str, Any]], filter_query: Dict[str, Any]) -> None:
        try:
            operator_evaluator = ElectrusLogicalOperators()
            filtered_data = [item for item in collection_data if not operator_evaluator.evaluate(item, filter_query)]

            await self._write_collection_data(filtered_data)
        except Exception as e:
            raise ElectrusException(f"Error deleting data: {e}")
