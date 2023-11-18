import json
import re
from typing import Any, Dict, Type, Union, List, Callable
from .exceptions import ValidationError

class Field:
    def __init__(
        self,
        field_type: Type,
        required: bool = True,
        default: Any = None,
        validators: Union[None, Callable, List[Callable]] = None,
        constraints: Dict[str, Any] = None,
        error_messages: Union[None, Dict[str, str]] = None
    ):
        self.field_type = field_type
        self.required = required
        self.default = default
        self.validators = validators or []
        self.constraints = constraints or {}
        self.error_messages = error_messages or {}

    def validate(self, value):
        if value is None and not self.required:
            return self.default
        elif value is None and self.required:
            raise ValidationError(self.error_messages.get('required', "Field is required"))

        if self.constraints:
            self._apply_constraints(value)

        for validator in self.validators:
            try:
                validator(value)
            except ValidationError as e:
                raise ValidationError(self.error_messages.get('validator', f"Validation failed: {e.message}"))

        return value

    def _apply_constraints(self, value):
        if 'min_length' in self.constraints and len(value) < self.constraints['min_length']:
            raise ValidationError(self.error_messages.get('min_length', f"Value length should be at least {self.constraints['min_length']}"))

        if 'max_length' in self.constraints and len(value) > self.constraints['max_length']:
            raise ValidationError(self.error_messages.get('max_length', f"Value length should not exceed {self.constraints['max_length']}"))

        if isinstance(value, (int, float)):
            if 'min_value' in self.constraints and value < self.constraints['min_value']:
                raise ValidationError(self.error_messages.get('min_value', f"Value should be at least {self.constraints['min_value']}"))

            if 'max_value' in self.constraints and value > self.constraints['max_value']:
                raise ValidationError(self.error_messages.get('max_value', f"Value should not exceed {self.constraints['max_value']}"))

class Polin:
    def __init__(self, **data):
        self.fields = self.__annotations__
        self.validated_data = self.validate_data(data)

    def validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data = {}
        for attr, attr_type in self.fields.items():
            field = getattr(self, attr)
            value = data.get(attr)

            try:
                validated_value = field.validate(value)
                validated_data[attr] = validated_value
            except ValidationError as e:
                raise ValidationError(f"Validation error in field '{attr}': {e.message}")

        return validated_data

    def dict(self) -> Dict[str, Any]:
        return self.validated_data

    def json(self) -> str:
        return json.dumps(self.validated_data)

class EmailField(Field):
    def __init__(self, required: bool = True, error_messages: Union[None, Dict[str, str]] = None):
        super().__init__(str, required=required, validators=[self.validate_email], error_messages=error_messages)

    @staticmethod
    def validate_email(value):
        email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_regex.match(value):
            raise ValidationError("Invalid email format")
        return True
    
class NumericField(Field):
    def __init__(self, field_type: Type, **kwargs):
        super().__init__(field_type, **kwargs)
        self.validators.append(self.validate_numeric)

    @staticmethod
    def validate_numeric(value):
        if not isinstance(value, (int, float)):
            raise ValidationError("Invalid numeric value")
        return True

class ListField(Field):
    def __init__(self, inner_field: Field, **kwargs):
        super().__init__(list, **kwargs)
        self.inner_field = inner_field

    def validate(self, value):
        value = super().validate(value)
        return [self.inner_field.validate(item) for item in value]

class ModelField(Field):
    def __init__(self, model_class: Type['Polin'], required: bool = True, error_messages: Union[None, Dict[str, str]] = None):
        super().__init__(dict, required=required, validators=[self.validate_model], error_messages=error_messages)
        self.model_class = model_class

    def validate_model(self, value):
        if not isinstance(value, dict):
            raise ValidationError("Invalid type. Expected dictionary for nested model")
        
        try:
            model_instance = self.model_class(**value)
            return model_instance.dict()
        except ValidationError as e:
            raise ValidationError(f"Validation error in nested model '{self.model_class.__name__}': {e.message}")