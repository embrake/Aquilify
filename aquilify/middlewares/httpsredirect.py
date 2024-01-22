from __future__ import annotations

from ..types import ASGIApp
from ..wrappers import Request, Response
from ..settings.httpsredirect import HTTPSConfigSettings

_settings = HTTPSConfigSettings().fetch()

class HTTPSRedirectMiddleware:
    def __init__(self) -> None:
        self.strict = _settings.get('strict') or True
        self.allowed_hosts = _settings.get('allowed_host') or []

    async def __call__(self, request: Request, response: Response) -> Response:
        if self._should_redirect(request):
            url = self._construct_https_url(request)
            return Response(status_code=301, headers={'Location': str(url)})
        return response

    def _should_redirect(self, request: Request) -> bool:
        if self.strict:
            return request.scheme == 'http' and self._is_allowed_host(request)
        else:
            return not request.scheme == 'https' and self._is_allowed_host(request)

    def _is_allowed_host(self, request: Request) -> bool:
        return not self.allowed_hosts or request.client.host in self.allowed_hosts

    def _construct_https_url(self, request: Request) -> str:
        return request.url.replace(scheme='https')