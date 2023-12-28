# @noql -> refer :: 3211

# LICENCED BY AQUILIFY

import jinja2

from .template import Jinja2Templates
from .responses import RedirectResponse

from aquilify.settings import settings

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
    
def render_from_string(
    template_name: str = None,
    template_string: str = None,
    context: dict = None
):
    """
    Render a Jinja2 template from either a template file or a string.

    Args:
        template_name (str, optional): The name of the template file to render.
        template_string (str, optional): The template string to render.
        context (dict, optional): The context data to render the template.

    Returns:
        str: Rendered content as a string.

    Raises:
        ValueError: If neither 'template_name' nor 'template_string' is provided,
                    or if both are provided simultaneously.
        FileNotFoundError: If the template file specified by 'template_name' is not found.
        SyntaxError: If there is a syntax error in the provided template.
        RuntimeError: If an error occurs during template rendering.
    """
    env: jinja2.Environment = jinja2.Environment(loader=jinja2.FileSystemLoader(settings.TEMPLATES[0].get('DIRS')))
    
    if not (template_name or template_string):
        raise ValueError("Either 'template_name' or 'template_string' must be provided.")

    if template_name and template_string:
        raise ValueError("Only one of 'template_name' or 'template_string' should be provided.")

    if context is None:
        context = {}

    try:
        if template_name:
            if not env:
                raise ValueError("Jinja2 Environment 'env' must be provided when using 'template_name'.")
            
            template = env.get_template(template_name)
        else:
            if not template_string:
                raise ValueError("When using 'template_string', the template string must be provided.")

            if not env:
                env = jinja2.Environment()

            template = env.from_string(template_string)

        content = template.render(context)
        return content

    except jinja2.TemplateNotFound as e:
        raise FileNotFoundError(f"Template '{template_name}' not found.") from e
    except jinja2.TemplateSyntaxError as e:
        raise SyntaxError(f"Syntax error in the provided template: {e.message}") from e
    except Exception as e:
        raise RuntimeError(f"An error occurred during template rendering: {e}") from e
    
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