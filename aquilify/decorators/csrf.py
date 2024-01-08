from functools import wraps
from ..wrappers import (
    Request,
    Response
)
from ..exception.base import TooManyRequests, Forbidden
from ..security.csrf import CSRF, CSRFTokenError

_csrf = CSRF()

def csrf_protect(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        try:
            if request.method in _csrf.protected_methods:
                try:
                    if not await _csrf.validate_csrf_token(request):
                        return Forbidden('CSRF Token Validation Failed')
                except CSRFTokenError:
                    return Forbidden('CSRF Token Validation Failed')

                client_ip = _csrf.get_client_ip(request)

                if _csrf.rate_limiter and not _csrf.rate_limiter.check(client_ip):
                    _csrf.logger.warning(f"Rate limit exceeded for IP {client_ip}")
                    return TooManyRequests("Rate limit exceeded")

                if _csrf.token_refresh_interval and await _csrf.should_refresh_csrf_token(request.cookies.get(_csrf.csrf_token_key)):
                    new_csrf_token = await _csrf.generate_csrf_token(client_ip)
                    return await _csrf.inject_csrf_token(Response(), new_csrf_token)

            return await func(request, *args, **kwargs)
        except Exception as e:
            raise e
    return wrapper