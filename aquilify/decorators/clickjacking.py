from functools import wraps
from typing import Callable
from enum import Enum
from ..wrappers import Response, Request

class XFrameOptions(Enum):
    DENY = "DENY"
    SAMEORIGIN = "SAMEORIGIN"
    ALLOWALL = "ALLOWALL"

def xframe_options_exempt(handler: Callable[..., Response]) -> Callable[..., Response]:
    @wraps(handler)
    async def wrapper(*args, **kwargs) -> Response:
        response = await handler(*args, **kwargs)
        response.headers['X-Frame-Options'] = XFrameOptions.ALLOWALL.value
        return response
    return wrapper

def xframe_options(option: XFrameOptions) -> Callable:
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        async def wrapped_view(request: Request, *args, **kwargs) -> Response:
            try:
                response = await view_func(request, *args, **kwargs)
                response.headers["X-Frame-Options"] = option.value
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                response = Response(error_message, status_code=500)
            return response
        return wrapped_view
    return decorator
