from typing import Optional, Union, Callable
from datetime import datetime
from ..exception.base import GatewayTimeout
from ..wrappers import Request, Response

class TimeoutMiddleware:
    def __init__(
        self,
        timeout_seconds: Optional[Union[int, float]] = 10,
        timeout_response: Optional[Union[str, Callable[..., Response]]] = "Gateway Timeout"
    ):
        self.timeout_seconds = timeout_seconds
        self.timeout_response = timeout_response

    async def __call__(self, request: Request, response: Callable[..., Response]):
        start_time = datetime.now()

        elapsed_time = (datetime.now() - start_time).total_seconds()
        if self.timeout_seconds and elapsed_time < self.timeout_seconds:
            return self._handle_timeout()

        return response

    def _handle_timeout(self) -> Response:
        if isinstance(self.timeout_response, str):
            return GatewayTimeout(self.timeout_response)
        elif callable(self.timeout_response):
            return self.timeout_response()
        else:
            raise ValueError("Invalid timeout_response format. Provide a string message or a callable.")
