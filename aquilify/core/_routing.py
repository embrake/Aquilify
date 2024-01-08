import re
import inspect
import importlib
from importlib import import_module

from typing import (
    Any, 
    Awaitable, 
    Callable, 
    Dict, 
    List, 
    Optional, 
    Pattern, 
    Tuple, 
    Type, 
    TypeVar
)

from ..types import ASGIApp
from .__globals import Converter
from .schematic import Schematic
from ..exception.base import ImproperlyConfigured

from ..types import (
    Routes,
    WebSocketRoutes
)

T = TypeVar("T")

class ColoursCode:
    BG_YELLOW = "\033[35m"
    BLUE = "\033[34m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

_routes: Routes = []
_links: Routes = []
_websockets: WebSocketRoutes = []
_handlers_set = set()

class DuplicateHandler:
    @staticmethod
    def _duplicate_handler(handler: Callable[..., Awaitable[T]]) -> None:
        if handler in _handlers_set:
            raise ImproperlyConfigured("Duplicate handler found in routes.")
        _handlers_set.add(handler)
    
    @staticmethod
    def _is_duplicate_route(path: str, endpoint: Callable[..., Awaitable[Any]]) -> bool:
        for route in _routes:
            if route[0] == path and route[2] == endpoint:
                return True
        return False
    
    @staticmethod
    def _is_duplicate_websocket(path: str, endpoint: Callable[..., Awaitable[Any]]) -> bool:
        for route in _websockets:
            if route[0] == path and route[2] == endpoint:
                return True
        return False
    
    @staticmethod
    def _is_duplicate_route_with_regex(path_regex: str, endpoint: Callable[..., Awaitable[Any]]) -> bool:
        return any(route[3].pattern == path_regex and route[2] == endpoint for route in _routes)
    
class RoutingHelpers:
    @staticmethod
    def _helper_inc_path(path: str, func_include: Callable[..., Awaitable[T]]):
        for func in func_include:
            if not len(func) == 7:
                pass
            else:
                sub_path, sub_methods, sub_handler, sub_strict_slashes, sub_response_model, sub_endpoint, sub_name = func
                
                if sub_handler is None or not (inspect.iscoroutinefunction(sub_handler) or inspect.isasyncgenfunction(sub_handler)):
                    raise ImproperlyConfigured("Invalid handler function provided for adding a route.")
                
                allowed_methods = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"}
                if sub_methods and not all(method.upper() in allowed_methods for method in map(str.upper, sub_methods)):
                    invalid_methods = [method for method in sub_methods if method.upper() not in allowed_methods]
                    raise ImproperlyConfigured(f"Invalid HTTP method(s) provided: {', '.join(invalid_methods)}")

                sub_methods = sub_methods or ["GET"]
                
                converted_path, path_regex = Converter()._regex_converter(path + sub_path, sub_strict_slashes, '')
                
                if DuplicateHandler._is_duplicate_route(converted_path, sub_handler):
                    raise ImproperlyConfigured("Duplicate endpoint detected for the same route.")
                
                _routes.append((
                    converted_path,
                    sub_methods,
                    sub_handler,
                    path_regex,
                    sub_response_model,
                    sub_endpoint
                ))
                _links.append((
                    path,
                    sub_endpoint,
                    sub_name
                ))
        return None
    
    @staticmethod
    def _helper_inc_websockets(path: str, func_include: Callable[..., Awaitable[T]]):
        for func in func_include:
            if not len(func) == 2:
                pass
            else:
                sub_path, sub_handler = func
                
                if sub_handler is None or not (inspect.iscoroutinefunction(sub_handler) or inspect.isasyncgenfunction(sub_handler)):
                    raise ImproperlyConfigured("Invalid handler function provided for adding a websocket route.")
                
                converted_path, path_regex = Converter()._regex_converter(path + sub_path, False)
                
                if DuplicateHandler._is_duplicate_websocket(converted_path, sub_handler):
                    raise ImproperlyConfigured("Duplicate endpoint detected for the same websocket route.")
                
                _websockets.append((
                    converted_path,
                    path_regex,
                    sub_handler
                ))
            
