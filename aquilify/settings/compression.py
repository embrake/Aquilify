import os
import ast
import importlib

class SettingsImportError(Exception):
    pass

class CompressionSetting:
    def _compression_settings():
        file_path = "./settings.py"
        try:
            with open(file_path, 'r') as file:
                parsed = ast.parse(file.read(), filename=file_path)

            variables_to_import = [
                'GZIP_COMPRESSION_LEVEL',
                'GZIP_COMPRESSION_CONTENT_TYPES',
                'GZIP_IGNORE_CONTENT_LENGHT',
                'GZIP_CONTENT_ENCODING',
                'GZIP_EXCLUDE_PATHS',
                'GZIP_COMPRESSION_FUNCTION'
            ]

            imported_settings = {}
            for node in parsed.body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    target = node.targets[0]
                    if isinstance(target, ast.Name) and target.id in variables_to_import:
                        if target.id == 'GZIP_COMPRESSION_FUNCTION':
                            value = ast.literal_eval(node.value)
                            imported_functions = {}

                            for func_name, func_path in value.items():
                                try:
                                    module_name, _, func_name = func_path.rpartition('.')
                                    module = importlib.import_module(module_name)
                                    imported_functions[func_name] = getattr(module, func_name)
                                except AttributeError:
                                    raise SettingsImportError(f"Function or class '{func_name}' not found in module '{module_name}'")
                                except Exception as e:
                                    raise SettingsImportError(f"Error importing function '{func_name}' from '{func_path}': {e}")

                            imported_settings[target.id] = imported_functions
                        else:
                            value = ast.literal_eval(node.value)
                            imported_settings[target.id] = value

            return imported_settings
        except FileNotFoundError:
            raise SettingsImportError(f"File not found at path '{file_path}'")
        except SyntaxError as se:
            raise SettingsImportError(f"Syntax error in '{file_path}': {se}")
        except Exception as e:
            raise SettingsImportError(f"Error importing settings from '{file_path}': {e}")
