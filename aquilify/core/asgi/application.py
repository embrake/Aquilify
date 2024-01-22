import importlib.util
import os
import sys

from .asgi_middleware  import ASGIMiddlewareLoader, ASGIMiddlewareLoaderError

from typing import Any, Dict, Optional, List

CachedModules = Dict[str, Any]

cached_modules: CachedModules = {}


class EntryPointExtractor:
    def __init__(self):
        pass

    def _extract_module_info(self, entry_point):
        module_info = {}
        if isinstance(entry_point, str):
            index_of_dot = entry_point.find('.')
            if index_of_dot != -1:
                module_info['module_path'] = entry_point[:index_of_dot]
                module_info['module_variable'] = entry_point[index_of_dot + 1:]
            else:
                module_info['module_path'] = entry_point
                module_info['module_variable'] = None
        return module_info

    def extractEntryPoint(self):
        current_directory = os.getcwd()
        settings_path = os.path.join(current_directory, 'settings.py')

        if os.path.exists(settings_path):
            spec = importlib.util.spec_from_file_location("settings", settings_path)
            settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings)

            if hasattr(settings, 'ENTRY_POINT'):
                entry_point = settings.ENTRY_POINT
                return self._extract_module_info(entry_point)
            else:
                return None
        else:
            return None

class ASGI:
    @staticmethod
    def wrap_with_middlewares(variable: Any, middlewares: List[Any]) -> Any:
        """Applies middlewares to the given variable."""
        for middleware in middlewares:
            variable = middleware(variable)
        return variable

    @staticmethod
    def load_module(module_name: str) -> Any:
        """Loads a Python module by name."""
        try:
            if module_name in sys.modules:
                return sys.modules[module_name]
            else:
                spec = importlib.util.find_spec(module_name)
                if spec is not None:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    sys.modules[module_name] = module
                    return module
                else:
                    raise ImportError(f"Module '{module_name}' not found in the Python path")
        except Exception as e:
            raise ImportError(f"Failed to load module '{module_name}': {e}")

    @staticmethod
    def get_variable_from_module(module: Any, variable_name: Optional[str]) -> Any:
        """Retrieves a variable from a loaded module."""
        if variable_name is None:
            return module
        else:
            imported_variable = getattr(module, variable_name, None)
            if imported_variable is not None:
                return imported_variable
            else:
                raise AttributeError(f"Variable '{variable_name}' not found in module '{module.__name__}'")

    @staticmethod
    def application() -> Any:
        """Loads an ASGI application."""
        entry_point = EntryPointExtractor().extractEntryPoint()
        module_name = entry_point['module_path'] or '__root__'
        variable_name = entry_point['module_variable'] or '__instance__'

        try:
            module = ASGI.load_module(module_name)
            imported_variable = ASGI.get_variable_from_module(module, variable_name)

            middleware_loader = ASGIMiddlewareLoader()
            middlewares = middleware_loader.load_asgi_middlewares()

            return ASGI.wrap_with_middlewares(imported_variable, middlewares)

        except ASGIMiddlewareLoaderError as e:
            raise ImportError(f"Failed to load ASGI middlewares: {e}")
        except ImportError as e:
            raise ImportError(f"Failed to import '{variable_name}' from '{module_name}': {e}")
        except Exception as e:
            raise ImportError(f"Failed to initialize ASGI application: {e}")