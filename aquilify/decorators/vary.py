from functools import wraps

from aquilify.utils.cache import patch_vary_headers


def vary_on_headers(*headers):
    """
    A view decorator that adds the specified headers to the Vary header of the
    response. Usage:

       @vary_on_headers('Cookie', 'Accept-language')
       async def index(request):
           ...

    Note that the header names are not case-sensitive.
    """

    def decorator(func):

        async def _view_wrapper(request, *args, **kwargs):
            response = await func(request, *args, **kwargs)
            patch_vary_headers(response, headers)
            return response

        return wraps(func)(_view_wrapper)

    return decorator


vary_on_cookie = vary_on_headers("Cookie")
vary_on_cookie.__doc__ = (
    'A view decorator that adds "Cookie" to the Vary header of a response. This '
    "indicates that a page's contents depends on cookies."
)
