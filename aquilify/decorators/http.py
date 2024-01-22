from functools import wraps
from typing import Union, Callable, Awaitable, List, Dict

from aquilify.exception.base import MethodNotAllowed
from aquilify.wrappers import Request
from aquilify.responses import JsonResponse
from aquilify.core.status import HTTP_405_METHOD_NOT_ALLOWED

import asyncio

ErrorHandler = Union[Callable[[Request], str], Awaitable[Callable[[Request], str]]]
AllowedMethods = Union[List[str], Dict[str, List[str]]]

def require_http_method(methods: AllowedMethods, error_handler: ErrorHandler = None):
    def decorator(func: Callable[..., Awaitable[JsonResponse]]):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs) -> JsonResponse:
            allowed_methods = []
            if isinstance(methods, dict):
                allowed_methods = methods.get(request.url.path, [])
            elif isinstance(methods, list):
                allowed_methods = methods
            else:
                raise ValueError("Invalid 'methods' argument provided.")

            if request.method not in allowed_methods:
                error_message = "Method Not Allowed"
                if error_handler:
                    if asyncio.iscoroutinefunction(error_handler):
                        error_message = await error_handler(request)
                    else:
                        error_message = error_handler(request)
                allowed_methods_str = ', '.join(allowed_methods)
                raise MethodNotAllowed(
                    f"{error_message}. Allowed methods: {allowed_methods_str}"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator