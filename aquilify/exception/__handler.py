from __future__ import annotations

import sys
import traceback
import html
import typing
from typing import Callable, Type

if typing.TYPE_CHECKING:
    from ..wrappers import Response, Request

from .content import exceptions
from ._sys_info import get_sys_info

ExceptionHandlers = dict[Type[Exception], Callable]
exception_handlers: ExceptionHandlers = {}


def add_exception_handler(exception_cls: Type[Exception], handler: Callable):
    exception_handlers[exception_cls] = handler


def get_code_lines():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback_info = traceback.extract_tb(exc_traceback)
    relevant_code = []

    for filename, line_num, func_name, code_text in traceback_info:
        code_lines = []
        try:
            with open(filename) as file:
                code_lines = file.readlines()
        except FileNotFoundError as e:
            relevant_code.append(f"File '{filename}' not found: {str(e)}")
        except Exception as e:
            relevant_code.append(f"Error reading file '{filename}': {str(e)}")

        start_line = max(0, line_num - 5)
        end_line = min(len(code_lines), line_num + 5)

        relevant_code.append(f"In function '{func_name}' (File: '{filename}', Line: {line_num}):\n")

        max_digits = len(str(end_line))
        for i, line in enumerate(code_lines[start_line:end_line], start=start_line + 1):
            line = line.rstrip()
            marker = " >>> " if i == line_num else "     "
            line_num_str = str(i).rjust(max_digits)
            formatted_line = f"{marker}{line_num_str} | {line}"
            if i == line_num:
                formatted_line += f"   <-- Caused Exception: {exc_type.__name__}: {exc_value}"
            relevant_code.append(formatted_line)

        relevant_code.append('\n' + '-' * 60 + '\n')

        try:
            if hasattr(exc_value, 'args') and exc_value.args:
                relevant_code.append(f"Exception Arguments: {exc_value.args}\n")
        except Exception as e:
            relevant_code.append(f"Error retrieving exception arguments: {str(e)}\n")

        try:
            locals_dict = code_text and eval(code_text).f_locals
            if locals_dict:
                relevant_code.append("Local Variables:\n")
                for var_name, var_value in locals_dict.items():
                    if not var_name.startswith("__"):
                        relevant_code.append(f"{var_name}: {var_value}\n")
        except Exception as e:
            relevant_code.append(f"Error retrieving local variables: {str(e)}\n")

        try:
            globals_dict = code_text and eval(code_text).f_globals
            if globals_dict:
                relevant_code.append("Global Variables:\n")
                for var_name, var_value in globals_dict.items():
                    if not var_name.startswith("__"):
                        relevant_code.append(f"{var_name}: {var_value}\n")
        except Exception as e:
            relevant_code.append(f"Error retrieving global variables: {str(e)}\n")

    return '\n'.join(relevant_code)


async def default_exception_handler(error_message: str, traceback_info: str, code_lines, req_data = None) -> Response:
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

        content = exceptions(error_message, formatted_traceback, underlined_lines, error_type, file_and_line,
                             code_lines, get_sys_info(), req_data)
        return Response(content, content_type='text/html', status_code=500)
    except Exception as e:
        error_message = f"Error in default exception handling: {str(e)}"
        return Response(content=error_message, content_type='text/plain', status_code=500)

def request_data(request: Request = None):
    if request is None:
        pass
    req_data = {
        "Host": request.host,
        "Port": request.url.port,
        "Client-IP": request.remote_addr,
        "Path": request.path,
        "Method": request.method,
        "User-Agent-String": request.user_agent,
        "Browser": request.user_agent.browser,
        "Timezone": request.user_agent.timezone,
        "Language": request.user_agent.language,
        "Platform": request.user_agent.platform,
        "Query-Params": request.query_params,
        "Base-Url": request.base_url,
        "Origin": request.origin,
        "Scheme": request.scheme,
        "Referer": request.referer,
        "Path-Params": request.path_param,
        "Session": request.session,
        "Cookie": request.cookies
    }
    return req_data

async def handle_exception(exception: Exception, request: Request = None) -> Response:
    try:
        traceback_info = traceback.format_exc()
        error_message = f"{str(exception)}"
        handler = exception_handlers.get(type(exception), default_exception_handler)
        req_data = request_data(request)
        return await handler(error_message, traceback_info, get_code_lines(), req_data)
    except Exception as e:
        error_message = f"{str(e)}"
        traceback_info = traceback.format_exc()
        return await default_exception_handler(error_message, traceback_info, get_code_lines())
