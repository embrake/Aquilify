from __future__ import annotations

import json
import inspect
import warnings
import traceback
import xml.etree.ElementTree as ET

from enum import Enum
from functools import wraps
from inspect import signature
from collections import defaultdict


from typing import (
    Callable,
    Any,
    List,
    Type,
    Dict,
    Optional,
    TypeVar,
    Tuple,
    Awaitable,
    Pattern,
    Union,
    Mapping
)

from aquilify.config import Config
from aquilify.settings import settings
from aquilify.views.urlI8N import urlI8N
from aquilify.responses import HTMLResponse
from aquilify.core.schematic import Schematic
from aquilify.wrappers.reqparser import Reqparser
from aquilify.core.__status import exception_dict
from aquilify.utils.module_loading import import_string
from aquilify.exception.__handler import handle_exception
from aquilify.settings.lifespan import ASGILifespanLoader
from aquilify.exception.base import ImproperlyConfigured

from aquilify.exception.debug import (
    debug_404,
    debug_405
)

from aquilify.exception.base import (
    HTTPException,
    InternalServerError
)

from aquilify.wrappers import (
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    WebSocketState
)

from aquilify.types import (
    ASGIApp,
    Scope,
    Receive,
    Send,
    Lifespan,
    StatefulLifespan
)

from aquilify.core.__globals import (
    Converter,
    routing,
    BaseSettings,
    StageHandler,
    fetchSettingsMiddleware
)



T = TypeVar("T")

_settings = BaseSettings().compator()

class RequestStage(Enum):
    BEFORE: str = 'before'
    AFTER: str = 'after'

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

