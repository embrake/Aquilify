import os
import json
import aiofiles

from typing import (
    Any,
    Dict,
    List,
    Union,
    Optional
)

from ..partials import (
    ElectrusUpdateData,
    ElectrusInsertData,
    ElectrusFindData,
    ElectrusDeleteData,
    ElectrusLogicalOperators
)

from ..utils import (
    ElectrusBulkOperation,
    ElectrusDistinctOperation,
    ElectrusDataComparator,
    ElectrusAggregation
)

from ...exception.base import ElectrusException

class Collection:
    def __init__(self, db_name: str, collection_name: str):
        self.db_name = db_name
        self.collection_name = collection_name
        self.base_path = os.path.expanduser(f'~/.electrus')
        self.collection_dir_path = os.path.join(self.base_path, self.db_name, self.collection_name)
        self.collection_path = os.path.join(self.collection_dir_path, f'{self.collection_name}.json')
        os.makedirs(self.collection_dir_path, exist_ok=True)
        
        self._create_empty_collection_file()
        
    def _create_empty_collection_file(self) -> None:
        if not os.path.exists(self.collection_path):
            with open(self.collection_path, 'w') as file:
                file.write(json.dumps([], indent=4))

    async def _read_collection_data(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.collection_path):
                async with aiofiles.open(self.collection_path, 'r') as file:
                    return json.loads(await file.read())
        except Exception as e:
            raise ElectrusException(f"Error reading collection data: {e}")
        return []

    async def _write_json(self, data: Any, file_path: str) -> None:
        try:
            async with aiofiles.open(file_path, 'w') as file:
                await file.write(json.dumps(data, indent=4))
        except Exception as e:
            raise ElectrusException(f"Error writing to file: {e}")

    async def insert_one(self, data: Dict[str, Any], overwrite: Optional[bool] = False) -> None:
        try:
            collection_path = self.collection_path
            return await ElectrusInsertData(collection_path)._obl_one(data, overwrite)
        except Exception as e:
            raise ElectrusException(f"Error inserting data: {e}")

    async def insert_many(self, data_list: List[Dict[str, Any]], overwrite: Optional[bool] = False) -> None:
        try:
            collection_path = self.collection_path
            return await ElectrusInsertData(collection_path)._obl_many(data_list, overwrite)
        except Exception as e:
            raise ElectrusException(f"Error inserting multiple data: {e}")

    async def update_one(self, filter_query: Dict[str, Any], update_data: Dict[str, Any]) -> None:
        return await ElectrusUpdateData.update(self.collection_path, filter_query, update_data)
    
    async def update_many(self, filter_query: Dict[str, Any], update_data: Dict[str, Any]) -> None:
        return await ElectrusUpdateData.update(self.collection_path, filter_query, update_data, multi=True)

    async def find_one(self, filter_query: Dict[str, Any], projection: List[str] = None) -> Union[Dict[str, Any], None]:
        try:
            collection_path = self.collection_path
            return await ElectrusFindData(collection_path).find_one(filter_query, projection)
        except Exception as e:
            raise ElectrusException(f"Error finding data: {e}")
        
    def find(self) -> ElectrusFindData:
        return ElectrusFindData(self.collection_path)

    async def find_many(self, filter_query: Dict[str, Any], projection: List[str] = None, sort_by: str = None, limit: int = None) -> List[Dict[str, Any]]:
        try:
            collection_data = await self._read_collection_data()
            results = []
            operator_evaluator = ElectrusLogicalOperators()

            for item in collection_data:
                if operator_evaluator.evaluate(item, filter_query):
                    if projection:
                        result = {key: item.get(key) for key in projection}
                        results.append(result)
                    else:
                        results.append(item)
                    if limit and len(results) >= limit:
                        break

            if sort_by:
                results = sorted(results, key=lambda x: x.get(sort_by))

            return results
        except FileNotFoundError:
            raise ElectrusException(f"Database '{self.db_name}' or collection '{self.collection_name}' not found.")
        except Exception as e:
            raise ElectrusException(f"Error finding data: {e}")

    async def fetch_all(
        self,
        filter_query: Optional[Dict[str, Any]] = None,
        projection: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        try:
            collection_data = await self._read_collection_data()
            operator_evaluator = ElectrusLogicalOperators()

            if filter_query:
                collection_data = [item for item in collection_data if operator_evaluator.evaluate(item, filter_query)]

            if projection:
                if not filter_query:
                    collection_data = [{key: item.get(key) for key in projection} for item in collection_data]
                else:
                    collection_data = [{key: doc[key] for key in projection if key in doc} for doc in collection_data]

            if sort_by:
                collection_data.sort(key=lambda x: x.get(sort_by))

            if limit:
                collection_data = collection_data[:limit]

            return collection_data

        except FileNotFoundError:
            raise ElectrusException(f"Database '{self.db_name}' or collection '{self.collection_name}' not found.")
        except Exception as e:
            raise ElectrusException(f"Error fetching data: {e}")

    async def count_documents(self, filter_query: Dict[str, Any]) -> int:
        try:
            collection_data = await self._read_collection_data()
            count = sum(1 for item in collection_data if all(item.get(key) == value for key, value in filter_query.items()))
            return count
        except FileNotFoundError:
            raise ElectrusException(f"Database '{self.db_name}' or collection '{self.collection_name}' not found.")
        except Exception as e:
            raise ElectrusException(f"Error counting documents: {e}")

    async def delete_one(self, filter_query: Dict[str, Any]) -> None:
        return await ElectrusDeleteData.delete(self.collection_path, filter_query)
    
    async def delete_many(self, filter_query: Dict[str, Any]) -> None:
        return await ElectrusDeleteData.delete(self.collection_path, filter_query, True)
    
    async def bulk_operation(self, operations: List[Dict[str, Any]]) -> ElectrusBulkOperation:
        return await ElectrusBulkOperation(self.collection_path)._bulk_write(operations)
    
    async def distinct(
        self,
        field: str,
        filter_query: Optional[Dict[str, Any]] = None,
        sort: Optional[bool] = False
    ) -> ElectrusDistinctOperation:
        return await ElectrusDistinctOperation(self.collection_path)._distinct(field, filter_query, sort)
    
    async def import_data(self, file_path: str, append: bool = False) -> None:
        try:
            data_comparator = ElectrusDataComparator()
            await data_comparator.import_data(file_path, self.collection_path, append)
        except Exception as e:
            raise ElectrusException(f"Error importing data: {e}")

    async def export_data(self, file_path: str) -> None:
        try:
            collection_data = await self._read_collection_data()
            data_comparator = ElectrusDataComparator()
            await data_comparator.export_data(file_path, collection_data)
        except Exception as e:
            raise ElectrusException(f"Error exporting data: {e}")
        
    async def aggregation(self, pipeline: List[Dict[str, Any]]) -> ElectrusAggregation:
        try:
            collection_data = await self._read_collection_data()
            aggregation = ElectrusAggregation(collection_data)
            result = aggregation.execute(pipeline)
            return result
        except Exception as e:
            raise ElectrusException(f"Error performing aggregation: {e}")