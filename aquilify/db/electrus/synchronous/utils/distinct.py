from typing import Any, Dict, List, Optional, Union
from ...exception.base import ElectrusException
from ..partials import ElectrusLogicalOperators

import json

class DistinctOperation:
    def __init__(self, collection_path: str):
        self.collection_path = collection_path

    def _read_collection_data(self) -> List[Dict[str, Any]]:
        try:
            with open(self.collection_path, 'r') as file:
                return json.loads(file.read())
        except Exception as e:
            raise ElectrusException(f"Error reading collection data: {e}")

    def _distinct(
        self,
        field: str,
        filter_query: Optional[Dict[str, Any]] = None,
        sort: Optional[bool] = False
    ) -> Union[List[Any], None]:
        try:
            collection_data = self._read_collection_data()
            distinct_values = {item.get(field) for item in collection_data if item.get(field) is not None}

            if filter_query:
                distinct_values = {
                    item.get(field) for item in collection_data
                    if all(
                        ElectrusLogicalOperators().evaluate(item, {field: filter_query[field]})
                        if field in filter_query else True
                        for field in item.keys()
                    )
                }

            distinct_values = list(distinct_values)
            if sort:
                distinct_values.sort()

            return distinct_values
        except Exception as e:
            raise ElectrusException(f"Error retrieving distinct values: {e}")
