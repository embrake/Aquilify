from typing import Awaitable, List, Optional
from ..wrappers import Request, Response
from ..exception.base import Forbidden
from ..responses import RedirectResponse

from ..settings.trustedhost import TrustedHostConfigSettings

_settings = TrustedHostConfigSettings().fetch()

class TrustedhostMiddleware:
    def __init__(
        self
    ) -> None:
        self.allowed_hosts: List[str] = _settings.get('allowed_hosts') or ["*"]
        self.allow_subdomains: bool = _settings.get('allow_subdomains') or True
        self.redirect_on_fail: bool = _settings.get("redirect_on_fail") or False
        self.redirect_url: Optional[str] = _settings.get('redirect_url') or None
        self.enforce_https: bool = _settings.get('enforce_https') or False
        self.www_redirect: bool = _settings.get('www_redirect') or False

    async def __call__(
        self, request: Request, response: Response
    ) -> Awaitable[Response]:
        try:
            host = request.host
            if not host:
                return await self._handle_fail_response()
            
            if self.www_redirect and host.startswith("www."):
                return self._redirect_to_non_www(request, response)
                
            if self._is_host_allowed(host):
                if self.enforce_https and not request.scheme.startswith("https"):
                    return await self._redirect_to_https(request, response)
            else:
                return await self._handle_fail_response()
                
            return response

        except Exception as e:
            raise

    def _is_host_allowed(self, host: str) -> bool:
        if "*" in self.allowed_hosts:
            return True
        elif host in self.allowed_hosts:
            return True
        elif self.allow_subdomains:
            for allowed_host in self.allowed_hosts:
                if host.endswith("." + allowed_host):
                    return True
        return False

    async def _redirect_to_https(
        self, request: Request, response: Response
    ) -> Response:
        redirect_url = f"https://{request.headers['host']}{request.url.path}"
        if request.url.query:
            redirect_url += f"?{request.url.query}"
        response = RedirectResponse(redirect_url, 301)
        return response
    
    async def _redirect_to_non_www(
        self, request: Request, response: Response
    ) -> Response:
        redirect_url = f"{request.scheme}://{request.headers['host'].replace('www.', '')}{request.url.path}"
        if request.url.query:
            redirect_url += f"?{request.url.query}"
        response = RedirectResponse(redirect_url, 301)
        return response

    async def _handle_fail_response(self) -> Response:
        response = Forbidden("Host not allowed")
        if not response:
            if self.redirect_on_fail and self.redirect_url:
                response = RedirectResponse(self.redirect_url, 307)
            return response
        return response
