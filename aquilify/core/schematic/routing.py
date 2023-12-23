import inspect

from typing import (
    Optional,
    List,
    Type,
    Callable,
    Awaitable,
    TypeVar,
    Tuple,
    Pattern,
    Dict,
    Any
)

T = TypeVar("T")

RouteInfo = Tuple[
    str, List[str], Callable[..., Awaitable[T]], List[str], Pattern, Type[T], str, Dict[str, Any]
]
Routes = List[RouteInfo]
WebSocketRoute = Tuple[str, Callable[..., Awaitable[T]]]
WebSocketRoutes = List[WebSocketRoute]

routes: Routes = []
websockets: WebSocketRoutes = []

def rule(
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

    routes.append(
        (
            path,
            methods,
            handler,
            strict_slashes,
            response_model,
            endpoint,
        )
    )

def websocket_rule(
        path: str,
        endpoint: Optional[Callable[..., Awaitable[T]]] = None
    ) -> None:
        handler = endpoint
        if handler is None:
            raise ValueError("Handler function is required for adding a websocket route.")
        
        if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
            raise TypeError("ASGI Websocket can only register asynchronous functions.")
            
        if not path.startswith('/'):
            raise TypeError("Websocket paths must start with '/'.")
            
        websockets.append((path, handler))