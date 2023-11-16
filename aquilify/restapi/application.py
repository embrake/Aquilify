import re
import json
import traceback
import inspect
from inspect import signature
from functools import wraps
from collections import defaultdict

from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Union,
    Pattern,
    Type,
    Match,
    List,
    Tuple,
    Optional,
    TypeVar,
    Mapping
)

from ..types import (
    ASGIApp,
    Scope,
    Message,
    Receive,
    Lifespan,
    StatefulLifespan
)


from ..wrappers import (
    Request,
    Response
)

from ..exception.base import (
    HTTPException,
    MethodNotAllowed,
    InternalServerError
)

from enum import Enum

from ..exception.__handler import handle_exception
from .reqparser import Reqparser

from .__status import exception_dict

class RequestStage(Enum):
    BEFORE: str = 'before'
    AFTER: str = 'after'

T = TypeVar("T")

class Resource:
    def __init__(self) -> None:
        self.parser: Reqparser = Reqparser()

    async def handle_request(self, request, method, **kwargs):
        try:
            allowed_methods = [m for m in dir(self) if not m.startswith("__") and callable(getattr(self, m))]
            
            if method.lower() in allowed_methods:
                handler = getattr(self, method.lower())
                try:
                    args = await self._argsparser(request)
                    return await handler(request, **args)
                except ValueError as e:
                    return Response(str(e), status_code=400)
            else:
                return MethodNotAllowed()
        except Exception as e:
            await handle_exception(e)
        
    async def _argsparser(self, request):
        try:
            args = await self.parser.parse(request)
            return args
        except ValueError as e:
            print(e)
            return {}

