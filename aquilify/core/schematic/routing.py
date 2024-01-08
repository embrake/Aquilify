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

class ImproperlyConfigured(Exception):
    pass

def rule(
    path: str,
    endpoint: Optional[Callable[..., Awaitable[Any]]] = None,
    **kwargs: Any
) -> Optional[List[Tuple]]:
    """
    Define an HTTP routing rule.

    Args:
    - path (str): The URL path pattern.
    - endpoint (Optional[Callable[..., Awaitable[T]]]): The function to be executed for the route.
    - **kwargs (Any): Additional keyword arguments.

    Supported **kwargs:
    - response_model (Optional[Type[T]]): The response model type.
    - strict_slashes (bool): Whether to consider trailing slashes.
    - methods (List[str]): HTTP methods supported by the route.
    - name (Optional[str]): The name of the route.

    Returns:
    - Optional[List[Tuple[str, EndpointType]]]: A list containing a tuple of path and endpoint.

    Example:
    >>> rule('/home', home_handler, methods=['GET', 'POST'], name='home_route')
    """
    if not path.startswith('/'):
        raise ImproperlyConfigured("Paths must start with '/'.")
    
    response_model = kwargs.pop('response_model', None)
    strict_slashes = kwargs.pop('strict_slashes', True)
    methods = kwargs.pop('methods', None)
        
    return (path, methods, endpoint, strict_slashes, response_model, endpoint, kwargs.get('name'))

def rule_all(
    path: str,
    endpoint: Callable[..., Awaitable[T]] = None,
    response_model: Optional[Type[T]] = None,
    strict_slashes: bool = True,
    name: Optional[str] = None
) -> Callable[..., Awaitable[T]]:
    """
    Define an HTTP routing rule for all methods.

    Args:
    - path (str): The URL path pattern.
    - endpoint (Callable[..., Awaitable[T]]): The function to be executed for the route.
    - response_model (Optional[Type[T]]): The response model type.
    - strict_slashes (bool): Whether to consider trailing slashes.
    - name (Optional[str]): The name of the route.

    Returns:
    - Callable[..., Awaitable[T]]: The function to handle the route.

    Example:
    >>> rule_all('/user', user_handler, UserModel, strict_slashes=False, name='user_route')
    """
    
    handler = endpoint
    allowed_methods = [
        "GET", "POST", "PUT", "DELETE",
        "HEAD", "OPTIONS", "PATCH", "TRACE"
    ]
    
    if not path.startswith('/'):
        raise ImproperlyConfigured("Paths must start with '/'.")
    
    return (
        path,
        allowed_methods,
        handler,
        strict_slashes,
        response_model,
        endpoint,
        name
    )
    
def re_rule(
    path_regex: str,
    endpoint: Optional[Callable[..., Awaitable[Any]]] = None,
    **kwargs: Any
    ) -> Optional[List[Tuple]]:
    """
    Define a regex-based HTTP routing rule.

    Args:
    - path_regex (str): The regex pattern for the URL path.
    - endpoint (Optional[Callable[..., Awaitable[T]]]): The function to be executed for the route.
    - **kwargs (Any): Additional keyword arguments.

    Supported **kwargs:
    - response_model (Optional[Type[T]]): The response model type.
    - strict_slashes (bool): Whether to consider trailing slashes.
    - methods (List[str]): HTTP methods supported by the route.
    - name (Optional[str]): The name of the route.

    Returns:
    - Optional[List[Tuple[str, EndpointType]]]: A list containing a tuple of path and endpoint.

    Example:
    >>> re_rule('/user/\\d+', user_handler, methods=['GET', 'PUT'], name='user_route')
    """
    if endpoint is None or not (inspect.iscoroutinefunction(endpoint) or inspect.isasyncgenfunction(endpoint)):
        raise ImproperlyConfigured("Invalid handler function provided for adding a route.")

    response_model = kwargs.pop('response_model', None)
    methods = kwargs.pop('methods', None)

    return (path_regex, methods, endpoint, kwargs.get('strict_slashes', False), response_model, endpoint, kwargs.get('name'))


def websocket(
    path: str,
    endpoint: Optional[Callable[..., Awaitable[T]]] = None,
) -> None:
    """
    Define a WebSocket routing rule.

    Args:
    - path (str): The URL path pattern.
    - endpoint (Optional[Callable[..., Awaitable[T]]]): The function to be executed for the route.
    
    Example:
    >>> websocket('/ws', ws_handler)
    """
    handler = endpoint
    if handler is None:
        raise ValueError("Handler function is required for adding a websocket route.")
    
    if not (inspect.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)):
        raise TypeError("ASGI Websocket can only register asynchronous functions.")
        
    if not path.startswith('/'):
        raise TypeError("Websocket paths must start with '/'.")
        
    return (path, endpoint)