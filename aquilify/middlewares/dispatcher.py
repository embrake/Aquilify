import logging
from typing import Awaitable, Callable, Dict, Optional, Union
from ..types import ASGIApp, Receive, Scope, Send
from ..responses import JsonResponse

class Dispatcher:
    """
    Dispatches incoming requests to different mounted ASGI apps based on the URL path.

    Usage:
    ```python
    # Create the main application
    main_app = Aquilify()

    # Create instances of the mounted apps
    app1 = Aquilify()
    app2 = Aquilify()

    # Create the Dispatcher instance
    dispatcher = Dispatcher(main_app, {})

    # Map app1 to /app1 and app2 to /app2
    dispatcher.map_url('/app1', app1)
    dispatcher.map_url('/app2', app2)

    # Define error handlers if necessary
    async def error_handler1(scope, receive, send, exc):
        # Custom error handling logic for app1
        pass

    async def error_handler2(scope, receive, send, exc):
        # Custom error handling logic for app2
        pass

    dispatcher.map_url('/app1', app1, error_handler1)
    dispatcher.map_url('/app2', app2, error_handler2)

    # Run the dispatcher
    @app.route("/")
    async def homepage(request):
        return JsonResponse({"message": "Hello, world!"})

    @app.route("/app1")
    async def app1_homepage(request):
        return JSONResponse({"message": "App 1 homepage"})

    @app.route("/app2")
    async def app2_homepage(request):
        return JSONResponse({"message": "App 2 homepage"})
    ```
    """

    def __init__(self, main_app: ASGIApp, mounts: Dict[str, ASGIApp]) -> None:
        """
        Initializes the Dispatcher instance.

        Args:
            main_app (ASGIApp): The main ASGI app to handle the requests.
            mounts (Dict[str, ASGIApp]): A dictionary containing mounted apps.
        
        Usage:
        ```python
            main_app = Aquilify() # create a main app instance

            app2 = Aquilify() #sub app for mounting in main_app

            dispatcher = Dispatcher(main_app, {
                '/app2': app2
            })

        Run:
            $ netix --debug main:dispatcher 
            ---------- or -----------
            $ uvicorn main:dispatcher

        """
        self.main_app: ASGIApp = main_app
        self.mounts: Dict[str, ASGIApp] = mounts
        self.error_handlers: Dict[str, Optional[Callable[..., Awaitable[None]]]] = {
            mount_point: None for mount_point in mounts
        }
        self.logger = logging.getLogger(__name__)

    def map_url(self, mount_point: str, app: ASGIApp, 
                error_handler: Optional[Callable[..., Awaitable[None]]] = None) -> None:
        """
        Maps a URL mount point to a specified ASGI app.

        Args:
            mount_point (str): The URL mount point.
            app (ASGIApp): The ASGI app to mount at the specified point.
            error_handler (Optional[Callable[..., Awaitable[None]]]): Error handler for this mounted app.
        """
        self.mounts[mount_point] = app
        self.error_handlers[mount_point] = error_handler

    def unmap_url(self, mount_point: str) -> None:
        """
        Unmaps a URL mount point, removing the mounted app.

        Args:
            mount_point (str): The URL mount point to unmap.
        """
        if mount_point in self.mounts:
            del self.mounts[mount_point]
            del self.error_handlers[mount_point]

    async def conditional_mount(self, mount_point: str, app: ASGIApp,
                               condition: Union[Callable, Awaitable[bool]], 
                               error_handler: Optional[Callable[..., Awaitable[None]]] = None) -> None:
        """
        Mounts an ASGI app based on a specified condition.

        Args:
            mount_point (str): The URL mount point.
            app (ASGIApp): The ASGI app to mount at the specified point.
            condition (Union[Callable, Awaitable[bool]]): Condition to decide the mounting.
            error_handler (Optional[Callable[..., Awaitable[None]]]): Error handler for this mounted app.
        """
        if callable(condition):
            condition = await condition()
        if condition:
            self.mounts[mount_point] = app
            self.error_handlers[mount_point] = error_handler

    async def dispatch(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Dispatches incoming requests to the appropriate mounted ASGI app.

        Args:
            scope (Scope): The ASGI scope of the request.
            receive (Receive): Callable to receive messages from the client.
            send (Send): Callable to send messages to the client.
        """
        path = scope.get('path', '/')
        for mount_point, mounted_app in self.mounts.items():
            if path == mount_point or path.startswith(mount_point + '/'):
                sub_path = path[len(mount_point):] if path != mount_point else '/'
                scope['path'] = sub_path
                scope['app_mount'] = mount_point
                error_handler = self.error_handlers.get(mount_point)
                try:
                    await mounted_app(scope, receive, send)
                except Exception as e:
                    if error_handler:
                        await error_handler(scope, receive, send, e)
                    else:
                        self.logger.exception(f"An error occurred in the mounted app {mount_point}.")
                        await self.general_error_handler(scope, receive, send, e)
                return
        await self.main_app(scope, receive, send)

    async def general_error_handler(self, scope: Scope, receive: Receive, send: Send, exc: Exception) -> None:
        """
        Handles general errors for unhandled exceptions.

        Args:
            scope (Scope): The ASGI scope of the request.
            receive (Receive): Callable to receive messages from the client.
            send (Send): Callable to send messages to the client.
            exc (Exception): The exception raised.
        """
        error_details = {'error': 'An error occurred', 'details': str(exc)}
        error_resp = JsonResponse(error_details, status_code=500)
        await error_resp(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Calls the dispatcher to handle incoming requests.

        Args:
            scope (Scope): The ASGI scope of the request.
            receive (Receive): Callable to receive messages from the client.
            send (Send): Callable to send messages to the client.
        """
        try:
            await self.dispatch(scope, receive, send)
        except Exception as e:
            await self.general_error_handler(scope, receive, send, e)
