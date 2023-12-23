# @noql -> refer :: 3211

# LICENCED BY AQUILIFY

from .template import Jinja2Templates
from .responses import RedirectResponse

from typing import Optional, Dict, Any

async def render(
    request,
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None,
    content_type: Optional[str] = None
) -> Jinja2Templates:
    """
    Renders a template using Jinja2Templates and returns a Response object.

    Example:
       ```python
       # save this as views.py
       
       from aquilify.shortcuts import render

       async def homeview(request):
           await render(request, 'index.html', {'message': 'Welcome to Aquiliy})

           
       ```

    Args:
        request (Request): The incoming Aquilify Request object.
        template_name (str): The name of the template file to render.
        context (Optional[Dict[str, Any]]): Context data to be passed to the template (default: None).
        status_code (int): The HTTP status code for the response (default: 200).
        headers (Optional[Dict[str, str]]): Additional HTTP headers to include (default: None).
        content_type (Optional[str]): The content type of the response (default: None).

    Returns:
        Response: A Response object with the rendered template.

    Raises:
        Exception: Any exception that occurs during template rendering.

    
    """
    templates = Jinja2Templates()
    try:
        return await templates.TemplateResponse(
            template_name,
            {"request": request, **(context or {})},
            status_code=status_code,
            headers=headers,
            content_type=content_type
        )
    except Exception as e:
        raise e
    
async def redirect(
    url: Optional[str] = None,
    status_code: int = 307,
    headers: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, str]] = None,
    anchor: Optional[str] = None,
    delay: int = 0,
    content: Optional[str] = None,
    secure_headers: bool = False
) -> RedirectResponse:
    """
    Constructs a RedirectResponse object to redirect to the provided URL with specified parameters.

    Args:
        url (Optional[str]): The URL to redirect to.
        status_code (int): The HTTP status code for the redirection (default: 307).
        headers (Optional[Dict[str, str]]): Additional HTTP headers to include.
        query_params (Optional[Dict[str, str]]): Query parameters to append to the URL.
        anchor (Optional[str]): The anchor to append to the URL.
        delay (int): Delay in seconds before the redirection (default: 0).
        content (Optional[str]): Content for the redirection response body.
        secure_headers (bool): Flag to add security headers (default: False).

    Returns:
        RedirectResponse: RedirectResponse object.
    """
    return RedirectResponse(
        url,
        status_code=status_code,
        headers=headers,
        query_params=query_params,
        anchor=anchor,
        delay=delay,
        content=content,
        secure_headers=secure_headers
    )