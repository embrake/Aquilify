from ..wrappers import Request, Response
from ..settings import settings

def write_hsts_header_value(max_age: int, include_subdomains: bool) -> str:
    value = f"max-age={max_age};"

    if include_subdomains:
        value = value + " includeSubDomains;"

    return value


class HSTSMiddleware:
    """
    Middleware configuring "Strict-Transport-Security" header on responses.
    By default, it uses "max-age=31536000; includeSubDomains;".
    """

    def __init__(
        self,
        max_age: int = getattr(settings, 'HSTS_MAX_AGE', 31536000),
        include_subdomains: bool = getattr(settings, 'HSTS_INCLUDE_SUBDOMAINS', True),
    ) -> None:
        self._value = write_hsts_header_value(max_age, include_subdomains)

    async def __call__(self, request: Request, response: Response):
        response.headers["Strict-Transport-Security"] = self._value
        return response
