import inspect
from importlib import import_module
from typing import Any, Awaitable, Callable, Dict, List, Optional, Pattern, Tuple, Type, TypeVar

from ..types import ASGIApp
from .__globals import Converter
from .schematic import Schematic

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

RouteInfo = Tuple[
    str, List[str], Callable[..., Awaitable[T]], List[str], Pattern, Type[T], str, Dict[str, Any]
]
Routes = List[RouteInfo]
WebSocketRoute = Tuple[str, Callable[..., Awaitable[T]]]
WebSocketRoutes = List[WebSocketRoute]

_routes: Routes = []
_links: Routes = []
_websockets: WebSocketRoutes = []

class ImproperlyConfigured(Exception):
    pass

def rule(
    path: str,
    methods: Optional[List[str]] = None,
    response_model: Optional[Type[T]] = None,
    endpoint: Optional[Callable[..., Awaitable[T]]] = None,
    name: Optional[str] = None,
    strict_slashes: bool = True,
    **kwargs: Any
) -> None:
    if kwargs:
        return ValueError("**kwargs support isn't implemented yet! @noql -> 4113")
    
    if endpoint is None:
        raise ValueError("Handler function is required for adding a route.")

    if not inspect.iscoroutinefunction(endpoint) and not inspect.isasyncgenfunction(endpoint):
        raise TypeError("ASGI can only register asynchronous functions.")

    if not path.startswith('/'):
        raise TypeError("Paths must start with '/'.")

    allowed_methods = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"}
    if methods is not None and not all(method.upper() in allowed_methods for method in map(str.upper, methods)):
        invalid_methods = [method for method in methods if method.upper() not in allowed_methods]
        raise ValueError(f"Invalid HTTP method(s) provided: {', '.join(invalid_methods)}")

    methods = methods or ["GET"]

    converted_path, path_regex = Converter()._regex_converter(path, strict_slashes, '')
    handler = endpoint

    _routes.append((
        converted_path,
        methods,
        handler,
        path_regex,
        response_model,
        endpoint
    ))
    _links.append((
        path,
        endpoint,
        name
    ))

def websocket(
    path: str,
    endpoint: Optional[Callable[..., Awaitable[T]]] = None
) -> None:
    if endpoint is None:
        raise ValueError("Handler function is required for adding a websocket route.")

    if not inspect.iscoroutinefunction(endpoint) and not inspect.isasyncgenfunction(endpoint):
        raise TypeError("ASGI Websocket can only register asynchronous functions.")

    if not path.startswith('/'):
        raise TypeError("Websocket paths must start with '/'.")
    
    compiled_path, path_regex = Converter()._regex_converter(path, False)
    handler = endpoint
    _websockets.append((compiled_path, path_regex, handler))

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

def link(schematic: Dict[str, str]) -> None:
    for url_prefix, schematic_path in schematic.items():
        try:
            module_name, class_name = schematic_path.rsplit('.', 1)
            module = import_module(module_name)
            schematic_instance = getattr(module, class_name)
            
            if not isinstance(schematic_instance, Schematic):
                raise TypeError(f"{schematic_path} is not a valid Aquilify Schematic ASGIApp class")
                
            _schematic._process_routes(schematic_instance, url_prefix)
            _schematic._process_schematic_instance(schematic_instance, url_prefix)
        except (ValueError, AttributeError, ModuleNotFoundError) as e:
            raise ImportError(f"Failed to import {schematic_path}: {e}")
        except TypeError as e:
            raise TypeError(f"Error processing {schematic_path}: {e}")