from typing import Any, Awaitable, Callable
from aquilify.wrappers import Request, Response

class CSRFConfigurationError(Exception):
    pass

class CSRFMiddleware:
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        request: Request,
        response: Response
    ) -> Response:
        csrf_token_key = '_csrf_token'
        csrf_view_key = '_csrf_view'

        if request.method in ['GET']:
            if csrf_token_key not in request.context:
                return response
            
            if csrf_view_key not in request.context:
                return response
            
            csrf_token = request.context.get(csrf_token_key)
            csrf_view = request.context.get(csrf_view_key)

            try:
                await self._inject_csrf_token(csrf_view, response, csrf_token)
                response.headers['X-CSRF-TOKEN'] = csrf_token
                return response
            except CSRFConfigurationError as e:
                raise e
        return response

    async def _inject_csrf_token(
        self,
        csrf_view: Callable[..., Awaitable[None]],
        response: Response,
        csrf_token: Any
    ) -> None:
        await csrf_view.inject_csrf_token(response, csrf_token)
