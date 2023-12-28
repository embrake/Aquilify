from urllib.parse import urlencode
from ...settings import settings
from typing import Dict, Any, Callable, Union

from ...security.crypter import safe_join

class EndpointNotFoundError(ValueError):
    pass

class MissingParameterError(ValueError):
    pass

class URLContextProcessor:
    def __init__(self):
        self.ENDPOINTS: Dict[str, Callable[..., str]] = {
            'static': URLContextProcessor._build_static_url,
            'redirect': URLContextProcessor._build_redirect_url,
            'media': URLContextProcessor._build_media_url
        }

    def build_url(self, endpoint: str, **values: Any) -> str:
        builder_func: Callable[..., str] = self.ENDPOINTS.get(endpoint)
        if builder_func is None:
            raise EndpointNotFoundError(f"Endpoint '{endpoint}' not found")

        return builder_func(self, **values)

    @staticmethod
    def _build_static_url(self, **values: Any) -> str:
        filename: Union[str, None] = values.get('filename')
        if not filename:
            raise MissingParameterError("Static filename not provided")
        return safe_join(settings.STATIC_URL, filename)

    @staticmethod
    def _build_media_url(self, **values: Any) -> str:
        filename: Union[str, None] = values.get('filename')
        if not filename:
            raise MissingParameterError("Media filename not provided")
        return safe_join(settings.MEDIA_URL, filename)

    @staticmethod
    def _build_redirect_url(self, **values: Any) -> str:
        location: Union[str, None] = values.get('location')
        if not location:
            raise MissingParameterError("Redirect location not provided")

        args: Dict[str, Any] = values.get('args', {})
        query_string = urlencode(args) if args else ''

        return safe_join(location, query_string)

    async def __call__(self, context: Dict[str, Any], request: Any) -> Dict[str, Any]:
        context['url'] = self.build_url
        return context
