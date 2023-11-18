import os
import json
import platform
from typing import Callable, Any, Type
from enum import Enum

class ConfigError(Exception):
    pass

class Config:
    def __init__(self, prefix='', env_prefix='', system_env=True):
        self.config = {}
        self.prefix = prefix
        self.env_prefix = env_prefix
        if system_env:
            self.load('env')

    def _detect_system(self):
        return platform.system().lower()

    def _get_env_prefix_by_system(self):
        system = self._detect_system()
        return f'{self.env_prefix}_{system.upper()}' if self.env_prefix else system.upper()

    def from_object(self, obj):
        for key in dir(obj):
            if key.isupper():
                self.config[key] = getattr(obj, key)

    def from_env(self):
        env_prefix = self._get_env_prefix_by_system()
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                self.config[key[len(env_prefix):].upper()] = self._cast_value(value)

    def from_json_file(self, file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                self.config.update(data)
        except FileNotFoundError as e:
            raise ConfigError(f"Config file not found: {file_path}") from e
        except json.JSONDecodeError as e:
            raise ConfigError(f"Error decoding JSON in config file: {file_path}") from e

    def load(self, source, system_env=True):
        if source.lower() == 'env':
            self.from_env()
        elif source.lower().endswith('.json'):
            self.from_json_file(source)
        else:
            raise ConfigError(f"Unsupported configuration source: {source}")

    def get(self, key, default=None, expected_type=None, validator=None):
        value = self.config.get(key, default)
        return self._validate_and_cast(value, key, expected_type, validator)

    def set(self, key, value):
        self.config[key] = self._cast_value(value)

    def set_dict(self, values):
        if not isinstance(values, dict):
            raise ConfigError("Input must be a dictionary")
        for key, value in values.items():
            self.set(key, value)

    def validate(self, key, validator: Callable[[Any], bool], default=None):
        value = self.config.get(key, default)
        if not validator(value):
            raise ConfigError(f"Invalid value for key '{key}'")
        return value

    def get_nested(self, keys, default=None, expected_type=None, validator=None):
        current = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return self._validate_and_cast(current, keys[-1], expected_type, validator)

    def set_nested(self, keys, value):
        current = self.config
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = self._cast_value(value)

    def get_typed(self, key, expected_type: Type, default=None):
        value = self.config.get(key, default)
        return self._validate_and_cast(value, key, expected_type)

    def get_list(self, key, delimiter=',', expected_type=None):
        value = self.config.get(key, '')
        items = [self._validate_and_cast(item.strip(), key, expected_type) for item in value.split(delimiter)]
        return items

    def get_dict(self, key, delimiter=':', pair_delimiter=',', key_type=None, value_type=None):
        value = self.config.get(key, '')
        items = [item.split(delimiter, 1) for item in value.split(pair_delimiter)]
        result_dict = {}

        for item in items:
            if len(item) == 2:
                key, value = item
                key = self._validate_and_cast(key.strip(), key, key_type)
                value = self._validate_and_cast(value.strip(), key, value_type)
                result_dict[key] = value

        return result_dict

    def get_enum(self, key, enum_type: Type[Enum], default=None):
        value = self.config.get(key, default)
        if value is not None:
            try:
                return enum_type[value]
            except KeyError:
                raise ConfigError(f"Invalid value '{value}' for enum {enum_type.__name__}")

    def _cast_value(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
            elif value.isdigit():
                return int(value)
            elif value.replace('.', '', 1).isdigit():
                return float(value)
        return value

    def _validate_and_cast(self, value, key, expected_type, validator):
        if expected_type and not isinstance(value, expected_type):
            raise ConfigError(f"Invalid type for value '{value}' of key '{key}'. Expected {expected_type}")

        if validator and not validator(value):
            raise ConfigError(f"Invalid value '{value}' for key '{key}'")

        return value

    def reload(self, system_env=True):
        self.config.clear()
        self.load('env', system_env)

    def export(self, format='json'):
        if format.lower() == 'json':
            return json.dumps(self.config, indent=2)
        else:
            raise ConfigError(f"Unsupported export format: {format}")

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.set(key, value)

    def __repr__(self):
        return repr(self.config)