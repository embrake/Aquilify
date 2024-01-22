from aquilify.wrappers import Response, Request
from aquilify.utils.cache import cc_delim_re, get_conditional_response, set_response_etag
from aquilify.utils.http import parse_http_date_safe

class ConditionalGetMiddleware:
    def __init__(self) -> None:
        pass
    
    def needs_etag(self, response):
        cache_control_headers = cc_delim_re.split(response.headers.get("Cache-Control", ""))
        return all(header.lower() != "no-store" for header in cache_control_headers)
    
    async def __call__(self, request: Request, response: Response):

        if request.method != "GET":
            return response

        if self.needs_etag(response) and not response.headers.get("ETag"):
            set_response_etag(response)

        etag = response.headers.get("ETag")
        last_modified = response.headers.get("Last-Modified")
        last_modified = last_modified and parse_http_date_safe(last_modified)

        if etag or last_modified:
            return get_conditional_response(
                request,
                etag=etag,
                last_modified=last_modified,
                response=response,
            )

        return response
