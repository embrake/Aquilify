from urllib.parse import urljoin, urlencode

class TemplateURLBuilder:
    def __init__(self):
        self.endpoints = {
            'static': self._build_static_url,
            'redirect': self._build_redirect_url
        }

    def build_url(self, endpoint: str, **values) -> str:
        builder_func = self.endpoints.get(endpoint)
        if builder_func is None:
            raise ValueError(f"Invalid endpoint '{endpoint}' provided")
        return builder_func(**values)

    def _build_static_url(self, **values) -> str:
        filename = values.get('filename')
        if filename is None:
            raise ValueError("Static filename not provided")
        return f'/static/{filename}'

    def _build_redirect_url(self, **values) -> str:
        location = values.get('location')
        if location is None:
            raise ValueError("Redirect location not provided")

        args = values.get('args', {})
        if args:
            location = urljoin(location, f'?{urlencode(args)}')
        return location

    async def __call__(self, context, request):
        context['build_url'] = self.build_url
        return context
