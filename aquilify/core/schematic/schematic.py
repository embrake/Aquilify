from __future__ import annotations

import secrets
import inspect

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
    Pattern
)

from . import routing

T = TypeVar("T")

class Schematic:
    def __init__(self, name: str):
        self.name = name
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
        self.middlewares: List[Callable[..., Awaitable[T]]] = []
        self.schematic_id = secrets.token_hex(11)
        self.middleware(self._schematicIdMiddleware)
        self._helper_route_setup()

    def rule(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        response_model: Optional[Type[T]] = None,
        endpoint: Optional[str] = None,
        strict_slashes: bool = True,
    ) -> Callable[..., Awaitable[T]]:
        allowed_methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"]
        try:

            if not path.startswith('/'):
                raise TypeError("Paths must start with '/'.")
            
            if methods is not None:
                for method in methods:
                    if method not in allowed_methods:
                        raise ValueError(f"Invalid HTTP method provided: {method}")

            if methods is None:
                methods = ["GET"]

            def decorator(
                handler: Callable[..., Awaitable[T]]
            ) -> Callable[..., Awaitable[T]]:
                if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
                    raise TypeError("ASGI can only register asynchronous functions.")
                self.routes.append(
                    (
                        path,
                        methods,
                        handler,
                        strict_slashes,
                        response_model,
                        endpoint,
                    )
                )
                return handler
            return decorator
        except Exception as e:
            raise e
        
    def add_rule(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        endpoint: Optional[Callable[..., Awaitable[T]]] = None,
        response_model: Optional[Type[T]] = None,
        strict_slashes: bool = True,
    ) -> None:
        handler = endpoint
        if handler is None:
            raise ValueError("Handler function is required for adding a route.")
        
        if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
            raise TypeError("ASGI can only register asynchronous functions.")

        if not path.startswith('/'):
            raise TypeError("Paths must start with '/'.")
        
        if methods is not None:
            allowed_methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"]
            for method in methods:
                if method not in allowed_methods:
                    raise ValueError(f"Invalid HTTP method provided: {method}")

        if methods is None:
            methods = ["GET"]

        self.routes.append(
            (
                path,
                methods,
                handler,
                strict_slashes,
                response_model,
                endpoint,
            )
        )

    def websocket(
        self,
        path: str
    ) -> Callable[..., Awaitable[T]]:
        def decorator(
            handler: Callable[..., Awaitable[T]]
        ) -> Callable[..., Awaitable[T]]:
            if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
                raise TypeError("ASGI Websocket, can only register asynchronous functions.")
            if not path.startswith('/'):
                raise TypeError("Websocket paths must startwith '/'.")
            self.websockets.append((path, handler))
            return handler

        return decorator

    def add_websocket_rule(
        self,
        path: str,
        handler: Optional[Callable[..., Awaitable[T]]] = None
    ) -> None:
        if handler is None:
            raise ValueError("Handler function is required for adding a websocket route.")
        
        if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
            raise TypeError("ASGI Websocket can only register asynchronous functions.")
            
        if not path.startswith('/'):
            raise TypeError("Websocket paths must start with '/'.")
            
        self.websockets.append((path, handler))
        
    def middleware(
        self,
        middleware: Callable[..., Awaitable[T]],
        order: Optional[int] = 0,
        conditions: Optional[List[Callable[..., bool]]] = None,
        group: Optional[str] = None,
        active: bool = True,
        excludes: Optional[Callable[..., Awaitable[T]]] = None,
    ) -> None:
        """To use schematic middleware enable middlewares in the include function 
        ```python
        app.include({
           '/blog': my_schematic
        }), 
        middlewares = True)"""
        middleware_entry = {
            "middleware": middleware,
            "order": order,
            "conditions": conditions,
            "group": group,
            "excludes": excludes,
        }
        self.middlewares.append(middleware_entry)

    def _helper_route_setup(self):
        for route in routing.routes:
            path, methods, handler, strict_slashes, response_model, endpoint = route

            self.routes.append(
                (
                    path,
                    methods,
                    handler,
                    strict_slashes,
                    response_model,
                    endpoint,
                )
            )

    async def _schematicIdMiddleware(self, request, response):
        response.headers['schematic-instance-id'] = self.schematic_id
        return response
    
    def get_schematic(self) -> Callable[..., Awaitable]:
        return self
