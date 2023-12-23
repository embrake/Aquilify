from typing import Any, Dict, Optional, Callable
from markupsafe import Markup
from html import escape
from ...settings.xsrf_view import XSRFConfigSettings

try:
    _config_settings = XSRFConfigSettings()
    _config_settings.fetch()
    _settings = _config_settings.template_data[0]
except Exception as e:
    raise Exception("Template settings not found in settings.py, configure it before you use.")

class XSRFContextView:
    def __init__(self) -> None:
        self.csrf: Optional[Any] = _settings.get('csrf')

    async def __call__(self, context: Dict[str, Any], request: Any) -> Dict[str, Any]:
        token: Optional[str] = await self._get_csrf_token(request) if self.csrf else None
        csrf_protect: Callable[[], Markup] = self._get_csrf_protect(token)
        context['csrf_protect'] = csrf_protect
        request.context['_csrf_token'] = token
        request.context['_csrf_view'] = self.csrf
        return context

    async def _get_csrf_token(self, request: Any) -> Optional[str]:
        if self.csrf:
            return await self.csrf.generate_csrf_token(request.remote_addr)
        return None

    def _get_csrf_protect(self, token: Optional[str]) -> Callable[[], Markup]:
        if token:
            token_name: str = self.csrf.csrf_token_key
            return lambda: Markup(f'<input name="{token_name}" type="hidden" value="{escape(token)}"></input>')
        return lambda: Markup('')
