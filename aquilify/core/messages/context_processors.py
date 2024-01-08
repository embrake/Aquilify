from typing import Any, Dict
from .api import get_messages
from .constants import DEFAULT_LEVELS

class Messages:
    """
    Middleware class responsible for handling messages in the application context.
    """

    async def __call__(self, context: Dict[str, Any], request) -> Dict[str, Any]:
        """
        Assigns messages and default levels to the context based on the incoming request.

        Args:
        - context (Dict[str, Any]): The application context.
        - request (Request): The incoming request.

        Returns:
        - Dict[str, Any]: The updated application context containing messages and default levels.
        """
        context['messages'] = get_messages(request)
        context['DEFAULT_MESSAGE_LEVELS'] = DEFAULT_LEVELS
        
        return context
