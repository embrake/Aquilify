import re
import imghdr
import uuid
from urllib.parse import urlparse

from datetime import datetime
from typing import Any, Dict, List as ListType, Union

from .exceptions import (
    ValidationError,
    FieldValidationError
)

from .schema import Schema
from .schema import Field

class String(Field):
    def __init__(self, required: bool = False, min_length: int = None, max_length: int = None, regex: str = None, allow_blank: bool = False, strip_whitespace: bool = False, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex
        self.allow_blank = allow_blank
        self.strip_whitespace = strip_whitespace

    async def validate(self, data: Any) -> str:
        if not isinstance(data, str):
            raise ValidationError(self.error_messages.get("validation", "Invalid data type. Expected string."))

        if self.strip_whitespace:
            data = data.strip()

        if not self.allow_blank and not data:
            raise ValidationError(self.error_messages.get("blank", "Field cannot be blank."))

        if self.min_length is not None and len(data) < self.min_length:
            raise ValidationError(f"Value must be at least {self.min_length} characters long.")

        if self.max_length is not None and len(data) > self.max_length:
            raise ValidationError(f"Value cannot exceed {self.max_length} characters.")

        if self.regex is not None and not re.match(self.regex, data):
            raise ValidationError(self.error_messages.get("invalid", "Invalid format."))

        return data

    async def serialize(self, data: str) -> str:
        if self.strip_whitespace:
            data = data.strip()

        if not self.allow_blank and not data:
            raise ValidationError(self.error_messages.get("blank", "Field cannot be blank."))

        return data

    async def serialize(self, data: str) -> str:
        if data is None and not self.allow_none:
            raise ValidationError(self.error_messages.get("null", "Field cannot be null."))
        return data


class Email(Field):
    USER_REGEX = r"(?=^.{1,64}$)^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    DOMAIN_REGEX = r"(?=^.{1,253}$)(?:(?:\.{1}|\.{0,1}[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*\.{1}[a-zA-Z]{2,})$"

    def __init__(self, required: bool = False, error_messages: Dict[str, str] = None, allow_name: bool = False, domain_whitelist: ListType[str] = None, domain_blacklist: ListType[str] = None):
        super().__init__(required, error_messages)
        self.allow_name = allow_name
        self.domain_whitelist = domain_whitelist or []
        self.domain_blacklist = domain_blacklist or []

    async def validate(self, data: Any) -> str:
        if not isinstance(data, str):
            raise ValidationError("Invalid data type. Expected string.")

        email_regex = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,4}$'

        if not self.allow_name:
            email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        match = re.match(email_regex, data)
        if not match:
            raise ValidationError(self.error_messages.get("invalid", "Invalid email format."))

        if match:
            email = match.group()
            email_parts = email.split('@')
            email_local_part = email_parts[0]
            email_domain = email_parts[1]

            if not re.match(self.USER_REGEX, email_local_part):
                raise ValidationError(self.error_messages.get("local_part", "Invalid email local part."))

            if not re.match(self.DOMAIN_REGEX, email_domain):
                raise ValidationError(self.error_messages.get("domain", "Invalid email domain."))

            if self.domain_whitelist and email_domain not in self.domain_whitelist:
                raise ValidationError(self.error_messages.get("domain", "Email domain is not allowed."))

            if self.domain_blacklist and email_domain in self.domain_blacklist:
                raise ValidationError(self.error_messages.get("domain", "Email domain is blacklisted."))

        return data

    async def serialize(self, data: str) -> str:
        return data
    
class Integer(Field):
    def __init__(self, required: bool = False, allow_negative: bool = True, min_value: int = None, max_value: int = None, error_messages: Dict[str, str] = None, allow_divisible_by: int = None, allow_even: bool = False, allow_odd: bool = False):
        super().__init__(required, error_messages)
        self.allow_negative = allow_negative
        self.min_value = min_value
        self.max_value = max_value
        self.allow_divisible_by = allow_divisible_by
        self.allow_even = allow_even
        self.allow_odd = allow_odd

    async def validate(self, data: Any) -> int:
        if not isinstance(data, int):
            raise ValidationError("Invalid data type. Expected integer.")

        if not self.allow_negative and data < 0:
            raise ValidationError(self.error_messages.get("negative", "Value cannot be negative."))

        if self.min_value is not None and data < self.min_value:
            raise ValidationError(f"Value must be greater than or equal to {self.min_value}.")

        if self.max_value is not None and data > self.max_value:
            raise ValidationError(f"Value must be less than or equal to {self.max_value}.")

        if self.allow_even and data % 2 != 0:
            raise ValidationError("Value must be even.")

        if self.allow_odd and data % 2 == 0:
            raise ValidationError("Value must be odd.")

        if self.allow_divisible_by and data % self.allow_divisible_by != 0:
            raise ValidationError(f"Value must be divisible by {self.allow_divisible_by}.")

        return data

    async def serialize(self, data: int) -> int:
        return data

class Float(Field):
    def __init__(self, required: bool = False, min_value: float = None, max_value: float = None, allow_nan: bool = True, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.min_value = min_value
        self.max_value = max_value
        self.allow_nan = allow_nan

    async def validate(self, data: Any) -> float:
        if data is None and not self.allow_none:
            raise ValidationError(self.error_messages.get("null", "Field cannot be null."))

        if data is not None:
            try:
                float_data = float(data)
            except (ValueError, TypeError):
                raise ValidationError(self.error_messages.get("invalid", "Invalid data type. Expected float."))

            if not self.allow_nan and (float('nan') == float_data or float('-nan') == float_data):
                raise ValidationError(self.error_messages.get("nan", "Field does not allow NaN."))

            if self.min_value is not None or self.max_value is not None:
                if self.min_value is not None and self.max_value is not None:
                    if not self.min_value <= float_data <= self.max_value:
                        raise ValidationError(f"Value must be between {self.min_value} and {self.max_value}.")
                elif self.min_value is not None:
                    if float_data < self.min_value:
                        raise ValidationError(f"Value must be greater than or equal to {self.min_value}.")
                elif self.max_value is not None:
                    if float_data > self.max_value:
                        raise ValidationError(f"Value must be less than or equal to {self.max_value}")

        return float_data

    async def serialize(self, data: float) -> float:
        if data is None and not self.allow_none:
            raise ValidationError(self.error_messages.get("null", "Field cannot be null."))
        return data

class Date(Field):
    def __init__(self, required: bool = False, format: str = "%Y-%m-%d", min_date: str = None, max_date: str = None, allow_none: bool = False, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.format = format
        self.min_date = min_date
        self.max_date = max_date
        self.allow_none = allow_none

    async def validate(self, data: Any) -> str:
        if data is None and not self.allow_none:
            raise ValidationError(self.error_messages.get("null", "Field cannot be null."))

        if data is not None:
            try:
                parsed_date = datetime.strptime(data, self.format).date()
            except ValueError:
                raise ValidationError(self.error_messages.get("invalid", f"Invalid date format. Expected '{self.format}'."))

            if self.min_date is not None and parsed_date < datetime.strptime(self.min_date, self.format).date():
                raise ValidationError(f"Date should be after {self.min_date}.")
            
            if self.max_date is not None and parsed_date > datetime.strptime(self.max_date, self.format).date():
                raise ValidationError(f"Date should be before {self.max_date}.")

        return data

    async def serialize(self, data: str) -> str:
        if data is None and not self.allow_none:
            raise ValidationError(self.error_messages.get("null", "Field cannot be null."))
        return data
    
class NestedSchema(Field):
    def __init__(self, schema: Schema, required: bool = False, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.schema = schema

    async def validate(self, data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("Invalid data type. Expected dictionary.")

        try:
            return await self._validate_nested_schema(data)
        except ValidationError as e:
            raise ValidationError(f"Nested schema validation failed: {e.message}")

    async def _validate_nested_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not data:
            if self.required:
                raise ValidationError("Nested data is required.")
            return {}

        validated_data = {}
        errors = {}
        
        for field_name, field_obj in self.schema.__dict__.items():
            if isinstance(field_obj, Field):
                field_data = data.get(field_name)
                if field_data is None and field_obj.required:
                    error_message = field_obj.error_messages.get("required", f"{field_name} is required.")
                    errors[field_name] = error_message
                if field_data is not None:
                    try:
                        validated_data[field_name] = await field_obj.validate(field_data)
                    except ValidationError as e:
                        errors[field_name] = str(e)

        if errors:
            raise FieldValidationError("Validation failed", errors)
        
        return validated_data

    async def serialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.schema.dumps(data)

class Bool(Field):
    def __init__(self, required: bool = False, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)

    async def validate(self, data: Any) -> bool:
        if isinstance(data, str):
            data = data.lower()
            if data in ['true', 't', 'yes', 'y', '1', 'false', 'f', 'no', 'n', '0']:
                return data in ['true', 't', 'yes', 'y', '1']
            else:
                raise ValidationError("Invalid boolean string representation.")

        if not isinstance(data, bool):
            raise ValidationError("Invalid data type. Expected boolean.")
        return data

    async def serialize(self, data: bool) -> bool:
        return data

class RegexMemorizer:
    _cache = {}

    @classmethod
    def compile(cls, pattern):
        if pattern not in cls._cache:
            cls._cache[pattern] = re.compile(pattern)
        return cls._cache[pattern]

class URL(Field):
    def __init__(self, required: bool = False, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.default_schemes = {'http', 'https', 'ftp', 'ftps'}
        self.scheme_re = RegexMemorizer.compile(r'^[a-z][a-z0-9+.-]*$')
        self.absolute_re = RegexMemorizer.compile(r'^/[^/\\]')
        self.relative_re = RegexMemorizer.compile(r'^[^/\\]')
        self.path_segment_re = RegexMemorizer.compile(r'^[^/\\]*$')

    async def validate(self, data: Any) -> str:
        if data is None:
            if self.required:
                raise ValidationError(self.error_messages.get("required", "Field is required."))
            return data

        if not isinstance(data, str):
            raise ValidationError("Invalid data type. Expected string.")

        parsed_url = urlparse(data)

        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValidationError("Invalid URL format: Missing scheme or network location.")

        if parsed_url.scheme not in self.default_schemes:
            raise ValidationError("Invalid URL scheme. Only 'http', 'https', 'ftp', or 'ftps' schemes are allowed.")

        if not self.scheme_re.match(parsed_url.scheme):
            raise ValidationError("Invalid URL scheme format.")

        if parsed_url.port:
            if not (0 <= parsed_url.port <= 65535):
                raise ValidationError("Invalid URL port. Port must be between 0 and 65535.")

        domain_parts = parsed_url.netloc.split(':')
        domain = domain_parts[0]

        if not domain:
            raise ValidationError("Invalid URL format: Missing or invalid domain.")

        if domain != 'localhost':
            if len(domain.split('.')) <= 1 or len(domain.split('.')[-1]) < 2:
                raise ValidationError("Invalid URL format: Missing or invalid domain.")

        domain_name = domain.split('.')[-1]
        if domain_name != 'localhost' and not re.match(r'^[a-zA-Z0-9-]+$', domain_name):
            raise ValidationError("Invalid URL format: Domain contains invalid characters.")

        return data

    async def serialize(self, data: str) -> str:
        return data
    
class IPAddress(Field):
    def __init__(self, required: bool = False, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)

    async def validate(self, data: Any) -> str:
        if not isinstance(data, str):
            raise ValidationError("Invalid data type. Expected string.")

        ip_regex = r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if not re.match(ip_regex, data):
            raise ValidationError("Invalid IP address format.")
        return data

    async def serialize(self, data: str) -> str:
        return data
    
class Range(Field):
    def __init__(
        self,
        min: Union[int, float, None] = None,
        max: Union[int, float, None] = None,
        min_inclusive: bool = True,
        max_inclusive: bool = True,
        error_messages: Dict[str, str] = None,
    ):
        super().__init__(error_messages=error_messages)
        self.min_value = min
        self.max_value = max
        self.min_inclusive = min_inclusive
        self.max_inclusive = max_inclusive

    async def validate(self, data: Union[int, float]) -> Union[int, float]:
        error_messages = []

        if self.min_value is not None:
            if self.min_inclusive:
                if data < self.min_value:
                    error_messages.append(f"Value must be greater than or equal to {self.min_value}.")
            else:
                if data <= self.min_value:
                    error_messages.append(f"Value must be greater than {self.min_value}.")

        if self.max_value is not None:
            if self.max_inclusive:
                if data > self.max_value:
                    error_messages.append(f"Value must be less than or equal to {self.max_value}.")
            else:
                if data >= self.max_value:
                    error_messages.append(f"Value must be less than {self.max_value}.")

        if error_messages:
            raise ValidationError(", ".join(error_messages))

        return data

    async def serialize(self, data: Union[int, float]) -> Union[int, float]:
        return data

class Age(Field):
    def __init__(self, required: bool = False, min_age: int = None, max_age: int = None, age_range: Range = None, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.min_age = min_age
        self.max_age = max_age
        self.age_range = age_range

    async def validate(self, data: Any) -> int:
        if self.age_range:
            return await self.age_range.validate(data)

        if not isinstance(data, int):
            raise ValidationError("Age must be an integer.")

        if data < 0:
            raise ValidationError("Age cannot be negative.")

        if self.min_age is not None and data < self.min_age:
            raise ValidationError(f"Age should be at least {self.min_age} years.")

        if self.max_age is not None and data > self.max_age:
            raise ValidationError(f"Age cannot exceed {self.max_age} years.")

        return data

    async def serialize(self, data: int) -> int:
        return data
    
class Decimal(Field):
    def __init__(self, required: bool = False, min_value: float = None, max_value: float = None, precision: int = None, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.min_value = min_value
        self.max_value = max_value
        self.precision = precision

    async def validate(self, data: Any) -> float:
        if not isinstance(data, (int, float)):
            raise ValidationError(self.error_messages.get("invalid", "Invalid data type. Expected decimal or integer."))

        if isinstance(data, int):
            data = float(data)

        if self.min_value is not None and data < self.min_value:
            raise ValidationError(self.error_messages.get("min_value", f"Value must be greater than or equal to {self.min_value}."))

        if self.max_value is not None and data > self.max_value:
            raise ValidationError(self.error_messages.get("max_value", f"Value must be less than or equal to {self.max_value}"))

        if self.precision is not None:
            precision_str = str(data).split('.')
            if len(precision_str) > 1 and len(precision_str[1]) > self.precision:
                raise ValidationError(self.error_messages.get("precision", f"Value can have at most {self.precision} decimal places."))

        return data

    async def serialize(self, data: float) -> float:
        return data

class ListField(Field):
    def __init__(self, inner_field: Field, min_length: int = None, max_length: int = None, custom_validator=None, **kwargs):
        super().__init__(**kwargs)
        self.inner_field = inner_field
        self.min_length = min_length
        self.max_length = max_length
        self.custom_validator = custom_validator

    async def validate(self, data: Any) -> ListType:
        if not isinstance(data, list):
            raise ValidationError(self.error_messages.get("invalid", "Field must be a list."))

        if self.min_length is not None and len(data) < self.min_length:
            raise ValidationError(self.error_messages.get("min_length", f"List length should be at least {self.min_length}"))

        if self.max_length is not None and len(data) > self.max_length:
            raise ValidationError(self.error_messages.get("max_length", f"List length should be at most {self.max_length}"))

        if self.custom_validator:
            try:
                await self.custom_validator(data)
            except ValidationError as e:
                raise ValidationError(str(e))

        validated_data = []
        for index, item in enumerate(data):
            try:
                validated_item = await self.validate_item(item, index)
                validated_data.append(validated_item)
            except ValidationError as e:
                raise ValidationError({f"item_{index}": str(e)})
        return validated_data

    async def validate_item(self, item: Any, index: int) -> Any:
        try:
            validated_item = await self.inner_field.validate(item)
        except ValidationError as e:
            raise ValidationError({f"item_{index}": str(e)})
        return validated_item

    async def serialize(self, data: Any) -> ListType:
        if not isinstance(data, list):
            raise ValidationError(self.error_messages.get("invalid", "Field must be a list."))

        if self.min_length is not None and len(data) < self.min_length:
            raise ValidationError(self.error_messages.get("min_length", f"List length should be at least {self.min_length}"))

        if self.max_length is not None and len(data) > self.max_length:
            raise ValidationError(self.error_messages.get("max_length", f"List length should be at most {self.max_length}"))

        if self.custom_validator:
            try:
                await self.custom_validator(data)
            except ValidationError as e:
                raise ValidationError(str(e))

        serialized_data = []
        for index, item in enumerate(data):
            try:
                serialized_item = await self.serialize_item(item, index)
                serialized_data.append(serialized_item)
            except ValidationError as e:
                raise ValidationError({f"item_{index}": str(e)})
        return serialized_data

    async def serialize_item(self, item: Any, index: int) -> Any:
        try:
            serialized_item = await self.inner_field.serialize(item)
        except ValidationError as e:
            raise ValidationError({f"item_{index}": str(e)})
        return serialized_item

class UUID(Field):
    def __init__(self, required: bool = False, version: int = None, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.version = version

    async def validate(self, data: Any) -> str:
        if not isinstance(data, str):
            raise ValidationError(self.error_messages.get("invalid", "Invalid data type. Expected string."))

        try:
            uuid_obj = uuid.UUID(data)
        except ValueError:
            raise ValidationError(self.error_messages.get("format", "Invalid UUID format."))

        if self.version is not None and uuid_obj.version != self.version:
            raise ValidationError(self.error_messages.get("version", f"UUID should be version {self.version}."))

        return data

    async def serialize(self, data: str) -> str:
        return data


class File(Field):
    def __init__(self, required: bool = False, allowed_extensions: ListType[str] = None, max_size: int = None, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.allowed_extensions = allowed_extensions
        self.max_size = max_size

    async def validate(self, data: Any) -> Any:
        if not isinstance(data, bytes):
            raise ValidationError(self.error_messages.get("invalid", "Invalid file data."))

        if self.allowed_extensions:
            file_ext = imghdr.what(None, h=data)
            if file_ext not in self.allowed_extensions:
                raise ValidationError(self.error_messages.get("extensions", f"File extension not allowed. Allowed extensions: {', '.join(self.allowed_extensions)}"))

        if self.max_size is not None and len(data) > self.max_size:
            raise ValidationError(self.error_messages.get("max_size", f"File size exceeds the maximum allowed size: {self.max_size} bytes."))

        return data

    async def serialize(self, data: Any) -> Any:
        return data 
    
class Password(Field):
    def __init__(
        self,
        required: bool = False,
        min_length: int = 8,
        max_length: int = 64,
        special_chars: bool = True,
        uppercase: bool = True,
        lowercase: bool = True,
        numbers: bool = True,
        consecutive_chars: int = 3,
        error_messages: Dict[str, str] = None,
    ):
        super().__init__(required, error_messages)
        self.min_length = min_length
        self.max_length = max_length
        self.special_chars = special_chars
        self.uppercase = uppercase
        self.lowercase = lowercase
        self.numbers = numbers
        self.consecutive_chars = consecutive_chars

    async def validate(self, data: Any) -> str:
        if not isinstance(data, str):
            raise ValidationError("Invalid data type. Expected string.")

        if self.min_length > self.max_length:
            raise ValidationError("Minimum password length cannot be greater than maximum.")

        if len(data) < self.min_length:
            raise ValidationError(f"Password must be at least {self.min_length} characters long.")

        if len(data) > self.max_length:
            raise ValidationError(f"Password cannot exceed {self.max_length} characters.")

        if not self._check_password_complexity(data):
            raise ValidationError("Password complexity requirements not met.")

        if not self._check_consecutive_chars(data):
            raise ValidationError(f"Password should not contain {self.consecutive_chars} consecutive identical characters.")

        return data

    async def serialize(self, data: str) -> str:
        return data

    def _check_password_complexity(self, password: str) -> bool:
        has_special_chars = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)) if self.special_chars else True
        has_uppercase = bool(re.search(r"[A-Z]", password)) if self.uppercase else True
        has_lowercase = bool(re.search(r"[a-z]", password)) if self.lowercase else True
        has_numbers = bool(re.search(r"\d", password)) if self.numbers else True

        return has_special_chars and has_uppercase and has_lowercase and has_numbers

    def _check_consecutive_chars(self, password: str) -> bool:
        for i in range(len(password) - self.consecutive_chars + 1):
            if len(set(password[i : i + self.consecutive_chars])) == 1:
                return False
        return True

class And(Field):
    def __init__(self, fields: ListType[Field], error_messages: Dict[str, str] = None):
        super().__init__(error_messages=error_messages)
        self.fields = fields

    async def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        errors = {}

        for field in self.fields:
            try:
                validated_data = await field.validate(data)
                data.update(validated_data)
            except ValidationError as e:
                field_name = f"AND_{e.field_name}"
                errors[field_name] = e.message

        if errors:
            raise FieldValidationError("Validation failed", errors)

        return data

    async def serialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        serialized_data = {}
        errors = {}

        for field in self.fields:
            try:
                serialized_field = await field.serialize(data)
                serialized_data.update(serialized_field)
            except ValidationError as e:
                field_name = f"AND_{e.field_name}"
                errors[field_name] = e.message

        if errors:
            raise FieldValidationError("Serialization failed", errors)

        return serialized_data

class Length(Field):
    def __init__(self, equal: int = None, min_length: int = None, max_length: int = None, error_messages: Dict[str, str] = None):
        super().__init__(error_messages=error_messages)
        self.equal = equal
        self.min_length = min_length
        self.max_length = max_length

    async def validate(self, data: Any) -> Any:
        if data is None:
            raise ValidationError("Data is None.")

        try:
            length = len(data)
        except TypeError:
            raise ValidationError("Unable to determine the length of the data.")

        if self.equal is not None and length != self.equal:
            raise ValidationError(f"Length must be {self.equal} characters long.")
        if self.min_length is not None and length < self.min_length:
            raise ValidationError(f"Length must be at least {self.min_length} characters long.")
        if self.max_length is not None and length > self.max_length:
            raise ValidationError(f"Length cannot exceed {self.max_length} characters.")

        return data

    async def serialize(self, data: Any) -> Any:
        return data

class Regexp(Field):
    def __init__(self, regex: str, flags: int = 0, required: bool = False, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.regex = regex
        self.flags = flags
        self.compiled_regex = self.compile_regex(regex, flags)

    @staticmethod
    def compile_regex(pattern, flags):
        try:
            compiled = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regular expression: {e}")
        return compiled

    async def validate(self, data: Any) -> str:
        if data is None:
            if self.required:
                raise ValidationError(self.error_messages.get("required", "Field is required."))
            return data

        if not isinstance(data, str):
            raise ValidationError(self.error_messages.get("invalid", "Value must be a string."))

        if not self.compiled_regex.match(data):
            error_message = self.error_messages.get("invalid", "Does not match the pattern.")
            raise ValidationError(error_message)

        return data

    async def serialize(self, data: str) -> str:
        return data

    def serialize_flags(self):
        return repr(re.ASCII if self.flags & re.ASCII else 0)
    
class Equal(Field):
    def __init__(self, equal_to: str, required: bool = False, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.equal_to = equal_to

    async def validate(self, data: Any) -> str:
        if data is None:
            if self.required:
                raise ValidationError(self.error_messages.get("required", "Field is required."))
            return data

        if data != self.equal_to:
            error_message = self.error_messages.get("invalid", f"Value must be equal to '{self.equal_to}'.")
            raise ValidationError(error_message)

        return data

    async def serialize(self, data: str) -> str:
        return data
    
class Dictonary(Field):
    def __init__(self, required: bool = False, min_items: int = None, max_items: int = None, schema: Schema = None, error_messages: Dict[str, str] = None):
        super().__init__(required, error_messages)
        self.min_items = min_items
        self.max_items = max_items
        self.schema = schema

    async def validate(self, data: Any) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary.")

        if self.min_items is not None and len(data) < self.min_items:
            raise ValidationError(f"Dictionary must have at least {self.min_items} items.")

        if self.max_items is not None and len(data) > self.max_items:
            raise ValidationError(f"Dictionary cannot exceed {self.max_items} items.")

        if self.schema:
            validated_data = {}
            errors = {}
            for key, value in data.items():
                try:
                    validated_value = await self._validate_dict_item(value, key)
                    validated_data[key] = validated_value
                except FieldValidationError as e:
                    errors[key] = e.message
            if errors:
                raise FieldValidationError("Validation failed", errors)
            return validated_data

        return data

    async def _validate_dict_item(self, value: Any, key: str) -> Any:
        if not self.schema:
            return value

        try:
            return await self.schema.validate(value)
        except FieldValidationError as e:
            raise FieldValidationError(f"Error in field '{key}'", e.message)

    async def serialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data
