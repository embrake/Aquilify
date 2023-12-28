import importlib.util
import os
import re
import ast
from typing import Callable, Awaitable, Optional, List, Union, Any

class BaseSettings:
    def __init__(self) -> None:
        self.settings_path = os.path.join(os.getcwd(), 'settings.py')

    def _settings_env(self):
        if not os.path.exists(self.settings_path):
            raise FileNotFoundError(f"Error: '{self.settings_path}' does not exist")

        try:
            with open(self.settings_path, 'r') as file:
                file_content = file.read()
                comments_removed = re.sub(r'#.*$', '', file_content, flags=re.MULTILINE)
                
                if "use development" not in comments_removed.lower() and "use production" not in comments_removed.lower():
                    raise ValueError(f"Error: Neither 'use development' nor 'use production' found in settings.py. Add 'use development' to your settings.py")
                return True
        except Exception as e:
            raise Exception(f"Error: {e}")

    def compator(self):
        self._settings_env()
        try:
            spec = importlib.util.spec_from_file_location("settings", self.settings_path)
            if spec is None:
                raise ImportError(f"Error: Unable to load '{self.settings_path}'")

            settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings)

            debug = settings.DEBUG if getattr(settings, 'DEBUG', False) else False
            return debug

        except (FileNotFoundError, ValueError, ImportError, AttributeError, Exception) as e:
            return f"Error: {e}"

class BaseMiddlewareSettings:
    def __init__(self) -> None:
        self.settings_path = os.path.join(os.getcwd(), 'settings.py')
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def static_settings(self):
        default_settings = {
            'static_folders': [os.path.join(self.base_dir, 'static')],
            'url_prefix': '/static/',
            'cache_max_age': 0,
            'enable_gzip': True,
            'response_handler': None,
            'chunk_size': 65536
        }

        try:
            spec = importlib.util.spec_from_file_location("settings", self.settings_path)
            if spec is None:
                raise ImportError(f"Error: Unable to load '{self.settings_path}'")

            settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(settings)
        except ImportError:
            return default_settings

        static_folders = getattr(settings, "STATICFILE_DIRS", default_settings['static_folders'])
        static_url_prefix = getattr(settings, "STATIC_URL", default_settings['url_prefix'])
        cache_max_age = getattr(settings, "STATIC_MAX_AGE", default_settings['cache_max_age'])
        enable_gzip = getattr(settings, "STATIC_GZIP_COMPRESSION", default_settings['enable_gzip'])
        response_handler = getattr(settings, "STATIC_RESPONSE_HANDLER", default_settings['response_handler'])
        chunk_size = getattr(settings, "STATIC_CHUNK_SIZE", default_settings['chunk_size'])

        return {
            'static_folders': static_folders,
            'url_prefix': static_url_prefix,
            'cache_max_age': cache_max_age,
            'enable_gzip': enable_gzip,
            'response_handler': response_handler,
            'chunk_size': chunk_size
        }

class MiddlewareEntry:
    def __init__(
        self,
        origin: Union[str, dict],
        order: int = 0,
        __init__: str = None,
        conditions: Optional[List[Callable[..., bool]]] = None,
        group: Optional[str] = None,
        active: bool = True,
        excludes: Optional[Callable[..., Awaitable[bool]]] = None,
        type: str = 'http'
    ) -> None:
        self.origin = origin
        self.order = order
        self.__init__ = __init__
        self.conditions = conditions or []
        self.group = group
        self.active = active
        self.excludes = excludes
        self.type = type
        self.middleware = None

def fetchSettingsMiddleware(your_instance):
    settings_module_path = 'settings'
    middlewares = _import_middleware(settings_module_path)
    
    if not middlewares:
        pass

    for middleware_entry in middlewares:
        if middleware_entry.__init__ == "app":
            middleware = _instantiate_middleware(middleware_entry.middleware, your_instance)
        else:
            if middleware_entry.__init__ is not None:
                raise ValueError("Invalid '__init__' value. Expected 'app' but received another value, currently we only support for app instance __init__.")
            middleware = _instantiate_middleware(middleware_entry.middleware)
        _add_middleware_with_params(your_instance, middleware, middleware_entry)

