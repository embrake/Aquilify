import os
import re
import json

class LxEnviroment:
    def __init__(self, filename):
        self.filename = self.validate_filename(filename)
        self.filepath = f"{self.filename}.lxe"

    def validate_filename(self, filename):
        # Remove extension if provided
        filename_without_extension = os.path.splitext(filename)[0]
        return filename_without_extension
    
    def read_file_content(self):
        try:
            with open(self.filepath, "r") as file:
                content = file.read()
                # Remove comments before validating syntax
                content = re.sub(r"#.*", "", content)
                return content
        except FileNotFoundError:
            raise FileNotFoundError(f"{self.filename}.lxe not found.")
    
    def validate_syntax(self, content):
        try:
            self.validate_import_statement(content)
            self.validate_export_syntax(content)
            self.validate_builder_function(content)
            self.validate_math_import(content)
        except (ImportError, SyntaxError) as e:
            line_number = content.count("\n", 0, content.find(e.args[0])) + 1
            raise type(e)(f"{e.args[0]} at line {line_number} in {self.filename}.lxe")
    
    def validate_import_statement(self, content):
        import_pattern = r"import\s+{\s*enviroment\s*}\s+from\s+'LxEnviroment\.env'"
        if not re.search(import_pattern, content):
            raise ImportError("ImportError: 'enviroment' is not imported from 'LxEnviroment.env'.")

    def validate_export_syntax(self, content):
        export_pattern = r"enviroment\.export\s*=>\s*\(builder\)\s*=\s*{[^{}]*}"
        if not re.search(export_pattern, content):
            raise SyntaxError("SyntaxError: Unable to find valid 'enviroment.export => (builder) = {}' syntax.")

    def validate_builder_function(self, content):
        builder_pattern = r"=>\s*\(builder\)\s*=\s*{[^{}]*}"
        if not re.search(builder_pattern, content):
            raise SyntaxError("SyntaxError: 'builder' function is missing.")

    def validate_math_import(self, content):
        math_modules = ['add', 'sub', 'div', 'mult']
        for module in math_modules:
            import_pattern = fr"import\s+{{\s*{module}\s*}}\s+from\s+'LxEnviroment\.mathematic'"
            if re.search(import_pattern, content):
                return module
        raise ImportError("ImportError: Math modules not imported from 'LxEnviroment.mathematic'.")

    def perform_operation(self, operation, values):
        if operation == 'add':
            return sum(values)
        elif operation == 'sub':
            return values[0] - sum(values[1:])
        elif operation == 'mult':
            result = 1
            for val in values:
                result *= val
            return result
        elif operation == 'div':
            result = values[0]
            for val in values[1:]:
                result /= val
            return result

    def execute_math_operation(self, content):
        math_module = self.validate_math_import(content)
        pattern = fr"{math_module}\(\)\s*->\s*\(([^()]*)\)\s*->\s*{{type\s+either\s+(int|float|str)}}"
        match = re.search(pattern, content)
        if match:
            values = [eval(val.strip()) for val in match.group(1).split(',')]
            result = self.perform_operation(math_module, values)
            return result
        else:
            raise SyntaxError(f"SyntaxError: Invalid syntax for {math_module} operation.")

    def extract_environment_variables(self, content):
        self.validate_syntax(content)

        pattern = r"enviroment\.export\s*=>\s*\(builder\)\s*=\s*({[^{}]*})"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1)
        else:
            raise SyntaxError("SyntaxError: Unable to extract environment variables.")
    
    def parse_environment_variables(self, env_str):
        try:
            return json.loads(env_str)
        except json.JSONDecodeError:
            raise ValueError("ValueError: Invalid JSON format for environment variables.")
    
    def get_environment_variables(self):
        content = self.read_file_content()
        env_content = self.extract_environment_variables(content)
        return self.parse_environment_variables(env_content)
    
    def set_environment_variable(self, key, value):
        content = self.read_file_content()
        env_content = self.extract_environment_variables(content)
        env_dict = self.parse_environment_variables(env_content)
        
        env_dict[key] = value
        
        with open(self.filepath, "w") as file:
            content = re.sub(r"(enviroment\.export\s*=>\s*\(builder\)\s*=\s*)({[^{}]*})", f"\\1{json.dumps(env_dict, indent=4)}", content, flags=re.DOTALL)
            file.write(content)
    
    def create_lxe_file(self):
        try:
            with open(self.filepath, "w") as file:
                file.write('import { enviroment } from \'LxEnviroment.env\'\n\n')
                file.write('enviroment.export => (builder) = {}\n')
        except IOError:
            raise IOError(f"Error: Failed to create {self.filename}.lxe file.")