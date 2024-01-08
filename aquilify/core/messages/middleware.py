from typing import Any, Optional
from aquilify.settings import settings
from .storage import default_storage
from aquilify.wrappers import Request, Response

class MessageBeforeStage:
    """
    Middleware class for managing messages before request processing in the Aquilify ASGI framework.

    This middleware assigns message storage to the incoming request object.
    """

    async def __call__(self, request: Request) -> Any:
        """
        Assigns message storage to the incoming request object.

        Args:
        - request (Request): The incoming ASGI HTTP request.

        Returns:
        - Any: The assigned message storage.
        """
        message_storage: Any = default_storage(request)
        request._messages = message_storage
        return message_storage


class MessageMiddleware:
    """
    Middleware class for managing messages during request-response cycle in the Aquilify ASGI framework.

    This middleware updates the response with any stored messages from the request object.
    """

    async def __call__(self, request: Request, response: Response) -> Response:
        """
        Updates the response with any stored messages from the request object.

        Args:
        - request (Request): The incoming ASGI HTTP request.
        - response (Response): The outgoing ASGI HTTP response.

        Returns:
        - Response: The updated ASGI HTTP response.
        """
        if hasattr(request, "_messages"):
            stored_messages: Optional[Any] = request._messages.update(response)
            if stored_messages and settings.DEBUG:
                raise ValueError("Some temporary messages couldn't be stored.")
        return response
