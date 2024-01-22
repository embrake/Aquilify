import importlib.util
import os

class Router:
    @staticmethod
    def finalize():
        file_name='routing.py'
        current_directory = os.getcwd()
        module_path = os.path.join(current_directory, file_name)
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"File '{file_name}' not found in the current directory.")

        try:
            spec = importlib.util.spec_from_file_location(file_name.replace('.py', ''), module_path)
            with open(module_path, 'rb') as file:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            if hasattr(module, 'ROUTER'):
                return module.ROUTER
            else:
                raise AttributeError(f"The module '{file_name}' does not contain a variable named ROUTER")

        except ImportError as e:
            raise ImportError(f"Failed to import '{file_name}': {e}")
        except AttributeError as e:
            raise AttributeError(f"Attribute error in '{file_name}': {e}")
        except Exception as e:
            raise Exception(f"An error occurred while importing '{file_name}': {e}")