def _import_middleware(settings_module_path: str) -> List[MiddlewareEntry]:
    try:
        settings_module = importlib.import_module(settings_module_path)
        middlewares_list = getattr(settings_module, "MIDDLEWARES", [])
        return [_create_middleware_entry(entry) for entry in middlewares_list]
    except ImportError as e:
        raise ImportError(f"Error importing settings module '{settings_module_path}': {e}")

def _create_middleware_entry(middleware_entry_data) -> MiddlewareEntry:
    if isinstance(middleware_entry_data, str):
        middleware_entry_data = {"origin": middleware_entry_data}
    try:
        middleware_entry = MiddlewareEntry(**middleware_entry_data)
        middleware_entry.middleware = _get_middleware_class(middleware_entry.origin)
        return middleware_entry
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Error importing middleware '{middleware_entry_data.get('origin')}': {e}")

def _get_middleware_class(origin) -> Callable:
    if isinstance(origin, str):
        module_name, class_name = origin.rsplit('.', 1)
        middleware_module = importlib.import_module(module_name)
        return getattr(middleware_module, class_name)
    raise ValueError("Invalid middleware origin format. It should be a string representing the module path.")

def _instantiate_middleware(middleware_class, app=None):
    if callable(getattr(middleware_class, '__call__', None)) and not isinstance(middleware_class, type):
        return middleware_class
    elif isinstance(middleware_class, type):
        if app is not None:
            return middleware_class(app)
        return middleware_class()
    else:
        raise ValueError("Invalid middleware format. It should be either a function or a class.")

def _add_middleware_with_params(instance, middleware, middleware_entry):
    instance.add_middleware(
        middleware=middleware,
        order=middleware_entry.order,
        conditions=middleware_entry.conditions,
        group=middleware_entry.group,
        active=middleware_entry.active,
        excludes=middleware_entry.excludes,
        type=middleware_entry.type
    )

class StageHandler:
    def _exclude_comments(self, code: str) -> str:
        """Exclude comments from the code."""
        parsed_code = ast.parse(code)
        modified_code = ast.unparse(parsed_code)
        return modified_code

    def load_settings(self):
        try:
            with open("./settings.py", "r") as file:
                code = file.read()
                code = self._exclude_comments(code)
                
                spec = importlib.util.spec_from_loader("settings", loader=None, origin="./settings.py")
                settings = importlib.util.module_from_spec(spec)
                
                settings.__file__ = "./settings.py"  # Define __file__ manually
                
                exec(code, settings.__dict__)
                return settings
        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def load_middleware_from_path(self, middleware_path: str) -> Any:
        try:
            module_path, class_name = middleware_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            middleware_class = getattr(module, class_name)

            if isinstance(middleware_class, type):
                try:
                    middleware_instance = middleware_class()
                    return middleware_instance
                except Exception as e:
                    raise ImportError(f"Error instantiating middleware class: {e}")
            else:
                return middleware_class 

        except (ModuleNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading middleware: {e}")

    def process_stage_handlers(self, instance):
        settings = self.load_settings()
        STAGE_HANDLERS = getattr(settings, 'STAGE_HANDLERS', None)
        
        if STAGE_HANDLERS is None:
            raise AttributeError("STAGE_HANDLERS not found in settings.py")

        for handler in STAGE_HANDLERS:
            middleware_path = handler.get('origin')
            stage = handler.get('stage')

            if stage not in ['before', 'after']:
                raise ValueError(f"Invalid stage '{stage}'. Stage must be either 'before' or 'after'.")

            try:
                middleware_class = self.load_middleware_from_path(middleware_path)

                instance.request_stage_handlers.setdefault(stage, []).append(
                    (
                        middleware_class,
                        handler.get('order', 0),
                        handler.get('conditions', None)
                    )
                )

                if handler.get('group'):
                    instance.grouped_request_stages \
                        .setdefault(handler.get('group'), {}) \
                        .setdefault(stage, []).append(middleware_class)

                if handler.get('exclude'):
                    instance.excluded_stages.setdefault(handler.get('exclude'), set()).add(middleware_class)

                if handler.get('inherit'):
                    instance._inherit_from_group(stage, handler.get('group'), handler.get('inherit'))

            except ImportError as e:
                raise ImportError(f"Error processing middleware: {e}")