class Restful:
    def __init__(
        self,
        debug: bool = False,
        on_startup: Optional[Union[Callable[..., Awaitable[Any]], List[Callable[..., Awaitable[Any]]]]] = None,
        on_shutdown: Optional[Union[Callable[..., Awaitable[Any]], List[Callable[..., Awaitable[Any]]]]] = None,
        exception_handlers: Optional[
            Mapping[
                Any,
                Callable[
                    [Request, Exception],
                    Union[Response, Awaitable[Response]],
                ],
            ]
        ] = None,
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
        self.middlewares: List[Callable[..., Awaitable[T]]] = []
        self.middleware_order: List[Tuple[Callable[..., Awaitable[T]], int]] = []
        self.messages: List[Callable[..., Awaitable[T]]] = []
        self.middleware_activation: Dict[Callable[..., Awaitable[T]], bool] = {}
        self.middleware_dependencies: Dict[Callable[..., Awaitable[T]], List[Callable[..., Awaitable[T]]]] = defaultdict(list)
        self.middleware_exclusions: Dict[Callable[..., Awaitable[T]], List[Callable[..., Awaitable[T]]]] = defaultdict(list)
        self.startup_handlers: List[Callable[..., Awaitable[Lifespan]]] = []
        self.shutdown_handlers: List[Callable[..., Awaitable[Lifespan]]] = []
        self.grouped_request_stages: Dict[str, Dict[str, List[Callable]]] = {}
        self.error_handlers: Dict[str, Dict[str, List[Callable]]] = {}
        self.excluded_stages: Dict[str, List[Callable]] = {}
        self.request_stage_handlers: Dict[str, List[Tuple[Callable[..., Awaitable[None]], int, Optional[Callable]]]] = {
            RequestStage.BEFORE.value: [], 
            RequestStage.AFTER.value: []
        }
        self.debug: bool = debug
        self.exception_handlers = exception_handlers

        self._check_events(on_startup, on_shutdown)

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> ASGIApp:
        if scope['type'] == 'http':
            await self._http(scope, receive, send)
        elif scope['type'] == 'lifespan':
            await self._lifespan(scope, receive, send)

    def errorhandler(self, status_code: int) -> Callable:
        def decorator(handler: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            self.error_handlers[status_code] = handler
            return handler
        return decorator

    async def _http(
        self,
        scope: Dict[str, Scope],
        receive: Callable[..., Awaitable[Receive]],
        send: Callable[..., Awaitable[Message]]
    ) -> ASGIApp:
        try:
            request: Request = Request(scope, receive)
            response: Response = Response()
            context: Dict[str, List[Callable[..., Awaitable[T]]]] = {}

            route_found: bool = False
            for route, methods in self.routes:
                match: Match[str] = re.match(route, request.path)
                if match:
                    route_found = True
                    path_params: Dict[str, str] = match.groupdict()
                    request.path_params = path_params
                    await self._execute_request_stage_handlers(RequestStage.BEFORE.value, request, context=context)
                    response = await self.apply_middlewares(request, response)
                    if not isinstance(response, (Response, Awaitable)):
                        raise ValueError("Middleware must return a Response object or Awaitable[Response]")
                    if request.method in methods:
                        response = await methods[request.method](request, **request.path_params)

                        if isinstance(response, dict):
                            response = Response(content=json.dumps(response), content_type='application/json')
                        elif isinstance(response, tuple) and len(response) == 2 and isinstance(response[0], str) and isinstance(response[1], int):
                            response = Response(content=response[0], status_code=response[1])
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
                            raise TypeError(f"Invalid response type: Received {received_type}. Expected types are {expected_types}.")
                    else:
                        response = await self._error_validator(405, request)
                    break

            if not route_found:
                response = await self._error_validator(404, request)

            await self._execute_request_stage_handlers(RequestStage.AFTER.value, request, response, context=context)

        except Exception as e:
            response = await self._process_exception(e, request)

        await response(scope, receive, send)

    async def _process_exception(self, e, request) -> Response:
        reversed_exception_dict = {v: k for k, v in exception_dict.items()}
        if type(e) in reversed_exception_dict:
            status_code = reversed_exception_dict[type(e)]
            response = await self._error_validator(status_code, request)
            return response
        else:
            if self.debug:
                response = await handle_exception(e)
            elif self.exception_handlers:
                if not (inspect.iscoroutinefunction(self.exception_handlers) or inspect.isasyncgenfunction(self.exception_handlers)):
                    raise TypeError("ASGI can only register asynchronous functions or class.")
                response = await self.exception_handlers(e, request)
            else:
                response = await self._error_validator(500)
        return response

    async def _lifespan(
        self,
        scope: Dict[str, Scope],
        receive: Callable[..., Awaitable[Receive]],
        send: Callable[..., Awaitable[Message]]
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
            await handler()

    async def _shutdown_handlers(self) -> None:
        for handler in self.shutdown_handlers:
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

    def request_stage(self,
        stage: Union[Callable[..., Awaitable[T]], str],
        order: int = 0,
        condition: Optional[Callable[..., bool]] = None,
        group: Optional[str] = None,
        exclude: Optional[str] = None,
        inherit: Optional[str] = None) -> Callable:
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
                    await handle_exception(e)
                    print(f"Error in {stage} request stage handler: {e}")
                else:
                    return await self._error_validator(500)
        return None
    
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
            return exception_dict[error_code]()
        else:
            raise TypeError('Unsupported error type! : {}'.format(error_code))

    def middleware(
        self,
        middleware: Callable[..., Awaitable[T]],
        order: Optional[int] = 0,
        conditions: Optional[List[Callable[..., bool]]] = None,
        active: bool = True,
        excludes: Optional[Callable[..., Awaitable[T]]] = None,
    ) -> None:
        middleware_entry = {
            "middleware": middleware,
            "order": order,
            "conditions": conditions,
            "excludes": excludes,
        }
        self.middlewares.append(middleware_entry)
        self.middlewares.sort(key=lambda m: m["order"])
        self.middleware_activation[middleware] = active
        if excludes:
            self.middleware_exclusions[excludes].append(middleware)

    async def apply_middlewares(
        self, request: Request, response: Response
    ) -> Response:
        executed_middlewares = set()

        for middleware_entry in self.middlewares:
            middleware = middleware_entry["middleware"]
            conditions = middleware_entry.get("conditions")
            excludes = middleware_entry.get("excludes")

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
    
    def resources(
        self,
        resource_mapping: Dict[str, Type[Resource]]
    ) -> None:
        
        for path, resource_cls in resource_mapping.items():
            regex_pattern = self.convert_path_to_regex(path)
            methods_dict = {
                method.upper(): lambda req, m=method: resource_cls().handle_request(req, m)
                for method in ['GET', 'POST', 'PUT', 'DELETE']
            }
            self.routes.append((regex_pattern, methods_dict))

    @staticmethod
    def convert_path_to_regex(path: str) -> str:
        pattern: str = re.sub(r'{(\w+)}', r'(?P<\1>[^/]+)', path)
        return f"^{pattern}$"