import typing

if typing.TYPE_CHECKING:
    from .wrappers import Request
    from .wrappers import Response
    from .wrappers import WebSocket
    
T = typing.TypeVar("T")

AppType = typing.TypeVar("AppType")

Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]

Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]

ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]

StatelessLifespan = typing.Callable[[AppType], typing.AsyncContextManager[None]]
StatefulLifespan = typing.Callable[
    [AppType], typing.AsyncContextManager[typing.Mapping[str, typing.Any]]
]
Lifespan = typing.Union[StatelessLifespan[AppType], StatefulLifespan[AppType]]

HTTPExceptionHandler = typing.Callable[
    ["Request", Exception], typing.Union["Response", typing.Awaitable["Response"]]
]
WebSocketExceptionHandler = typing.Callable[
    ["WebSocket", Exception], typing.Awaitable[None]
]
ExceptionHandler = typing.Union[HTTPExceptionHandler, WebSocketExceptionHandler]

RouteInfo = typing.Tuple[
    str, typing.List[str], typing.Callable[..., typing.Awaitable[T]], typing.List[str], typing.Pattern, typing.Type[T], str, typing.Dict[str, typing.Any]
]
Routes = typing.List[RouteInfo]
WebSocketRoute = typing.Tuple[str, typing.Callable[..., typing.Awaitable[T]]]
WebSocketRoutes = typing.List[WebSocketRoute]