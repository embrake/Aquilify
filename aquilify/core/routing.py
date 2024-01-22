# Core routing -> @noql 5381

from typing import (
    Any,
    Awaitable,
    Callable,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

from ._routing import (
    include as include,
    link as link,
    WebsocketRouting,
    HTTPRouting
)

T = TypeVar("T")
EndpointType = Optional[Callable[..., Awaitable[T]]]
RouteReturnType = Optional[List[Tuple[str, EndpointType]]]

def rule(path: str, endpoint: EndpointType = None, **kwargs: Any) -> RouteReturnType:
    """
    Define an HTTP routing rule.

    Args:
    - path (str): The URL path pattern.
    - endpoint (Optional[Callable[..., Awaitable[T]]]): The function to be executed for the route.
    - **kwargs (Any): Additional keyword arguments.

    Supported **kwargs:
    - include.
        Args:
            - args (str): The modules' dotted paths.
            - namespace (str): The application namespace.
    - response_model (Optional[Type[T]]): The response model type.
    - strict_slashes (bool): Whether to consider trailing slashes.
    - methods (List[str]): HTTP methods supported by the route.
    - name (Optional[str]): The name of the route.

    Returns:
    - Optional[List[Tuple[str, EndpointType]]]: A list containing a tuple of path and endpoint.

    Example:
    >>> rule('/home', home_handler, include=True, methods=['GET', 'POST'], name='home_route')
    """
    return HTTPRouting.rule(path, endpoint, **kwargs)

def re_rule(path_regex: str, endpoint: EndpointType = None, **kwargs: Any) -> RouteReturnType:
    """
    Define a regex-based HTTP routing rule.

    Args:
    - path_regex (str): The regex pattern for the URL path.
    - endpoint (Optional[Callable[..., Awaitable[T]]]): The function to be executed for the route.
    - **kwargs (Any): Additional keyword arguments.

    Supported **kwargs:
    - include.
        Args:
            - args (str): The modules' dotted paths.
            - namespace (str): The application namespace.
    - response_model (Optional[Type[T]]): The response model type.
    - strict_slashes (bool): Whether to consider trailing slashes.
    - methods (List[str]): HTTP methods supported by the route.
    - name (Optional[str]): The name of the route.

    Returns:
    - Optional[List[Tuple[str, EndpointType]]]: A list containing a tuple of path and endpoint.

    Example:
    >>> re_rule('/user/\\d+', user_handler, include=True, methods=['GET', 'PUT'], name='user_route')
    """
    return HTTPRouting.re_rule(path_regex, endpoint, **kwargs)

def rule_all(
    path: str,
    endpoint: Callable[..., Awaitable[T]],
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
    return HTTPRouting.rule_all(path, response_model, endpoint, strict_slashes, name)

def websocket(path: str, endpoint: EndpointType = None, **kwargs: Any) -> None:
    """
    Define a WebSocket routing rule.

    Args:
    - path (str): The URL path pattern.
    - endpoint (Optional[Callable[..., Awaitable[T]]]): The function to be executed for the route.
    - **kwargs (Any): Additional keyword arguments.

    Supported **kwargs:
    - include.
        Args:
            - args (str): The modules' dotted paths.
            - namespace (str): The application namespace.

    Example:
    >>> websocket('/ws', ws_handler, include=True)
    """
    return WebsocketRouting.websocket(path, endpoint, **kwargs)

__all__ = [
    "rule",
    "websocket",
    "rule_all",
    "include",
    "link",
    "re_rule"
]