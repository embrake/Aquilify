from typing import Any, Dict, List, Optional

class Aggregation:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data

    def group(self, field: str) -> Dict[Any, List[Dict[str, Any]]]:
        grouped_data = {}
        for item in self.data:
            key = item.get(field)
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(item)
        return grouped_data

    def count(self) -> int:
        return len(self.data)

    def sum(self, field: str) -> Optional[float]:
        values = [item.get(field, 0) for item in self.data if isinstance(item.get(field), (int, float))]
        return sum(values) if values else None

    def average(self, field: str) -> Optional[float]:
        values = [item.get(field, 0) for item in self.data if isinstance(item.get(field), (int, float))]
        return sum(values) / len(values) if values else None

    def max(self, field: str) -> Any:
        values = [item.get(field) for item in self.data]
        return max(values) if values else None

    def min(self, field: str) -> Any:
        values = [item.get(field) for item in self.data]
        return min(values) if values else None

    def project(self, fields: List[str]) -> List[Dict[str, Any]]:
        return [{field: item.get(field) for field in fields} for item in self.data]

    def match(self, filter_query: Dict[str, Any]) -> List[Dict[str, Any]]:        
        return [item for item in self.data if all(item.get(key) == value for key, value in filter_query.items())]

    def sort(self, field: str, reverse: bool = False) -> List[Dict[str, Any]]:
        return sorted(self.data, key=lambda x: x.get(field), reverse=reverse)

    def limit(self, limit_value: int) -> List[Dict[str, Any]]:
        return self.data[:limit_value]

    def skip(self, skip_value: int) -> List[Dict[str, Any]]:
        return self.data[skip_value:]
    
    def sample(self, size: int) -> List[Dict[str, Any]]:
        import random
        return random.sample(self.data, size) if size <= len(self.data) else self.data

    def unwind(self, field: str) -> List[Dict[str, Any]]:
        unwound_data = []
        for item in self.data:
            field_data = item.get(field)
            if isinstance(field_data, list):
                for value in field_data:
                    new_item = item.copy()
                    new_item[field] = value
                    unwound_data.append(new_item)
            else:
                unwound_data.append(item)
        return unwound_data

    def lookup(self, from_collection: List[Dict[str, Any]], local_field: str, foreign_field: str, as_field: str) -> List[Dict[str, Any]]:
        merged_data = []
        for item in self.data:
            local_value = item.get(local_field)
            matching_items = [doc for doc in from_collection if doc.get(foreign_field) == local_value]
            if matching_items:
                for match in matching_items:
                    new_item = item.copy()
                    new_item[as_field] = match
                    merged_data.append(new_item)
            else:
                new_item = item.copy()
                new_item[as_field] = None
                merged_data.append(new_item)
        return merged_data
    
    def bucket(self, group_by: str, boundaries: List[float]) -> Dict[str, List[Dict[str, Any]]]:
        bucketed_data = {str(boundary): [] for boundary in boundaries}
        for item in self.data:
            value = item.get(group_by)
            for i, boundary in enumerate(boundaries):
                if i == len(boundaries) - 1:
                    if value >= boundary:
                        bucketed_data[str(boundary)].append(item)
                        break
                elif boundary <= value < boundaries[i + 1]:
                    bucketed_data[str(boundary)].append(item)
                    break
        return bucketed_data

    def add_fields(self, fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        for item in self.data:
            for key, value in fields.items():
                item[key] = value
        return self.data

    def facet(self, pipeline: List[List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
        results = {}
        for sub_pipeline in pipeline:
            new_aggregation = Aggregation(self.data)
            result = new_aggregation.execute(sub_pipeline)
            results[str(id(sub_pipeline))] = result
        return results

    def execute(self, pipeline: List[Dict[str, Any]]) -> Any:
        result = self.data
        try:
            for stage in pipeline:
                for operation, value in stage.items():
                    if operation == '$group':
                        field = value.get('_id')
                        result = self.group(field)
                    elif operation == '$count':
                        result = self.count()
                    elif operation == '$sum':
                        field = value
                        result = self.sum(field)
                    elif operation == '$avg':
                        field = value
                        result = self.average(field)
                    elif operation == '$max':
                        field = value
                        result = self.max(field)
                    elif operation == '$min':
                        field = value
                        result = self.min(field)
                    elif operation == '$project':
                        fields = value
                        result = self.project(fields)
                    elif operation == '$match':
                        filter_query = value
                        result = self.match(filter_query)
                    elif operation == '$sort':
                        field = value.get('field')
                        reverse = value.get('reverse', False)
                        result = self.sort(field, reverse)
                    elif operation == '$limit':
                        limit_value = value
                        result = self.limit(limit_value)
                    elif operation == '$skip':
                        skip_value = value
                        result = self.skip(skip_value)
                    elif operation == '$bucket':
                        group_by = value.get('groupBy')
                        boundaries = value.get('boundaries')
                        result = self.bucket(group_by, boundaries)
                    elif operation == '$addFields':
                        fields = value
                        result = self.add_fields(fields)
                    elif operation == '$facet':
                        sub_pipeline = value
                        result = self.facet(sub_pipeline)
                    elif operation == '$sample':
                        size = value
                        result = self.sample(size)
                    elif operation == '$unwind':
                        field = value
                        result = self.unwind(field)
                    elif operation == '$lookup':
                        from_collection = value.get('from')
                        local_field = value.get('localField')
                        foreign_field = value.get('foreignField')
                        as_field = value.get('as')
                        result = self.lookup(from_collection, local_field, foreign_field, as_field)
                    else:
                        raise ValueError(f"Unsupported operation: {operation}")
            return result
        except Exception as e:
            raise ValueError(f"Error in aggregation pipeline: {e}")
