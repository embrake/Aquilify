from typing import Any, Dict, Union

from .exceptions import ValidationError, FieldValidationError

class Schema:
    def __init__(self) -> None:
        pass

    @classmethod
    async def loads(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        return await cls._load(data)

    @classmethod
    async def dumps(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        return await cls._dump(data)

    @classmethod
    async def validate(cls, data: Dict[str, Any], partial: bool = False) -> Dict[str, Any]:
        validated_data = {}
        errors = {}
        for field_name, field_obj in cls.__dict__.items():
            if isinstance(field_obj, Field):
                field_data = data.get(field_name)
                if field_data is None and field_obj.required and not partial:
                    error_message = field_obj.error_messages.get("required", f"{field_name} is required.")
                    errors[field_name] = error_message
                if field_data is not None:
                    try:
                        if hasattr(field_obj, 'pre_load'):
                            field_data = await field_obj.pre_load(field_data)
                        if isinstance(field_obj, Schema):
                            validated_data[field_name] = await field_obj.validate(field_data)
                        else:
                            validated_data[field_name] = await field_obj.validate(field_data)
                    except ValidationError as e:
                        errors[field_name] = str(e)

        print(errors)
        if errors:
            raise FieldValidationError("Validation failed", errors)
        return validated_data

    @classmethod
    async def is_valid(cls, data: Dict[str, Any], partial: bool = False) -> bool:
        try:
            await cls.validate(data, partial=partial)
            return True
        except FieldValidationError:
            return False

    @classmethod
    async def _load(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        return await cls._process_data(data, validation=True)

    @classmethod
    async def _dump(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        return await cls._process_data(data, validation=False)

    @classmethod
    async def _process_data(cls, data: Dict[str, Any], validation: bool = True) -> Dict[str, Any]:
        processed_data = {}
        errors = {}
        for field_name, field_obj in cls.__dict__.items():
            if isinstance(field_obj, Field):
                field_data = data.get(field_name)
                if (field_data is None and field_obj.required and validation) or (field_data is not None and not validation):
                    error_message = field_obj.error_messages.get("required", f"{field_name} is required.")
                    errors[field_name] = error_message
                if field_data is not None and validation:
                    try:
                        if hasattr(field_obj, 'pre_load'):
                            field_data = await field_obj.pre_load(field_data)
                        if isinstance(field_obj, Schema):
                            processed_data[field_name] = await field_obj.validate(field_data)
                        else:
                            processed_data[field_name] = await field_obj.validate(field_data)
                    except ValidationError as e:
                        errors[field_name] = str(e)
                elif field_data is not None and not validation:
                    try:
                        if hasattr(field_obj, 'post_load'):
                            field_data = await field_obj.post_load(field_data)
                        if isinstance(field_obj, Schema):
                            processed_data[field_name] = await field_obj._dump(field_data)
                        else:
                            processed_data[field_name] = await field_obj.serialize(field_data)
                    except ValidationError as e:
                        errors[field_name] = str(e)
                elif isinstance(field_obj, Schema) and not validation:
                    processed_data[field_name] = None  # Initialize nested Schema instances for serialization
        if errors:
            raise FieldValidationError("Validation failed" if validation else "Serialization failed", errors)
        return processed_data

class Field:
    def __init__(self, required: bool = False, allow_none: bool = False, error_messages: Dict[str, str] = None):
        self.required = required
        self.allow_none = allow_none
        self.error_messages = error_messages if error_messages is not None else {}

    async def validate(self, data: Any) -> Any:
        if data is None and not self.allow_none:
            raise ValidationError(self.error_messages.get("null", "Field cannot be null."))
        return data

    async def serialize(self, data: Any) -> Any:
        if data is None and not self.allow_none:
            raise ValidationError(self.error_messages.get("null", "Field cannot be null."))
        return data

    async def pre_load(self, data: Any) -> Any:
        return data

    async def post_load(self, data: Any) -> Any:
        return data