class HTTPRouting:
    @staticmethod
    def rule(
        path: str,
        endpoint: Optional[Callable[..., Awaitable[Any]]] = None,
        **kwargs: Any
    ) -> Optional[List[Tuple]]:
        if not path.startswith('/'):
            raise ImproperlyConfigured("Paths must start with '/'.")
        
        include_routes = kwargs.pop('include', None)
        if include_routes:
            RoutingHelpers._helper_inc_path(path, include_routes)
            pass
        else:
            response_model = kwargs.pop('response_model', None)
            strict_slashes = kwargs.pop('strict_slashes', True)
            methods = kwargs.pop('methods', None)

            if endpoint is None or not (inspect.iscoroutinefunction(endpoint) or inspect.isasyncgenfunction(endpoint)):
                raise ImproperlyConfigured("Invalid handler function provided for adding a route.")

            allowed_methods = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"}
            methods = methods or ["GET"]
            invalid_methods = [method for method in methods if method.upper() not in allowed_methods]
            if invalid_methods:
                raise ImproperlyConfigured(f"Invalid HTTP method(s) provided: {', '.join(invalid_methods)}")

            converted_path, path_regex = Converter()._regex_converter(path, strict_slashes, '')

            if DuplicateHandler._is_duplicate_route(converted_path, endpoint):
                raise ImproperlyConfigured("Duplicate endpoint detected for the same route.")

            _routes.append((
                converted_path,
                methods,
                endpoint,
                path_regex,
                response_model,
                endpoint
            ))
            _links.append((
                path,
                endpoint,
                kwargs.get('name')
            ))
            
            return (path, methods, endpoint, strict_slashes, response_model, endpoint, kwargs.get('name'))
        
    @staticmethod
    def re_rule(
        path_regex: str,
        endpoint: Optional[Callable[..., Awaitable[Any]]] = None,
        **kwargs: Any
    ) -> Optional[List[Tuple]]:
        if endpoint is None or not (inspect.iscoroutinefunction(endpoint) or inspect.isasyncgenfunction(endpoint)):
            raise ImproperlyConfigured("Invalid handler function provided for adding a route.")

        response_model = kwargs.pop('response_model', None)
        methods = kwargs.pop('methods', None)

        allowed_methods = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"}
        methods = methods or ["GET"]
        invalid_methods = [method for method in methods if method.upper() not in allowed_methods]
        if invalid_methods:
            raise ImproperlyConfigured(f"Invalid HTTP method(s) provided: {', '.join(invalid_methods)}")

        path_regex_compiled = re.compile(path_regex)

        if DuplicateHandler._is_duplicate_route_with_regex(path_regex_compiled.pattern, endpoint):
            raise ImproperlyConfigured("Duplicate endpoint detected for the same route.")

        _routes.append((
            path_regex,
            methods,
            endpoint,
            path_regex_compiled,
            response_model,
            endpoint
        ))
        _links.append(
            (
                path_regex,
                endpoint,
                kwargs.get('name', None)
            )
        )
        return (path_regex, methods, endpoint, kwargs.get('strict_slashes', False), response_model, endpoint, kwargs.get('name'))
    
    @staticmethod
    def rule_all(
        path: str,
        response_model: Optional[Type[T]] = None,
        endpoint: Callable[..., Awaitable[T]] = None,
        strict_slashes: bool = True,
        name: Optional[str] = None
    ) -> Callable[..., Awaitable[T]]:
        
        handler = endpoint
        allowed_methods = [
            "GET", "POST", "PUT", "DELETE",
            "HEAD", "OPTIONS", "PATCH", "TRACE"
        ]

        if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
            raise TypeError("ASGI can only register asynchronous functions.")
        
        if not path.startswith('/'):
            raise ImproperlyConfigured("Paths must start with '/'.")
        
        DuplicateHandler._duplicate_handler(handler)

        converted_path, path_regex = Converter()._regex_converter(
            path, strict_slashes, ''
        )
        _routes.append(
            (
                converted_path,
                allowed_methods,
                handler,
                path_regex,
                response_model,
                endpoint
            )
        )
        
        _links.append((
            path,
            endpoint,
            name
        ))
        
        return (
            path,
            allowed_methods,
            handler,
            strict_slashes,
            response_model,
            endpoint,
            name
        )
        
