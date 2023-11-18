# This Enviroment is still under development... -> @noql 14752
# Don't use it for production usage instead use the aquilify.config for production usage

# For use in development create a .lxe file and implement you code there
# Here's the example code ::

# For setting varibales
# MYKEY: str => 'myvalue'  --> You must need to define the type of the varibale due to it's type sensitive nature -> @noql 1866

import os

class LexCrossFilesError(Exception):
    pass

class InvalidSyntaxError(LexCrossFilesError):
    pass

class UnknownTypeError(LexCrossFilesError):
    pass

class TypeMismatchError(LexCrossFilesError):
    pass

class UndefinedVariableError(LexCrossFilesError):
    pass

class VariableRedefinitionError(LexCrossFilesError):
    pass

class LexCrossFiles:
    def __init__(self, filename='default', file_path='', strict_mode=False, env_var_prefix=''):
        self.filename = filename
        self.file_path = file_path if file_path else './'
        self.variables = {}
        self.types = {}
        self.loaded = False
        self.strict_mode = strict_mode
        self.env_var_prefix = env_var_prefix

    def set_filename(self, filename):
        if '.' in filename:
            raise LexCrossFilesError("Please provide the filename without an extension.")
        self.filename = filename

    def set_file_path(self, file_path):
        self.file_path = file_path if file_path else './'

    def set_env_var_prefix(self, env_var_prefix):
        self.env_var_prefix = env_var_prefix

    def load(self):
        if '.' in self.filename:
            raise LexCrossFilesError("Please provide the filename without an extension.")
        file_to_open = os.path.join(self.file_path, f"{self.filename}.lxe")
        if os.path.exists(file_to_open):
            self.loaded = True
            self._parse_file(file_to_open)
        else:
            raise LexCrossFilesError(f"File '{self.filename}.lxe' not found in '{self.file_path}'.")

    def _parse_file(self, file_to_open):
        with open(file_to_open, 'r') as file:
            lines = file.readlines()
            current_var_name = None
            current_var_type = None
            current_var_value = ''

            for line_num, line in enumerate(lines, start=1):
                line = line.strip()
                
                if not line or line.startswith('//'):
                    continue
                
                if ':' not in line:
                    current_var_value += line
                    continue
                
                parts = line.split(':', maxsplit=2)
                if len(parts) != 3:
                    raise InvalidSyntaxError(f"Invalid syntax in file '{self.filename}.lxe' at line {line_num}: {line}")

                var_name, var_type, var_value = map(str.strip, parts)
                self._assign_variable(var_name, var_type, current_var_value + var_value, line_num)
                
                current_var_name = var_name
                current_var_type = var_type
                current_var_value = ''

    def _assign_variable(self, var_name, var_type, var_value, line_num):
        try:
            self._check_variable_existence(var_name, line_num)
            if var_type in ['int', 'float', 'str', 'bool', 'list', 'tuple', 'dict', 'set', 'complex']:
                self._validate_type(var_name, var_type, var_value, line_num)
            else:
                if self.strict_mode:
                    raise UnknownTypeError(f"Unknown type for variable '{var_name}' at line {line_num}.")
                print(f"Warning: Unknown type for variable '{var_name}' at line {line_num}.")
        except (ValueError, LexCrossFilesError) as e:
            raise LexCrossFilesError(f"Error in file '{self.filename}.lxe' at line {line_num}: {e}")

    def _check_variable_existence(self, var_name, line_num):
        if var_name in self.variables:
            print(f"Warning: Variable '{var_name}' is redefined at line {line_num}.")

    def _validate_type(self, var_name, var_type, var_value, line_num):
        if var_type == 'int':
            self.variables[var_name] = int(var_value)
        elif var_type == 'float':
            self.variables[var_name] = float(var_value)
        elif var_type == 'str':
            self._validate_string(var_name, var_value, line_num)
        elif var_type == 'bool':
            self.variables[var_name] = var_value.lower() == 'true'
        elif var_type == 'list':
            self._validate_eval(var_name, var_value, list, line_num)
        elif var_type == 'tuple':
            self._validate_eval(var_name, var_value, tuple, line_num)
        elif var_type == 'dict':
            self._validate_eval(var_name, var_value, dict, line_num)
        elif var_type == 'set':
            self._validate_eval(var_name, var_value, set, line_num)
        elif var_type == 'complex':
            self.variables[var_name] = complex(var_value.replace('i', 'j'))
        else:
            raise UnknownTypeError(f"Unknown type for variable '{var_name}' at line {line_num}.")

    def _validate_string(self, var_name, var_value, line_num):
        if not ((var_value.startswith('"') and var_value.endswith('"')) or
                (var_value.startswith("'") and var_value.endswith("'"))):
            raise InvalidSyntaxError(f"Invalid syntax for string variable '{var_name}' at line {line_num}. Strings must be enclosed in single or double quotes.")
        self.variables[var_name] = var_value[1:-1].replace("\\'", "'").replace('\\"', '"')

    def _validate_eval(self, var_name, var_value, expected_type, line_num):
        try:
            self.variables[var_name] = eval(var_value)
            if not isinstance(self.variables[var_name], expected_type):
                raise TypeMismatchError(f"Type mismatch for variable '{var_name}' at line {line_num}. Expected '{expected_type.__name__}'.")
        except Exception as e:
            raise TypeMismatchError(f"Error evaluating variable '{var_name}' at line {line_num}: {e}")

    def get(self, key, default=None):
        return self.variables.get(key, default)

    def __getitem__(self, key):
        if key not in self.variables:
            raise UndefinedVariableError(f"Variable '{key}' is not defined.")
        return self.variables[key]

    def is_loaded(self):
        return self.loaded

    def set_as_environment_variables(self):
        if self.is_loaded():
            for key, value in self.variables.items():
                os.environ[self.env_var_prefix + key] = str(value)
            print("Variables loaded into the environment.")
        else:
            raise LexCrossFilesError("Variables not loaded.")

    def get_all_variables(self):
        return self.variables

    def get_all_types(self):
        return self.types
