
# Aquilify devops / Test _app @noql :: 3211

from __future__ import annotations

import asyncio
import re
import zlib
import json
from collections import defaultdict

from ..wrappers import (
    Request,
    Response
)

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
)

from ..exception.base import (
    BadRequest,
    NotFound,
    MethodNotAllowed,
    Unauthorized,
    Forbidden,
    InternalServerError
)

from ..exception.__handler import handle_exception

T = TypeVar("T")

class Aquilify:
    def __init__(self, debug: bool = False) -> None:
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
        self.exception_handlers: Dict[
            Type[Exception], Callable[..., Awaitable[T]]
        ] = {}
        self.middlewares: List[Callable[..., Awaitable[T]]] = []
        self.middleware_order: List[Tuple[Callable[..., Awaitable[T]], int]] = []
        self.url_patterns: Dict[str, str] = {}
        self.request_transformers: List[Callable[..., Awaitable[Request]]] = []
        self.response_transformers: List[
            Callable[..., Awaitable[Response]]
        ] = []
        self.compression_enabled: bool = False
        self.messages: List[Callable[..., Awaitable[T]]] = []
        self.middleware_groups: Dict[str, List[Callable[..., Awaitable[T]]]] = {}
        self.middleware_activation: Dict[Callable[..., Awaitable[T]], bool] = {}
        self.middleware_dependencies: Dict[Callable[..., Awaitable[T]], List[Callable[..., Awaitable[T]]]] = defaultdict(list)
        self.middleware_exclusions: Dict[Callable[..., Awaitable[T]], List[Callable[..., Awaitable[T]]]] = defaultdict(list)
        self.debug = debug

    def add_exception_handler(
        self, exception_cls: Type[Exception], handler: Callable[..., Awaitable[T]]
    ) -> None:
        self.exception_handlers[exception_cls] = handler

    def route(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        response_model: Optional[Type[T]] = None,
        endpoint: Optional[str] = None,
        strict_slashes: bool = True,
    ) -> Callable[..., Awaitable[T]]:
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"]
        try:
            if methods is not None:
                for method in methods:
                    if method not in allowed_methods:
                        raise ValueError(f"Invalid HTTP method provided: {method}")

            if methods is None:
                methods = ["GET"]

            def decorator(
                handler: Callable[..., Awaitable[T]]
            ) -> Callable[..., Awaitable[T]]:
                converted_path, path_regex = self._regex_coverter(
                    path, strict_slashes
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
                InternalServerError()

    def _regex_coverter(
        self, path: str, strict_slashes: bool
    ) -> Tuple[str, Pattern]:
        if strict_slashes:
            pattern = re.sub(r"{([^}]+)}", r"(?P<\1>[^/]+)", path)
        else:
            pattern = re.sub(r"{([^}]+)}", r"(?P<\1>[^/]+/?)", path)
        pattern = f"^{pattern}$"
        path_regex = re.compile(pattern)
        return pattern, path_regex
    
    def middleware(
        self,
        middleware: Callable[..., Awaitable[T]],
        order: Optional[int] = 0,
        conditions: Optional[List[Callable[..., bool]]] = None,
        group: Optional[str] = None,
        active: bool = True,
        excludes: Optional[Callable[..., Awaitable[T]]] = None,
    ) -> None:
        middleware_entry = {
            "middleware": middleware,
            "order": order,
            "conditions": conditions,
            "group": group,
            "excludes": excludes,
        }
        self.middlewares.append(middleware_entry)
        self.middlewares.sort(key=lambda m: m["order"])
        if group:
            self.middleware_groups[group].append(middleware)
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
        scope: Dict[str, Any],
        receive: Callable[..., Awaitable[Any]],
        send: Callable[..., Awaitable[None]],
    ) -> None:
        path = scope.get("path", "/")
        method = scope.get("method", "GET")
        request = Request(scope, receive)
        response = None

        try:
            allowed_methods = set()
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
                    if not methods or method in methods:
                        request.path_params = match.groupdict()

                        for transformer in self.request_transformers:
                            request = await transformer(request)

                        response = await handler(request)

                        if isinstance(response, str):
                            response = Response(content=response, content_type="text/plain")
                        elif isinstance(response, dict):
                            response = Response(content=json.dumps(response), content_type='application/json')
                        elif not isinstance(response, Response):
                            raise ValueError("Invalid response type")

                        if response_model:
                            response = self.validate_and_serialize_response(
                                response, response_model
                            )

                        break

                    else:
                        allowed_methods.update(methods)

            if response is None:
                if allowed_methods:
                    response = MethodNotAllowed(allowed_methods)
                else:
                    response = NotFound()

            for transformer in self.response_transformers:
                response = await transformer(response)

            response = await self.apply_middlewares(request, response)

            if self.compression_enabled:
                response = self.compress_response(response)

        except Exception as e:
            if isinstance(e, BadRequest):
                response = e
            elif isinstance(e, Forbidden):
                response = e
            elif isinstance(e, Unauthorized):
                response = e
            else:
                if self.debug:
                    response = await handle_exception(e)
                else:
                    response = InternalServerError()

        await response(scope, receive, send)

    def validate_and_serialize_response(
        self, response: Response, response_model: Type[T]
    ) -> Response:
        if not isinstance(response, response_model):
            raise ValueError(
                f"Response does not match the expected model {response_model.__name__}"
            )
        return Response(content=response.dict(), content_type="application/json")

    async def lifespan(
        self, scope: Dict[str, Any], receive: Callable[..., Awaitable[Any]], send: Callable[..., Awaitable[None]]
    ) -> None:
        started = False
        event = await receive() 
        try:
            if event['type'] == 'lifespan.startup':
                await self.startup()
                await send({"type": "lifespan.startup.complete"})
                started = True
                await receive()
        except BaseException:
            import traceback
            exc_text = traceback.format_exc()
            if started:
                await send({"type": "lifespan.shutdown.failed", "message": exc_text})
            else:
                await send({"type": "lifespan.startup.failed", "message": exc_text})
            raise
        else:
            await self.shutdown()
            await send({"type": "lifespan.shutdown.complete"})

    async def __call__(
        self, scope: Dict[str, str], receive, send
    ) -> None:
        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)
        elif scope["type"] == "http":
            try:
                await self.handle_request(scope, receive, send)
            except Exception as e:
                if self.debug:
                    response = await handle_exception(e)
                else:
                    response = InternalServerError()
                await response(scope, receive, send)

    async def startup(self):
        print('starting.....')

    async def shutdown(self):
        print('shutting down....')

    def generate_url(self, route_name: str, **kwargs: Any) -> str:
        if route_name in self.url_patterns:
            pattern = self.url_patterns[route_name]
            for key, value in kwargs.items():
                pattern = pattern.replace(f"{{{key}}}", str(value))
            return pattern
        else:
            raise ValueError(f"Route name '{route_name}' not found in url patterns.")

    def compress_response(self, response: Response) -> Response:
        if response.content_type and "text/" in response.content_type:
            compressed_content = zlib.compress(response.body.encode("utf-8"))
            response.body = compressed_content.decode("utf-8")
            response.headers["Content-Encoding"] = "gzip"
        return response
