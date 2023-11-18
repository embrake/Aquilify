from typing import Awaitable, List, Optional
from ..wrappers import Request, Response
from ..exception.base import Forbidden
from ..responses import RedirectResponse

class TrustedhostMiddleware:
    def __init__(
        self,
        allowed_hosts: List[str] = ["*"],
        allow_subdomains: bool = True,
        redirect_on_fail: bool = False,
        redirect_url: Optional[str] = None,
        enforce_https: bool = False,
        www_redirect: bool = False,
    ) -> None:
        self.allowed_hosts = allowed_hosts
        self.allow_subdomains = allow_subdomains
        self.redirect_on_fail = redirect_on_fail
        self.redirect_url = redirect_url
        self.enforce_https = enforce_https
        self.www_redirect = www_redirect

    async def __call__(
        self, request: Request, response: Response
    ) -> Awaitable[Response]:
        try:
            host = request.headers.get("host", "")
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
