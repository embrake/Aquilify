import asyncio
from functools import lru_cache
from urllib.parse import urljoin, urlencode
from markupsafe import Markup
from html import escape

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape, Template, TemplateNotFound
except ImportError:
    Environment, FileSystemLoader, select_autoescape, Template, TemplateNotFound = None, None, None, None, None

from typing import (
    Any,
    Dict,
    Optional,
    Callable,
    List,
    Awaitable
)

from .wrappers import Response, Request
from .exception.__handler import handle_exception

class TemplateResponse:
    def __init__(
        self,
        template_paths: List[str] = ["templates"],
        default_context: Dict[str, Any] = None,
        autoescape: bool = True,
        template_engine: str = "jinja2",
        csrf: Callable[..., Awaitable] = None,
        cache_size: int = 128,
        url_for: Optional[Callable[..., str]] = None,
        flash_config: Optional[Dict[str, Any]] = None,
        context_processors: Optional[Dict[str, Callable[..., Dict[str, Any]]]] = None,
        custom_filters: Optional[Dict[str, Callable[..., Any]]] = None,
        custom_globals: Optional[Dict[str, Any]] = None,
        enable_template_cache: bool = True,
        custom_extensions: Optional[List[str]] = None,
    ):
        self._check_jinja2_library()
        
        self.template_paths = template_paths
        self.default_context = default_context or {}
        self.autoescape = autoescape
        self.template_engine = template_engine.lower()
        self.cache_size = cache_size
        self.context_processors = context_processors or {}
        self.flash_config = flash_config or {'with_category': False, 'category_filter': ()}
        self.custom_filters = custom_filters or {}
        self.custom_globals = custom_globals or {}
        self.enable_template_cache = enable_template_cache
        self.custom_extensions = custom_extensions or []
        self.csrf = csrf

        if self.template_engine not in ["jinja2"]:
            raise ValueError("Unsupported template engine. Currently, only 'jinja2' is supported.")

        self.env = self._create_environment()
        self.url_for = url_for or self._default_url_for

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
            raise FileNotFoundError(f"Template not found: {e.name}") from e

    def _inject_default_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        injected_context = self.default_context.copy()
        injected_context.update(context)
        return injected_context

    async def _add_url_generation(self, request: Request, context: Dict[str, Any], csrf_protect) -> Dict[str, Any]:
        if self.csrf is not None:
            context['build_url'] = self.url_for
            context['flashes'] = await self._get_flashes(request)
            context['csrf_protect'] = csrf_protect
            return context
        context['build_url'] = self.url_for
        context['flashes'] = await self._get_flashes(request)
        return context

    def _run_context_processors(self, context: Dict[str, Any]) -> Dict[str, Any]:
        for name, processor in self.context_processors.items():
            context[name] = processor(context)
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

    def _default_url_for(self, endpoint: str, **values) -> str:
        if endpoint == 'static':
            filename = values.get('filename', None)
            if filename:
                return f'/static/{filename}'
            else:
                raise ValueError("Static filename not provided")

        elif endpoint == 'redirect':
            location = values.get('location', None)
            if location:
                args = values.get('args', {})
                if args:
                    location = urljoin(location, f'?{urlencode(args)}')
                return location
            else:
                raise ValueError("Redirect location not provided")

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

        template = await asyncio.to_thread(self._get_template, template_name)
        context = self._inject_default_context(context)
        context = await self._add_url_generation(request, context, csrf_protect)
        context = self._run_context_processors(context)

        try:
            if inherit:
                inherited_template = await asyncio.to_thread(self._get_template, inherit)
                content = await asyncio.to_thread(template.render, content=inherited_template.render(**context), **context)
            else:
                content = await asyncio.to_thread(template.render, **context)
        except Exception as e:
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
