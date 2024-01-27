import json
import typing

from enum import Enum

class EnumEncoder(json.JSONEncoder):
    def default(self, obj: typing.Any) -> typing.Any:
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)