class WebsocketRouting:
    @staticmethod
    def websocket(
        path: str,
        endpoint: Optional[Callable[..., Awaitable[T]]] = None,
        **kwargs: Any
    ) -> None:
        
        if not path.startswith('/'):
            raise ImproperlyConfigured("Websocket paths must start with '/'.")
        
        if 'include' in kwargs:
            websocket_include = kwargs.get('include', None)
            if websocket_include:
                RoutingHelpers._helper_inc_websockets(path, websocket_include)
                return None
        else:
            if endpoint is None:
                raise ImproperlyConfigured("Handler function is required for adding a websocket route.")

            if not inspect.iscoroutinefunction(endpoint) and not inspect.isasyncgenfunction(endpoint):
                raise ImproperlyConfigured("ASGI Websocket can only register asynchronous functions.")
            
            compiled_path, path_regex = Converter()._regex_converter(path, False)
            handler = endpoint
            _websockets.append((compiled_path, path_regex, handler))
            return (path, handler)

class _SchematicInstance:
    def __init__(self) -> None:
        self.schematic = None
        self.schematic_id = None

    def _process_routes(self, schematic_instance: [ASGIApp], url_prefix: str) -> None:
        for route in schematic_instance.routes:
            path, methods, handler, strict_slashes, response_model, endpoint = route

            if path.endswith('/'):
                path = ''  # Simulating the root_path

            converted_path, path_regex = Converter()._regex_converter(url_prefix + path, strict_slashes)

            _routes.append(
                (
                    converted_path,
                    methods,
                    handler,
                    path_regex,
                    response_model,
                    endpoint,
                )
            )
            _links.append((
                url_prefix + path,
                endpoint,
                schematic_instance.name
            ))

    def _process_schematic_instance(self, schematic_instance: [ASGIApp], url_prefix: str) -> None:
        if schematic_instance.schematic_id is not None:
            self._update_schematic_info(schematic_instance)
            self._print_schematic_info(schematic_instance, url_prefix)

        self._process_websockets(schematic_instance, url_prefix)

    def _update_schematic_info(self, schematic_instance: [ASGIApp]) -> None:
        self.schematic_id = schematic_instance.schematic_id
        self.schematic = schematic_instance.get_schematic()

    def _print_schematic_info(self, schematic_instance: [ASGIApp], url_prefix: str) -> None:
        schematic_name = schematic_instance.name
        url_prefix_info = (
            f"at {ColoursCode.BOLD}{ColoursCode.GREEN}{url_prefix}{ColoursCode.RESET} url-prefix"
            if url_prefix
            else "with no specific URL prefix"
        )

        serving_message = (
            f"\n Serving Schematic {ColoursCode.BOLD}{ColoursCode.GREEN}'{schematic_name}'{ColoursCode.RESET} Instance {url_prefix_info}."
        )
        instance_id_message = f"Instance-ID: {ColoursCode.BOLD}{ColoursCode.GREEN}{self.schematic_id}{ColoursCode.RESET}"

        print(serving_message)
        print(instance_id_message)

        paths = [route[0] for route in schematic_instance.routes]
        if paths:
            print(
                f"{ColoursCode.CYAN}Routes{ColoursCode.RESET}: {ColoursCode.GREEN}{paths}{ColoursCode.RESET} \n"
            )
        else:
            print(
                f"{ColoursCode.RED}No HTTP routes found for this schematic.{ColoursCode.RESET} \n"
            )

    def _process_websockets(self, schematic_instance: [ASGIApp], url_prefix: str) -> None:
        if schematic_instance.websockets:
            print(f"{ColoursCode.BOLD}WebSocket Routes:{ColoursCode.RESET}")

            for path, handler in schematic_instance.websockets:
                full_path = url_prefix + path
                _websockets.append(
                    (
                        full_path,
                        Converter()._regex_converter(full_path, False)[1],
                        handler
                    )
                )
                print(f"  - Path: {ColoursCode.GREEN}{full_path}{ColoursCode.RESET}")
                print(f"    Handler: {handler.__name__}")
            
            print()
        else:
            print(f"{ColoursCode.RED}No WebSocket routes found for this schematic.{ColoursCode.RESET}\n")

