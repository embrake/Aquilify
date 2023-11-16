from __future__ import annotations

import traceback
import html
import typing
from typing import Callable, Type

if typing.TYPE_CHECKING:
    from ..wrappers import Response
from .content import exceptions

ExceptionHandlers = dict[Type[Exception], Callable]

exception_handlers: ExceptionHandlers = {}

def add_exception_handler(exception_cls: Type[Exception], handler: Callable):
    exception_handlers[exception_cls] = handler

async def default_exception_handler(error_message: str, traceback_info: str) -> Response:
    from ..wrappers import Response
    try:
        formatted_traceback = "<br>".join(html.escape(line) for line in traceback_info.splitlines())
        error_type = traceback_info.splitlines()[-1].split(":")[0].strip()

        traceback_lines = traceback_info.splitlines()
        underlined_lines = 'No critical exception found by the handler!'
        for i, line in enumerate(traceback_lines):
            if "^" in line:
                underlined_line = traceback_lines[i - 1]
                underlined_lines = str(underlined_line)

        file_and_line = ""
        for line in traceback_lines:
            if "File " in line:
                file_and_line = line.strip()

        content = exceptions(error_message, formatted_traceback, underlined_lines, error_type, file_and_line)
        return Response(content, content_type='text/html', status_code=500)
    except Exception as e:
        error_message = f"Error in default exception handling: {str(e)}"
        return Response(content=error_message, content_type='text/plain', status_code=500)

async def handle_exception(exception: Exception) -> Response:
    try:
        traceback_info = traceback.format_exc()
        error_message = f"{str(exception)}"

        handler = exception_handlers.get(type(exception), default_exception_handler)
        return await handler(error_message, traceback_info)
    except Exception as e:
        error_message = f"{str(e)}"
        traceback_info = traceback.format_exc()
        return await default_exception_handler(error_message, traceback_info)
