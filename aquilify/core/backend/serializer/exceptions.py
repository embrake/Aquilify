# noql exceptions: 306

import json

class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class SchemaLoadError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class FieldValidationError(Exception):
    def __init__(self, field_name, message):
        self.field_name = field_name
        self.message = message if isinstance(message, dict) else self._parse_json(message)
        super().__init__(f"Error in field '{field_name}': {json.dumps(self.message)}")

    def _parse_json(self, message):
        try:
            return json.loads(message.replace("'", '"'))
        except json.JSONDecodeError as e:
            return {"message": message}

    @property
    def json(self):
        return self.message
        
class FieldRequiredError(Exception):
    def __init__(self, field_name):
        self.field_name = field_name
        self.message = f"Field '{field_name}' is required but missing."
        super().__init__(self.message)

class FieldNotAllowedError(Exception):
    def __init__(self, field_name):
        self.field_name = field_name
        self.message = f"Field '{field_name}' is not allowed."
        super().__init__(self.message)


class FieldLengthError(Exception):
    def __init__(self, field_name, min_length=None, max_length=None):
        self.field_name = field_name
        self.min_length = min_length
        self.max_length = max_length
        if min_length and max_length:
            self.message = f"Length of field '{field_name}' should be between {min_length} and {max_length}."
        elif min_length:
            self.message = f"Length of field '{field_name}' should be at least {min_length}."
        elif max_length:
            self.message = f"Length of field '{field_name}' should not exceed {max_length}."
        else:
            self.message = f"Invalid length for field '{field_name}'."
        super().__init__(self.message)


class FieldValueError(Exception):
    def __init__(self, field_name, value):
        self.field_name = field_name
        self.value = value
        self.message = f"Invalid value '{value}' for field '{field_name}'."
        super().__init__(self.message)