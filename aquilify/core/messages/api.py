from typing import Any, Union, List, Optional

from . import constants
from .storage import default_storage

__all__ = (
    "add_message",
    "get_messages",
    "get_level",
    "set_level",
    "debug",
    "info",
    "success",
    "warning",
    "error",
    "MessageFailure",
)

class MessageFailure(Exception):
    pass

def add_message(request: Any, level: int, message: str, extra_tags: str = "", fail_silently: bool = False) -> None:
    """
    Add a message to the request.

    Args:
        request (Any): Request object.
        level (int): Message level (DEBUG, INFO, SUCCESS, WARNING, ERROR).
        message (str): Message content.
        extra_tags (str, optional): Extra tags for the message.
        fail_silently (bool, optional): If True, failures will not raise an error.

    Raises:
        TypeError: If the argument passed is not a valid request object.
        MessageFailure: If MessageMiddleware is not installed and fail_silently is False.
    """
    try:
        messages = request._messages
    except AttributeError:
        if not hasattr(request, "headers"):
            raise TypeError(
                f"add_message() argument must be a Request object, not '{request.__class__.__name__}'."
            )
        if not fail_silently:
            raise MessageFailure(
                "You cannot add messages without installing "
                "aquilify.core.messages.middleware.MessageMiddleware"
            )
    else:
        messages.add(level, message, extra_tags)

def get_messages(request: Any) -> List[Any]:
    """
    Get messages from the request.

    Args:
        request (Any): Request object.

    Returns:
        List[Any]: List of messages or an empty list if no messages found.
    """
    return getattr(request, "_messages", [])

def get_level(request: Any) -> int:
    """
    Get the current message level from the request.

    Args:
        request (Any): Request object.

    Returns:
        int: Current message level.
    """
    storage = getattr(request, "_messages", default_storage(request))
    return storage.level

def set_level(request: Any, level: int) -> bool:
    """
    Set the message level for the request.

    Args:
        request (Any): Request object.
        level (int): Message level to set.

    Returns:
        bool: True if the message level is set successfully, False otherwise.
    """
    if not hasattr(request, "_messages"):
        return False
    request._messages.level = level
    return True

def debug(request: Any, message: str, extra_tags: str = "", fail_silently: bool = False) -> None:
    """
    Add a debug message to the request.

    Args:
        request (Any): Request object.
        message (str): Debug message content.
        extra_tags (str, optional): Extra tags for the message.
        fail_silently (bool, optional): If True, failures will not raise an error.
    """
    add_message(request, constants.DEBUG, message, extra_tags=extra_tags, fail_silently=fail_silently)

def info(request: Any, message: str, extra_tags: str = "", fail_silently: bool = False) -> None:
    """
    Add an info message to the request.

    Args:
        request (Any): Request object.
        message (str): Info message content.
        extra_tags (str, optional): Extra tags for the message.
        fail_silently (bool, optional): If True, failures will not raise an error.
    """
    add_message(request, constants.INFO, message, extra_tags=extra_tags, fail_silently=fail_silently)

def success(request: Any, message: str, extra_tags: str = "", fail_silently: bool = False) -> None:
    """
    Add a success message to the request.

    Args:
        request (Any): Request object.
        message (str): Success message content.
        extra_tags (str, optional): Extra tags for the message.
        fail_silently (bool, optional): If True, failures will not raise an error.
    """
    add_message(request, constants.SUCCESS, message, extra_tags=extra_tags, fail_silently=fail_silently)

def warning(request: Any, message: str, extra_tags: str = "", fail_silently: bool = False) -> None:
    """
    Add a warning message to the request.

    Args:
        request (Any): Request object.
        message (str): Warning message content.
        extra_tags (str, optional): Extra tags for the message.
        fail_silently (bool, optional): If True, failures will not raise an error.
    """
    add_message(request, constants.WARNING, message, extra_tags=extra_tags, fail_silently=fail_silently)

def error(request: Any, message: str, extra_tags: str = "", fail_silently: bool = False) -> None:
    """
    Add an error message to the request.

    Args:
        request (Any): Request object.
        message (str): Error message content.
        extra_tags (str, optional): Extra tags for the message.
        fail_silently (bool, optional): If True, failures will not raise an error.
    """
    add_message(request, constants.ERROR, message, extra_tags=extra_tags, fail_silently=fail_silently)
