import os
import aiofiles
import json
from typing import Any, Dict, List, Optional, Union

from ...exception.base import ElectrusException
from .operators import ElectrusLogicalOperators


class ElectrusFindData:
    def __init__(self, collection_path: str):
        self.collection_path = collection_path
        self.filter_query: Dict[str, Any] = {}
        self.projection: Optional[List[str]] = None
        self.sort_by: Optional[str] = None
        self.skip_val: int = 0
        self.page_size_val: int = 10

    async def _read_collection_data(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.collection_path):
                async with aiofiles.open(self.collection_path, 'r') as file:
                    return json.loads(await file.read())
            return []
        except Exception as e:
            raise ElectrusException(f"Error reading collection data: {e}")

    def skip(self, skip_val: int) -> 'ElectrusFindData':
        self.skip_val = skip_val
        return self

    def limit(self, page_size_val: int) -> 'ElectrusFindData':
        self.page_size_val = page_size_val
        return self

    def find(self) -> 'ElectrusFindData':
        return self

    def sort(self, sort_by: str) -> 'ElectrusFindData':
        self.sort_by = sort_by
        return self

    def filter(self, query: Dict[str, Any]) -> 'ElectrusFindData':
        self.filter_query = query
        return self

    def project(self, projection: List[str]) -> 'ElectrusFindData':
        self.projection = projection
        return self

    def _apply_skip_limit(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return data[self.skip_val: self.skip_val + self.page_size_val]

    async def execute(self) -> List[Dict[str, Any]]:
        try:
            collection_data = await self._read_collection_data()
            operator_checker = ElectrusLogicalOperators()

            filtered_data = [
                item for item in collection_data
                if operator_checker.evaluate(item, self.filter_query)
            ]

            if self.sort_by:
                filtered_data.sort(key=lambda x: x.get(self.sort_by))

            if self.projection:
                filtered_data = (
                    {key: item[key] for key in self.projection if key in item}
                    for item in filtered_data
                )

            paginated_data = list(filtered_data)[self.skip_val: self.skip_val + self.page_size_val]

            return paginated_data
        except Exception as e:
            raise ElectrusException(f"Error finding data: {e}")

    async def distinct(self, key: str) -> List[Any]:
        try:
            collection_data = await self._read_collection_data()
            distinct_values = set()

            for item in collection_data:
                if all(item.get(k) == v for k, v in self.filter_query.items()):
                    distinct_values.add(item.get(key))

            return list(distinct_values)
        except Exception as e:
            raise ElectrusException(f"Error getting distinct values: {e}")

    async def find_one(
        self, filter_query: Dict[str, Any], projection: Optional[List[str]] = None
    ) -> Union[Dict[str, Any], None]:
        try:
            collection_data = await self._read_collection_data()
            operator_checker = ElectrusLogicalOperators()

            for item in collection_data:
                if operator_checker.evaluate(item, filter_query):
                    if projection:
                        return {key: item[key] for key in projection if key in item}
                    return item

            return None
        except Exception as e:
            raise ElectrusException(f"Error finding data: {e}")
