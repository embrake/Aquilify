import asyncio
from functools import lru_cache
from markupsafe import Markup
from html import escape

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape, Template, TemplateNotFound, TemplateError
except ImportError:
    Environment, FileSystemLoader, select_autoescape, Template, TemplateNotFound, TemplateError = None, None, None, None, None, None

from typing import (
    Any,
    Dict,
    Optional,
    Callable,
    List
)

from ..wrappers import Response, Request
from ..exception.__handler import handle_exception

from ..settings.templates import TemplateConfigSettings

try:
    _config_settings = TemplateConfigSettings()
    _config_settings.fetch()
    _settings = _config_settings.template_data[0]
except Exception as e:
    raise Exception("Template settings not found in settings.py, configure it before you use.")


class TemplateResponse:
    def __init__(
        self
    ):
        self._check_jinja2_library()
        
        self.template_paths = _settings.get('dirs') or ["templates"]
        self.default_context = None or {}
        self.autoescape = _settings['options'].get('autoscape') or True
        self.template_engine = _settings.get('backend').lower()
        self.cache_size = _settings['options'].get('cache_size') or True
        self.context_processors = _settings['options'].get('context_processors') or []
        self.flash_config = {'with_category': False, 'category_filter': ()}
        self.custom_filters = _settings['options'].get('filters') or {}
        self.custom_globals = _settings['options'].get('globals') or {}
        self.enable_template_cache = _settings['options'].get('enable_template_cache') or True
        self.custom_extensions = _settings['options'].get('extensions') or []
        self.csrf = _settings.get('csrf') or None

        if self.template_engine not in ["jinja2"]:
            raise ValueError("Unsupported template engine. Currently, only 'jinja2' is supported.")

        self.env: Environment = self._create_environment()

    def _check_jinja2_library(self):
        if Environment is None:
            raise ImportError("Jinja2 library is not installed. Please install it using 'pip install jinja2' or 'pip install aquilify[jinja2]'.")

    def _create_environment(self) -> Environment:
        if self.template_engine == "jinja2":
            loader = FileSystemLoader(self.template_paths)
            environment = Environment(
                loader=loader,
                autoescape=select_autoescape(['html', 'xml']) if self.autoescape else False,
                cache_size=self.cache_size if self.enable_template_cache else 0,
     
                extensions=self.custom_extensions,
            )
            environment.filters.update(self.custom_filters)
            environment.globals.update(self.custom_globals)
            return environment

    @lru_cache(maxsize=None)
    def _get_template(self, template_name: str) -> Template:
        try:
            return self.env.get_template(template_name)
        except TemplateNotFound as e:
            error_message = f"Template not found: {e.name}"
            raise FileNotFoundError(error_message) from e
        except TemplateError as e:
            error_message = f"Error loading template '{template_name}': {str(e)}"
            raise FileNotFoundError(error_message) from e

    def _inject_default_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        injected_context = self.default_context.copy()
        injected_context.update(context)
        return injected_context

    async def _add_url_generation(self, request: Request, context: Dict[str, Any], csrf_protect) -> Dict[str, Any]:
        if self.csrf is not None:
            context['flashes'] = await self._get_flashes(request)
            context['csrf_protect'] = csrf_protect
            return context
        context['flashes'] = await self._get_flashes(request)
        return context

    def _get_processor_name(self, processor) -> str:
        if hasattr(processor, '__call__'):
            if isinstance(processor, type):
                return f"Callable class '{processor.__name__}'"
            else:
                return f"Instance of callable class '{processor.__class__.__name__}'"
        else:
            return f"Function '{processor.__name__}'"

    def _run_context_processors(self, context: Dict[str, Any], request: Request) -> Dict[str, Any]:
        for processor in self.context_processors:
            processor_name = self._get_processor_name(processor)

            processed_context = processor(context, request)
            if not isinstance(processed_context, dict):
                raise ValueError(f"{processor_name} must return a dictionary.")
            context = processed_context
        return context
    
    async def _clear_flashes(self, request: Request):
        request.context['flash'] = {}

    async def flash(self, request: Request, message, category='message'):
        context = request.context.setdefault('flash', {})
        context.setdefault(category, []).append(message)

    async def _get_flashes(self, request: Request) -> Dict[str, List[str]]:
        with_category = self.flash_config.get('with_category', False)
        category_filter = self.flash_config.get('category_filter', ())

        flashes = request.context.pop('flash', {})

        if not with_category:
            return flashes

        if category_filter:
            filtered_flashes = {category: messages for category, messages in flashes.items() if category in category_filter}
            return filtered_flashes
        else:
            return flashes
            
    async def render(
        self,
        request: Request,
        template_name: str,
        context: Dict[str, Any] = None,
        status_code: int = 200,
        headers: Dict[str, str] = None,
        inherit: Optional[str] = None,
    ) -> Response:
        
        if context is None:
            context = {}
        
        token = None
        if self.csrf is not None:
            token = await self.csrf.generate_csrf_token(request.remote_addr)
            token_name = self.csrf.csrf_token_key
            csrf_protect = lambda: Markup(f'<input name="{token_name}" type="hidden" value="{escape(token)}"></input>') if token else ''

        csrf_protect = None
        
        template = await asyncio.to_thread(self._get_template, template_name)
        context = self._inject_default_context(context)
        context = await self._add_url_generation(request, context, csrf_protect)
        context = self._run_context_processors(context, request)

        try:
            if inherit:
                inherited_template = await asyncio.to_thread(self._get_template, inherit)
                content = await asyncio.to_thread(template.render, content=inherited_template.render(**context), **context)
            else:
                content = await asyncio.to_thread(template.render, **context)
        except TemplateNotFound as e:
            error_message = f"Template not found: {e.name}"
            raise FileNotFoundError(error_message) from e
        except TemplateError as e:
            await handle_exception(e)

        response = Response(
            content,
            content_type='text/html',
            status_code=status_code,
            headers=headers
        )
        if self.csrf is not None:
            await self.csrf.inject_csrf_token(response, token)
            response.headers['X-CSRF-TOKEN'] = token
        return response

    async def __call__(
        self,
        request: Request,
        template_name: str,
        context: Dict[str, Any] = None,
        status_code: int = 200,
        headers: Dict[str, str] = None,
        inherit: Optional[str] = None,
    ) -> Response:
        
        if context is None:
            context = {}
        
        token = None
        if self.csrf is not None:
            token = await self.csrf.generate_csrf_token(request.remote_addr)
            token_name = self.csrf.csrf_token_key
            csrf_protect = lambda: Markup(f'<input name="{token_name}" type="hidden" value="{escape(token)}"></input>') if token else ''

        else:
            csrf_protect = None
        
        template = await asyncio.to_thread(self._get_template, template_name)
        context = self._inject_default_context(context)
        context = await self._add_url_generation(request, context, csrf_protect)
        context = self._run_context_processors(context, request)

        try:
            if inherit:
                inherited_template = await asyncio.to_thread(self._get_template, inherit)
                content = await asyncio.to_thread(template.render, content=inherited_template.render(**context), **context)
            else:
                content = await asyncio.to_thread(template.render, **context)
        except TemplateNotFound as e:
            error_message = f"Template not found: {e.name}"
            raise FileNotFoundError(error_message) from e
        except TemplateError as e:
            await handle_exception(e)

        response = Response(
            content,
            content_type='text/html',
            status_code=status_code,
            headers=headers
        )
        if self.csrf is not None:
            await self.csrf.inject_csrf_token(response, token)
            response.headers['X-CSRF-TOKEN'] = token
        return response