_schematic = _SchematicInstance()

def link(path: str, instance: Callable[..., Awaitable[Schematic]]) -> None:
    try:
        module_name, class_name = instance.rsplit('.', 1)
        module = import_module(module_name)
        schematic_instance = getattr(module, class_name)
        
        if not isinstance(schematic_instance, Schematic):
            raise TypeError(f"{instance} is not a valid Aquilify Schematic ASGIApp class")
            
        _schematic._process_routes(schematic_instance, path)
        _schematic._process_schematic_instance(schematic_instance, path)
    except (ValueError, AttributeError, ModuleNotFoundError) as e:
        raise ImportError(f"Failed to import {instance}: {e}")
    except TypeError as e:
        raise TypeError(f"Error processing {instance}: {e}")

class DynamicModuleLoader:
    class ModuleImportError(Exception):
        pass

    class RoutingVariableError(Exception):
        pass

    def __init__(self):
        pass

    def _module_loader(self, dotted_path: str) -> Optional[Any]:
        """
        Load a module given its dotted path.

        Args:
        - dotted_path (str): The dotted path of the module.

        Returns:
        - Optional[Any]: The loaded module if successful, otherwise None.

        Raises:
        - ModuleImportError: If unable to import the specified module.
        """
        try:
            return importlib.import_module(dotted_path)
        except ImportError as e:
            raise self.ModuleImportError(f"Unable to import module {dotted_path}: {e}")

    def _routing_avrs(self, module: Any, namespace: str = '') -> Optional[List[Any]]:
        """
        Retrieve the routing variable list from a module.

        Args:
        - module (Any): The module object.
        - namespace (str): The namespace for the routing variable.

        Returns:
        - Optional[List[Any]]: The routing variable list if found, otherwise None.

        Raises:
        - RoutingVariableError: If the routing variable is not found or not a list in the module.
        """
        routing_var = getattr(module, f"{namespace}ROUTER", None)
        if routing_var is None:
            raise self.RoutingVariableError(f"No '{namespace}ROUTER' variable found in the module")
        if not isinstance(routing_var, list):
            raise self.RoutingVariableError(f"'{namespace}ROUTER' variable is not a list in the module")
        return routing_var

    def _include(self, dotted_path: str, namespace: str = '') -> Optional[List[Any]]:
        """
        Include routing configuration from other sources.

        Args:
        - dotted_path (str): The dotted path of the module.
        - namespace (str): The application namespace.

        Returns:
        - Optional[List[Any]]: The included routing configuration if successful, otherwise None.

        Raises:
        - ModuleImportError: If unable to import the specified module.
        - RoutingVariableError: If the routing variable is not found or not a list in the module.
        """
        try:
            module: Any = self._module_loader(dotted_path)
            return self._routing_avrs(module, namespace)
        except (self.ModuleImportError, self.RoutingVariableError) as e:
            print(f"Error: {e}")
            return None

def include(args: str, namespace: str = '') -> Optional[List[Any]]:
    """
    Include routing configuration from specified modules.

    Args:
    - args (str): The modules' dotted paths.
    - namespace (str): The application namespace.

    Returns:
    - Optional[List[Any]]: The included routing configurations.

    Example:
    >>> include('module1.urls', namespace='my_namespace')
    """
    cls: Optional[List[Any]] = DynamicModuleLoader()._include(args, namespace)
    return cls