class Aquilify:
    def __init__(
        self
        ) -> None:

        self.routes: List[
            Tuple[
                str,
                List[str],
                Callable[..., Awaitable[T]],
                List[str],
                Pattern,
                Type[T],
                str,
                Dict[str, Any],
            ]
        ] = []
        self.websockets: List[
            Tuple[
                str,
                Callable[..., Awaitable[T]]
            ]
        ] = []
        self._middlewares: List[Callable[..., Awaitable[T]]] = []
        self.middleware_order: List[Tuple[Callable[..., Awaitable[T]], int]] = []
        self.request_transformers: List[Callable[..., Awaitable[Request]]] = []
        self.response_transformers: List[
            Callable[..., Awaitable[Response]]
        ] = []
        self.messages: List[Callable[..., Awaitable[T]]] = []
        self.middleware_groups: Dict[str, List[Callable[..., Awaitable[T]]]] = {}
        self.middleware_activation: Dict[Callable[..., Awaitable[T]], bool] = {}
        self.middleware_dependencies: Dict[Callable[..., Awaitable[T]], List[Callable[..., Awaitable[T]]]] = defaultdict(list)
        self.middleware_exclusions: Dict[Callable[..., Awaitable[T]], List[Callable[..., Awaitable[T]]]] = defaultdict(list)
        self.before_request_handlers: List[Callable[..., Awaitable[T]]] = []
        self.after_request_handlers: List[Callable[..., Awaitable[T]]] = []
        self.startup_handlers: List[Callable[..., Awaitable[Lifespan]]] = []
        self.shutdown_handlers: List[Callable[..., Awaitable[Lifespan]]] = []
        self.grouped_request_stages: Dict[str, Dict[str, List[Callable]]] = {}
        self.error_handlers: Dict[str, Dict[str, List[Callable]]] = {}
        self.excluded_stages: Dict[str, List[Callable]] = {}
        self.config: Callable[..., Awaitable[T, Config, Union[str, dict, bytes, Any]]] = None,
        self.request_stage_handlers: Dict[str, List[Tuple[Callable[..., Awaitable[None]], int, Optional[Callable]]]] = {
            RequestStage.BEFORE.value: [], 
            RequestStage.AFTER.value: []
        }
        self.on_startup: Optional[Union[Callable[..., Awaitable[Any]], List[Callable[..., Awaitable[Any]]]]] = None,
        self.on_shutdown: Optional[Union[Callable[..., Awaitable[Any]], List[Callable[..., Awaitable[Any]]]]] = None,

        self.debug: bool = _settings or False
        self.schematic_id: Optional[str] = None
        self.schematic: Callable[..., Awaitable[T]] = None
        self.exception_handlers: Optional[
            Mapping[
                Any,
                Callable[
                    [Request, Exception],
                    Union[Response, Awaitable[Response]],
                ],
            ]
        ] = None
        self.settings_stage_handler = StageHandler()
        self.settings_stage_handler.process_stage_handlers(self)
        fetchSettingsMiddleware(self)
        self._check_lifespan_settings()
        self._load_exception_handler()

    def errorhandler(self, status_code: int) -> Callable:
        def decorator(handler: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            self.error_handlers[status_code] = handler
            return handler
        return decorator

    def route(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        response_model: Optional[Type[T]] = None,
        endpoint: Optional[str] = None,
        strict_slashes: bool = True,
    ) -> Callable[..., Awaitable[T]]:
        """
        We no longer document this decorator style API, and its usage is discouraged.
        Instead you should use the following approach:

        >>> ROUTER = [
                rule('/', methods=['GET', 'POST'], endpoint=home)
            ]
        """
        warnings.warn(
            "The `route` decorator is deprecated, and will be removed in version 1.12. ",  # noqa: E501
            DeprecationWarning,
        )
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"]
        try:
            if not path.startswith('/'):
                raise TypeError("Websocket paths must startwith '/'.")
            if methods is not None:
                for method in methods:
                    if method.upper() not in allowed_methods:
                        raise ValueError(f"Invalid HTTP method provided: {method}")

            if methods is None:
                methods = ["GET"]

            def decorator(
                handler: Callable[..., Awaitable[T]]
            ) -> Callable[..., Awaitable[T]]:
                if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
                    raise TypeError("ASGI can only register asynchronous functions.")
                converted_path, path_regex = Converter()._regex_converter(
                    path, strict_slashes, ''
                )
                self.routes.append(
                    (
                        converted_path,
                        methods,
                        handler,
                        path_regex,
                        response_model,
                        endpoint,
                    )
                )
                return handler

            return decorator
        except Exception as e:
            if self.debug:
                print(e)
            else:
                raise InternalServerError
            
    def _helper_route_setup(self):
        routes_to_add = []

        for route in routing._routes:
            path, methods, handler, strict_slashes, response_model, endpoint = route
            route_tuple = (
                path,
                tuple(methods),
                handler,
                strict_slashes,
                response_model,
                endpoint,
            )

            if route_tuple not in self.routes:
                routes_to_add.append(route_tuple)

        self.routes.extend(routes_to_add)
    
    def add_route(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        response_model: Optional[Type[T]] = None,
        endpoint: Optional[Callable[..., Awaitable[T]]] = None,
        strict_slashes: bool = True
    ) -> None:
        """
        We no longer document this add_route style API, and its usage is discouraged.
        Instead you should use the following approach:

        >>> ROUTING = [
                routing.route('/', methods=['GET', 'POST'], endpoint=home)
            ]
        """
        warnings.warn(
            "The `add_route` is deprecated, and will be removed in version 1.12. ",  # noqa: E501
            DeprecationWarning,
        )
        if endpoint is None:
            raise ValueError("Handler function is required for adding a route.")
        
        if not (inspect.iscoroutinefunction(endpoint) or inspect.isasyncgenfunction(endpoint)):
            raise TypeError("ASGI can only register asynchronous functions.")

        if not path.startswith('/'):
            raise TypeError("Paths must start with '/'.")
        
        if methods is not None:
            allowed_methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"]
            for method in methods:
                if method.upper() not in map(str.upper, allowed_methods):
                    raise ValueError(f"Invalid HTTP method provided: {method}")

        if methods is None:
            methods = ["GET"]

        converted_path, path_regex = Converter()._regex_converter(
            path, strict_slashes, ''
        )
        handler = endpoint
        self.routes.append(
            (
                converted_path,
                methods,
                handler,
                path_regex,
                response_model,
                endpoint,
            )
        )

    def add_websocket_route(
        self,
        path: str,
        handler: Optional[Callable[..., Awaitable[T]]] = None
    ) -> None:
        """
        We no longer document this add_websocket_route style API, and its usage is discouraged.
        Instead you should use the following approach:

        >>> ROUTING = [
                routing.websocket('/ws', endpoint=func)
            ]
        """
        warnings.warn(
            "The `add_websocket_route` is deprecated, and will be removed in version 1.12. ",  # noqa: E501
            DeprecationWarning,
        )
        if handler is None:
            raise ValueError("Handler function is required for adding a websocket route.")
        
        if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
            raise TypeError("ASGI Websocket can only register asynchronous functions.")
            
        if not path.startswith('/'):
            raise TypeError("Websocket paths must start with '/'.")
            
        compiled_path, path_regex = Converter()._regex_converter(path, False)
        self.websockets.append((compiled_path, path_regex, handler))
    
    def request_stage(
        self,
        stage: Union[Callable[..., Awaitable[T]], str],
        order: int = 0,
        condition: Optional[Callable[..., bool]] = None,
        group: Optional[str] = None,
        exclude: Optional[str] = None,
        inherit: Optional[str] = None
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            self.request_stage_handlers[stage].append((wrapper, order, condition))
            self.request_stage_handlers[stage] = sorted(self.request_stage_handlers[stage], key=lambda x: x[1])
            
            if group:
                if group not in self.grouped_request_stages:
                    self.grouped_request_stages[group] = {}
                self.grouped_request_stages[group].setdefault(stage, []).append(wrapper)
                
            if exclude:
                self.excluded_stages.setdefault(exclude, set()).add(wrapper)
                
            if inherit:
                self._inherit_from_group(stage, group, inherit)

            return wrapper

        return decorator
    
    def stage_handler(
        self,
        func: Callable,
        stage: Union[Callable[..., Awaitable[Any]], str],
        order: int = 0,
        condition: Optional[Callable[..., bool]] = None,
        group: Optional[str] = None,
        exclude: Optional[str] = None,
        inherit: Optional[str] = None
    ) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        self.request_stage_handlers.setdefault(stage, []).append((wrapper, order, condition))
        self.request_stage_handlers[stage] = sorted(self.request_stage_handlers[stage], key=lambda x: x[1])

        if group:
            if group not in self.grouped_request_stages:
                self.grouped_request_stages[group] = {}
            self.grouped_request_stages[group].setdefault(stage, []).append(wrapper)

        if exclude:
            self.excluded_stages.setdefault(exclude, set()).add(wrapper)

        if inherit:
            self._inherit_from_group(stage, group, inherit)

        return wrapper

    def _inherit_from_group(
        self,
        stage: Union[Callable[..., Awaitable[T]], str],
        group: Optional[str],
        inherit_group: Optional[str]
    ) -> None:
        if group in self.grouped_request_stages and inherit_group in self.grouped_request_stages:
            inherited_stages = self.grouped_request_stages[inherit_group].get(stage, [])
            self.grouped_request_stages[group].setdefault(stage, []).extend(inherited_stages)

    
    async def _execute_request_stage_handlers(
        self,
        stage: Union[Callable[..., Awaitable[T]], str],
        *args: Optional[Union[Callable[..., Awaitable[T]], str]],
        context: Dict[str, Any],
        **kwargs
    ) -> Any:
        handlers = self.request_stage_handlers[stage] + self.grouped_request_stages.get(stage, [])
        if stage in self.excluded_stages:
            handlers = [handler for handler in handlers if handler not in self.excluded_stages[stage]]
        for handler, _, condition in handlers:
            try:
                if not condition or (condition and condition(*args, **kwargs)):
                    func_args = list(signature(handler).parameters.keys())
                    handler_args = args + (context,) if 'context' in func_args else args
                    result = await handler(*handler_args, **kwargs)
                    if result:
                        return result
            except Exception as e:
                if self.debug:
                    await handle_exception(e, *args)
                    print(f"Error in {stage} request stage handler: {e}")
                else:
                    return await self._error_validator(500)
        return None

    def include(
        self,
        schematic: Dict[str, Schematic[ASGIApp]],
        include_middlewares: Optional[bool] = False
    ) -> None:
        for url_prefix, schematic_instance in schematic.items():
            self._process_routes(schematic_instance, url_prefix)
            if include_middlewares:
                self._add_middlewares(schematic_instance)
            self._process_schematic_instance(schematic_instance, url_prefix)

    def _process_routes(self, schematic_instance: Schematic[ASGIApp], url_prefix: str) -> None:
        for route in schematic_instance.routes:
            path, methods, handler, strict_slashes, response_model, endpoint = route

            if path.endswith('/'):
                path = ''  # Simulating the root_path

            converted_path, path_regex = Converter()._regex_converter(url_prefix + path, strict_slashes)

            self.routes.append(
                (
                    converted_path,
                    methods,
                    handler,
                    path_regex,
                    response_model,
                    endpoint,
                )
            )

    def _add_middlewares(self, schematic_instance: Schematic[ASGIApp]) -> None:
        self._middlewares.extend(schematic_instance.middlewares)

    def _process_schematic_instance(self, schematic_instance: Schematic[ASGIApp], url_prefix: str) -> None:
        if schematic_instance.schematic_id is not None:
            self._update_schematic_info(schematic_instance)
            self._print_schematic_info(schematic_instance, url_prefix)

        self._process_websockets(schematic_instance, url_prefix)

    def _update_schematic_info(self, schematic_instance: Schematic[ASGIApp]) -> None:
        self.schematic_id = schematic_instance.schematic_id
        self.schematic = schematic_instance.get_schematic()

    def _print_schematic_info(self, schematic_instance: Schematic[ASGIApp], url_prefix: str) -> None:
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

    def _process_websockets(self, schematic_instance: Schematic[ASGIApp], url_prefix: str) -> None:
        if schematic_instance.websockets:
            print(f"{ColoursCode.BOLD}WebSocket Routes:{ColoursCode.RESET}")

            for path, handler in schematic_instance.websockets:
                full_path = url_prefix + path
                self.websockets.append(
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

    def middleware(
        self,
        type: str = "http",
        order: Optional[int] = 0,
        conditions: Optional[List[Callable[..., bool]]] = None,
        group: Optional[str] = None,
        active: bool = True,
        excludes: Optional[Callable[..., Awaitable[T]]] = None
    ) -> Callable:
        if type not in ["http"]:
            raise ValueError(f"Invalid middleware type: {type}. Supported types are 'http'.")

        def decorator(middleware_func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            middleware_entry = {
                "middleware": middleware_func,
                "type": type,
                "order": order,
                "conditions": conditions,
                "group": group,
                "excludes": excludes,
                "type": type
            }
            self._middlewares.append(middleware_entry)
            self._middlewares.sort(key=lambda m: m["order"])
            if group:
                self.middleware_groups[group].append(middleware_func)
            self.middleware_activation[middleware_func] = active
            if excludes:
                self.middleware_exclusions[excludes].append(middleware_func)
            return middleware_func
        return decorator

    def add_middleware( 
        self,
        middleware: Callable[..., Awaitable[T]],
        order: Optional[int] = 0,
        conditions: Optional[List[Callable[..., bool]]] = None,
        group: Optional[str] = None,
        active: bool = True,
        excludes: Optional[Callable[..., Awaitable[T]]] = None,
        type: str = 'http'
    ) -> None:
        if type not in ["http"]:
            raise ValueError(f"Invalid middleware type: {type}. Supported types are 'http'.")
        middleware_entry = {
            "middleware": middleware,
            "order": order,
            "conditions": conditions,
            "group": group,
            "excludes": excludes,
            "type": type
        }
        self._middlewares.append(middleware_entry)
        self._middlewares.sort(key=lambda m: m["order"])
        if group:
            self.middleware_groups[group].append(middleware)
        self.middleware_activation[middleware] = active
        if excludes:
            self.middleware_exclusions[excludes].append(middleware)

    async def apply_middlewares(
        self, request: Request, response: Response
    ) -> Response:
        executed_middlewares = set()

        for middleware_entry in self._middlewares:
            middleware = middleware_entry["middleware"]
            conditions = middleware_entry.get("conditions")
            group = middleware_entry.get("group")
            excludes = middleware_entry.get("excludes")

            if group and middleware not in self.middleware_groups[group]:
                continue

            if not self.middleware_activation.get(middleware, True):
                continue

            if conditions:
                if not all(cond(request) for cond in conditions):
                    continue

            if excludes:
                exclusions = self.middleware_exclusions[excludes]
                if any(exc in executed_middlewares for exc in exclusions):
                    continue

            response = await middleware(request, response)
            executed_middlewares.add(middleware)

        return response
    
    async def handle_request(
        self,
        scope: Dict[str, Scope],
        receive: Callable[..., Awaitable[Receive]],
        send: Callable[..., Awaitable[Send]],
    ) -> None:
        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        request = Request(scope, receive)
        response = None
        context: Dict[str, List[Callable[..., Awaitable[T]]]] = {}

        try:
            self._helper_route_setup()
            allowed_methods = set()

            if not self.routes:
                if self.debug:
                    response = HTMLResponse(urlI8N())
                else:
                    response = HTMLResponse("<h1>Welcome to Aquilify, Your installation successful.</h1><p>You have debug=False in you Aquilify settings, change it to True in use of development for better experiance.")
            for (
                route_pattern,
                methods,
                handler,
                path_regex,
                response_model,
                endpoint,
            ) in self.routes:
                match = path_regex.match(path)
                if match:
                    if not methods or method.upper() in map(str.upper, methods):
                        path_params = match.groupdict()
                        processed_path_params = {key: self._convert_value(value) for key, value in path_params.items()}
                        request.path_params = processed_path_params

                        await self._execute_request_stage_handlers(RequestStage.BEFORE.value, request, context=context)

                        await self._context_processer(request)
                        scope['context'] = request.context ## context manager ..., Awaitable

                        for transformer in self.request_transformers:
                            request = await transformer(request)

                        handler_params = inspect.signature(handler).parameters

                        if 'request' in handler_params:
                            parser = Reqparser()

                            if 'parser' in handler_params:
                                response = await handler(request, parser=parser, **request.path_params)
                            else:
                                if request.path_params:
                                    valid_path_params = {key: value for key, value in request.path_params.items() if key in handler_params}
                                    response = await handler(request, **valid_path_params)
                                else:
                                    response = await handler(request)
                        else:
                            handler_kwargs = {param.name: request.path_params[param.name] for param in handler_params.values() if param.name in request.path_params}

                            if handler_kwargs and not request.path_params:
                                raise ValueError("Handler kwargs provided without request.path_params")

                            response = await handler(**handler_kwargs)

                        response = await self._process_response(response, handler.__name__)

                        if response_model:
                            response = self._validate_and_serialize_response(
                                response, response_model
                            )

                        break

                    else:
                        allowed_methods.update(methods)

            if response is None:
                if allowed_methods:
                    response = await self._error_validator(405, request, allowed_methods)
                else:
                    response = await self._error_validator(404, request)

            for transformer in self.response_transformers:
                response = await transformer(response)

            response = await self.apply_middlewares(request, response)
            if not isinstance(response, (Response, Awaitable)):
                raise ValueError("Middleware must return a Response object or Awaitable[Response]")
            
            await self._execute_request_stage_handlers(RequestStage.AFTER.value, request, response, context=context)

        except Exception as e:
            response = await self._process_exception(e, request)

        await response(scope, receive, send)

    async def _context_processer(self, request: Request):
        request.context['_request'] = request
        request.context['_app'] = self

    async def _process_exception(self, e, request) -> Response:
        reversed_exception_dict = {v: k for k, v in exception_dict.items()}
        if type(e) in reversed_exception_dict:
            status_code = reversed_exception_dict[type(e)]
            response = await self._error_validator(status_code, request)
            return response
        else:
            if self.debug:
                response = await handle_exception(e, request)
            elif self.exception_handlers:
                response = await self.exception_handlers(e, request)
            else:
                response = await self._error_validator(500)
        return response
    
    def _convert_value(self, value):
        if isinstance(value, int):
            return int(value)
        elif isinstance(value, str):
            if value.isdigit():
                return int(value)
            try:
                return float(value)
            except ValueError:
                return value
        return str(value)

    async def _process_response(self, response, caller_function) -> Response:
        caller_function_name = caller_function
        if isinstance(response, str):
            if response.startswith("<"):
                try:
                    ET.fromstring(response)
                    response = Response(response, content_type='application/xml')
                except ET.ParseError:
                    response = Response(response, content_type='text/html')
            else:
                response = Response(response, content_type='text/plain')
        elif isinstance(response, dict):
            response = Response(content=json.dumps(response), content_type='application/json')
        elif isinstance(response, tuple) and len(response) == 2 and isinstance(response[1], int):
            if isinstance(response[0], str):
                if response[0].startswith("<"):
                    try:
                        ET.fromstring(response[0])
                        response = Response(response[0], content_type='application/xml', status_code=response[1])
                    except ET.ParseError:
                        response = Response(response[0], content_type='text/html', status_code=response[1])
                else:
                    response = Response(response[0], content_type='text/plain', status_code=response[1])
            elif isinstance(response[0], dict):
                response = Response(content=json.dumps(response[0]), content_type='application/json', status_code=response[1])
            elif isinstance(response[0], list):
                def handle_nested(item):
                    return item if isinstance(item, (str, bytes)) else json.dumps(item)

                processed_list = [handle_nested(item) for item in response[0]]
                
                if all(isinstance(item, (str, bytes)) for item in processed_list):
                    response = Response(content=json.dumps(processed_list), content_type='application/json', status_code=response[1])
                else:
                    response = InternalServerError("Unable to process the list structure")
        elif isinstance(response, list):
            def handle_nested(item):
                return item if isinstance(item, (str, bytes)) else json.dumps(item)

            processed_list = [handle_nested(item) for item in response]
            
            if all(isinstance(item, (str, bytes)) for item in processed_list):
                response = Response(content=json.dumps(processed_list), content_type='application/json')
            else:
                response = InternalServerError("Unable to process the list structure")
        elif not isinstance(response, Response):
            received_type = type(response).__name__
            expected_types = ", ".join([typ.__name__ for typ in [str, dict, Response]])
            raise TypeError(f"Function '{caller_function_name}': Invalid response type: Received {received_type}. Expected types are {expected_types}.")
        return response

    async def _error_validator(self, error_code, *args):
        if error_code in self.error_handlers:
            if error_code == 500:
                error_handler = self.error_handlers[error_code]
                response = await error_handler() if not args else await error_handler(*args)
            else:
                error_handler = self.error_handlers[error_code]
                response = await error_handler(*args) if args else await error_handler()

            if isinstance(response, str):
                return Response(content=response, content_type="text/plain", status_code=error_code)
            elif isinstance(response, dict):
                return Response(content=json.dumps(response), status_code=error_code, content_type='application/json')
            elif isinstance(response, Response):
                return response
            else:
                received_type = type(response).__name__
                expected_types = ", ".join([typ.__name__ for typ in [str, dict, Response]])
                raise HTTPException(f"Invalid response type: Received {received_type}. Expected types are {expected_types}")
        
        if error_code in exception_dict:
            if error_code == 404 and self.debug:
                request: Request = args[0]
                return Response(debug_404(routing._links, { 'path': request.path, 'client_ip': request.remote_addr, 'user_agent': request.user_agent, 'url': request.url, 'method': request.method }), 404, content_type='text/html')
            elif error_code == 405 and self.debug:
                request: Request = args[0]
                return Response(debug_405({ 'method': request.method, "url": request.url, "client_ip": request.remote_addr, "user_agent": request.user_agent, "allowed_method": args[1]}), 405, content_type='text/html')
            else:
                return exception_dict[error_code]()
        else:
            raise TypeError('Unsupported error type! : {}'.format(error_code))

    def _validate_and_serialize_response(
        self, response: Response, response_model: Type[T]
    ) -> Response:
        if not isinstance(response, response_model):
            raise ValueError(
                f"Response does not match the expected model {response_model.__name__}"
            )
        return Response(content=response.dict(), content_type="application/json")
    
    def websocket(
        self,
        path: str
    ) -> Callable[..., Awaitable[T]]:
        """
        We no longer document this decorator style API, and its usage is discouraged.
        Instead you should use the following approach:

        >>> ROUTING = [
                routing.websocket('/ws', endpoint=func)
            ]
        """
        warnings.warn(
            "The `decorator` is deprecated, and will be removed in version 1.12. ",  # noqa: E501
            DeprecationWarning,
        )
        def decorator(
            handler: Callable[..., Awaitable[T]]
        ) -> Callable[..., Awaitable[T]]:
            if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
                raise TypeError("ASGI Websocket, can only register asynchronous functions.")
            if not path.startswith('/'):
                raise TypeError("Websocket paths must startwith '/'.")
            compiled_path, path_regex = Converter()._regex_converter(path, False)
            self.websockets.append((compiled_path, path_regex, handler))
            return handler

        return decorator

    async def _websocket_handler(
        self,
        scope: Dict[str, Scope],
        receive: Callable[..., Awaitable[Receive]],
        send: Callable[..., Awaitable[Send]],
    ) -> None:
        ws = WebSocket(scope, receive, send)
        try:
            await self._websocket_routes(ws)
            await self._helper_websocket_routes(ws)
        except WebSocketDisconnect as e:
            await ws.close(code=e.code, reason=e.reason)
        except RuntimeError as e:
            if ws.client_state != WebSocketState.CONNECTED:
                await ws.close(code=403, reason="Connection rejected")
            else:
                await ws.close(code=1011, reason="Unexpected condition")
        except Exception as e:
            await ws.send_text(f"Error: {str(e)}")
            if ws.application_state != WebSocketState.CONNECTED:
                await ws.close(code=1006, reason="Connection closed unexpectedly")
            else:
                await ws.close(code=1011, reason="Unexpected condition")

    async def _websocket_routes(self, ws: WebSocket) -> None:
        for path, path_regex, handler in self.websockets:
            match = path_regex.match(ws.path)
            if match:
                ws.path_params = match.groupdict()
                response = await handler(ws, **ws.path_params)
                if not isinstance(response, WebSocket):
                    received_type = type(response).__name__
                    expected_types = ", ".join([typ.__name__ for typ in [WebSocket]])
                    raise TypeError(f"Invalid response type: Received {received_type}. Expected types are {expected_types}.")
                return response
            
    async def _helper_websocket_routes(self, ws: WebSocket) -> None:
        for path, path_regex, handler in routing._websockets:
            match = path_regex.match(ws.path)
            if match:
                ws.path_params = match.groupdict()
                response = await handler(ws, **ws.path_params)
                if not isinstance(response, WebSocket):
                    received_type = type(response).__name__
                    expected_types = ", ".join([typ.__name__ for typ in [WebSocket]])
                    raise TypeError(f"Invalid response type: Received {received_type}. Expected types are {expected_types}.")
                return response
            
    def _load_exception_handler(self) -> Optional[
            Mapping[
                Any,
                Callable[
                    [Request, Exception],
                    Union[Response, Awaitable[Response]],
                ],
            ]
        ]:
        try:
            exception_handler: Optional[str] = getattr(settings, 'EXCEPTION_HANDLER', None)
            if exception_handler is not None:
                if not isinstance(exception_handler, str):
                    raise ImproperlyConfigured("Invalid exception_handler type, excepted string")
            if exception_handler:
                _handler = import_string(exception_handler)
                if inspect.isclass(_handler):
                    self.exception_handlers = _handler()
                else:
                    if not (inspect.iscoroutinefunction(_handler) or inspect.isasyncgenfunction(_handler)):
                        raise TypeError("ASGI can only register asynchronous functions or class of Exception handler.")
                    self.exception_handlers = _handler
            else:
                self.exception_handlers = None 
        except ImproperlyConfigured as config_error:
            raise ImproperlyConfigured(f"Error loading {exception_handler} Exception handler: {config_error}")
        except ImportError as import_error:
            raise ImproperlyConfigured(f"Error importing {exception_handler} Exception handler: {import_error}")
        except Exception as e:
            raise ImproperlyConfigured(f"An unexpected error occurred: {e}")
        
    async def __call__(
        self, scope: Dict[str, Scope], receive: Callable[..., Awaitable[Receive]], send: Callable[..., Awaitable[Send]]
    ) -> None:
        scope['app'] = self
        if self.schematic is not None:
            scope['schematic'] = self.schematic
        if scope['type'] == 'http':
            await self._http(scope, receive, send)
        elif scope['type'] == 'websocket':
            await self._websocket_handler(scope, receive, send)
        elif scope['type'] == 'lifespan':
            await self._lifespan(scope, receive, send)

    async def _http(
        self,
        scope: Dict[str, Scope],
        receive: Callable[..., Awaitable[Receive]],
        send: Callable[..., Awaitable[Send]]
    ) -> None:
        try:
            await self.handle_request(scope, receive, send)
        except Exception as e:
            if self.debug:
                request = Request(scope, receive, send)
                response = await handle_exception(e, request)
            elif self.exception_handlers:
                request = Request(scope, receive, send)
                response = await self.exception_handlers(e, request)
            else:
                response = await self._error_validator(500)
            await response(scope, receive, send)

    async def _lifespan(
        self,
        scope: Dict[str, Scope],
        receive: Callable[..., Awaitable[Receive]],
        send: Send
    ) -> Lifespan:
        
        started = False
        event: StatefulLifespan = await receive() 
        try:
            if event['type'] == 'lifespan.startup':
                await self._startup_handlers()
                await send({"type": "lifespan.startup.complete"})
                started = True
                await receive()
        except BaseException:
            exc_text = traceback.format_exc()
            if started:
                await send({"type": "lifespan.shutdown.failed", "message": exc_text})
            else:
                await send({"type": "lifespan.startup.failed", "message": exc_text})
            raise
        else:
            await self._shutdown_handlers()
            await send({"type": "lifespan.shutdown.complete"})

    async def _startup_handlers(self) -> None:
        for handler in self.startup_handlers:
            if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
                raise TypeError("ASGI can only register asynchronous lifespan functions.")
            await handler()

    async def _shutdown_handlers(self) -> None:
        for handler in self.shutdown_handlers:
            if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
                raise TypeError("ASGI can only register asynchronous lifespan functions.")
            await handler()

    def event(self, event_type: str) -> Callable:
        def decorator(handler: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            if event_type == 'startup':
                self.startup_handlers.append(handler)
            elif event_type == 'shutdown':
                self.shutdown_handlers.append(handler)
            return handler
        return decorator

    def _check_events(self, on_startup: Lifespan, on_shutdown: Lifespan):
        if on_startup:
            if isinstance(on_startup, list):
                self.startup_handlers.extend(on_startup)
            else:
                self.startup_handlers.append(on_startup)

        if on_shutdown:
            if isinstance(on_shutdown, list):
                self.shutdown_handlers.extend(on_shutdown)
            else:
                self.shutdown_handlers.append(on_shutdown)
                
    def _check_lifespan_settings(self):
        _settings = ASGILifespanLoader().load_asgi_lifespans()
        for lifespan in _settings:
            if lifespan.get('event') == 'startup':
                self.startup_handlers.append(lifespan.get('origin'))
            elif lifespan.get('event') == 'shutdown':
                self.shutdown_handlers.append(lifespan.get('origin'))
            else:
                raise HTTPException('Invalid event type! {} use either startup or shutdown.'.format(lifespan.get('origin')))
