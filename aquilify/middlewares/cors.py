import logging
from typing import List, Optional
from ..wrappers import Request, Response
from ..settings.cors import CORSConfigSettings

_settings = CORSConfigSettings().fetch()

class CORS:
    """
    Middleware for handling Cross-Origin Resource Sharing (CORS).

    Args:
        allow_origins (Union[List[str], Callable[[str], bool], Set[str]]): List of allowed origins,
            a callable that returns a boolean, or a set of allowed origins.
        allow_methods (List[str]): List of allowed HTTP methods.
        allow_headers (Union[List[str], Callable[[str], bool], Set[str]]): List of allowed headers,
            a callable that returns a boolean, or a set of allowed headers.
        expose_headers (Union[List[str], Set[str]]): List of headers exposed to the browser.
        allow_credentials (Union[bool, Callable[[str], bool]]): Allow credentials in requests.
        max_age (int): Maximum age (in seconds) to cache preflight response.
        security_headers (Dict[str, str]): Additional security headers to include in the response.
        log_cors_requests (bool): Log CORS requests.
        preflight_response (Callable[[Request], Optional[Response]]): Custom preflight response handler.
        cache_preflight (bool): Cache preflight responses to reduce redundant preflight requests.
        custom_response_handler (Callable[[Request, str, List[str]], Optional[Response]]):
            Custom response handler when a CORS request is denied.
        origin_whitelist (Callable[[str], bool]): Custom function to whitelist origins dynamically.
        automatic_preflight_handling (bool): Automatically handle preflight requests (OPTIONS).
        dynamic_headers_whitelist (Callable[[List[str]], List[str]]):
            Dynamically whitelist headers based on the requested headers.

    Returns:
        Middleware function to handle CORS requests.

    Usage:
        cors_middleware = CORS(
            allow_origins=['http://example.com', 'https://example.com'],
            allow_methods=['GET', 'POST'],
            allow_headers=['Authorization', 'Content-Type'],
            expose_headers=['Content-Length', 'X-Custom-Header'],
            allow_credentials=True,
            max_age=600,
            security_headers={'X-Frame-Options': 'SAMEORIGIN'},
            log_cors_requests=True,
            cache_preflight=True,
            automatic_preflight_handling=True
        )

        app.add_middleware(cors_middleware)

    Usage in a Aquilify application:
    ```python
        from aquilify.core import Aquilify

        app = Aquilify()
        cors_middleware = CORS(
            allow_origins=['http://example.com', 'https://example.com'],
            allow_methods=['GET', 'POST'],
            allow_headers=['Authorization', 'Content-Type'],
            expose_headers=['Content-Length', 'X-Custom-Header'],
            allow_credentials=True,
            max_age=600,
            security_headers={'X-Frame-Options': 'SAMEORIGIN'},
            log_cors_requests=True,
            cache_preflight=True,
            automatic_preflight_handling=True
        )

        app.add_middleware(cors_middleware)

        @app.route("/")
        async def read_root():
            return {"message": "Hello, CORS!"}
            """
    def __init__(
        self
    ):
        self.allow_origins = _settings.get('allowed_origin') or ["*"]
        self.allow_methods = _settings.get('allowed_method') or ["*"]
        self.allow_headers = _settings.get('allowed_headers') or ["*"]
        self.expose_headers = _settings.get('expose_headers') or set()
        self.allow_credentials = _settings.get('allowed_credentials') or False
        self.max_age = _settings.get('max_age') or 600
        self.security_headers = _settings.get('security_headers') or {}
        self.log_cors_requests = _settings.get('log_request') or True
        self.preflight_response = _settings.get('preflight_response') or None
        self.preflight_cache = _settings.get('preflight_cache') or {}
        self.custom_response_handler = _settings.get('response_handler') or None
        self.origin_whitelist = _settings.get('origin_whitelist') or None
        self.automatic_preflight_handling = _settings.get('automatic_preflight_handling') or True
        self.dynamic_headers_whitelist = _settings.get('dynamic_headers_whitelist') or None
        self.exclude_paths = _settings.get('exclude_paths') or []

    async def __call__(self, request: Request, response: Response):
        """
        Middleware entry point to handle CORS.

        Args:
            request (Request): The incoming HTTP request.
            response (Response): The HTTP response.

        Returns:
            Response: The modified HTTP response with CORS headers.
        """
        origin = request.origin

        if request.path in self.exclude_paths:
            return response

        if await self.is_origin_allowed(origin):
            if origin is not None:
                response.headers[b"Access-Control-Allow-Origin"] = origin.encode()
            else:
                response.headers[b"Access-Control-Allow-Origin"] = '*'.encode()
        else:
            response.headers[b"Access-Control-Allow-Origin"] = b"null"

        if request.method == "OPTIONS":
            if self.automatic_preflight_handling:
                await self.handle_preflight_request(request, response)
        else:
            response.headers[b"Vary"] = b"Origin"

        self.add_cors_headers(response)

        if self.log_cors_requests:
            self.log_cors_request(request, origin)

        return response

    async def handle_preflight_request(self, request: Request, response: Response):
        """
        Handles preflight (OPTIONS) requests for CORS.

        Args:
            request (Request): The incoming HTTP request.
            response (Response): The HTTP response.

        Returns:
            Optional[Response]: The preflight response if allowed, None otherwise.
        """
        requested_method = request.headers.get("access-control-request-method")
        requested_headers = request.headers.get("access-control-request-headers")

        if self.is_method_allowed(requested_method) and self.is_headers_allowed(requested_headers):
            if self.preflight_response:
                preflight_resp = self.preflight_response(request)
                if preflight_resp:
                    return preflight_resp
            response.status_code = 204
            response.content = b""
            response.headers[b"Access-Control-Max-Age"] = str(self.max_age).encode()
        else:
            disallowed_headers = self.disallowed_headers(requested_headers)
            custom_resp = self.handle_custom_response(request, request.origin, disallowed_headers)
            if custom_resp:
                return custom_resp
            response.status_code = 403

    def add_cors_headers(self, response: Response):
        """
        Adds CORS headers to the HTTP response.

        Args:
            response (Response): The HTTP response to modify.
        """
        response.headers[b"Access-Control-Allow-Credentials"] = b"true" if self.allow_credentials else b"false"
        response.headers[b"Access-Control-Allow-Headers"] = self.format_allowed_headers().encode()
        response.headers[b"Access-Control-Allow-Methods"] = ", ".join(self.allow_methods).encode()

        if self.expose_headers:
            response.headers[b"Access-Control-Expose-Headers"] = ", ".join(self.expose_headers).encode()

        for key, value in self.security_headers.items():
            response.headers[key.encode()] = value.encode()

    def format_allowed_headers(self) -> str:
        """
        Formats allowed headers for the response.

        Returns:
            str: Formatted allowed headers for the response.
        """
        if callable(self.allow_headers):
            return "*"
        return ", ".join(self.allow_headers).encode().decode()

    async def is_origin_allowed(self, origin: str) -> bool:
        """
        Checks if the given origin is allowed.

        Args:
            origin (str): The origin to check.

        Returns:
            bool: True if the origin is allowed or if "*" is in self.allow_origins, False otherwise.
        """
        if "*" in self.allow_origins:
            return True
        if callable(self.allow_origins):
            return await self.allow_origins(origin)
        if isinstance(self.allow_origins, set):
            return origin in self.allow_origins
        return origin in self.allow_origins

    def is_method_allowed(self, method: str) -> bool:
        """
        Checks if the given HTTP method is allowed.

        Args:
            method (str): The HTTP method to check.

        Returns:
            bool: True if the method is allowed, False otherwise.
        """
        return "*" in self.allow_methods or method in self.allow_methods

    def is_headers_allowed(self, headers: Optional[str]) -> bool:
        """
        Checks if the given headers are allowed.

        Args:
            headers (Optional[str]): The headers to check.

        Returns:
            bool: True if the headers are allowed, False otherwise.
        """
        if callable(self.allow_headers):
            return self.allow_headers(headers)
        if "*" in self.allow_headers:
            return True
        if headers is not None:
            requested_headers = [header.strip() for header in headers.split(",")]
            if self.dynamic_headers_whitelist:
                return all(requested_header in self.dynamic_headers_whitelist(requested_headers) for requested_header in requested_headers)
            return all(requested_header in self.allow_headers for requested_header in requested_headers)
        return False

    def disallowed_headers(self, requested_headers: str) -> List[str]:
        """
        Finds headers that are not allowed.

        Args:
            requested_headers (str): The headers to check.

        Returns:
            List[str]: List of headers that are not allowed.
        """
        if callable(self.allow_headers):
            return []
        if "*" in self.allow_headers:
            return []
        if requested_headers is not None:
            requested_headers = [header.strip() for header in requested_headers.split(",")]
            return [header for header in requested_headers if header not in self.allow_headers]
        return []

    def log_cors_request(self, request: Request, origin: str):
        """
        Logs CORS request details.

        Args:
            request (Request): The incoming HTTP request.
            origin (str): The origin of the request.
        """
        logger = logging.getLogger("CORS")
        logger.info(f"CORS Request: Origin - {origin}, Method - {request.method}, Path - {request.path}")

    def handle_custom_response(self, request: Request, origin: str, disallowed_headers: List[str]) -> Optional[Response]:
        """
        Handles custom response when a CORS request is denied.

        Args:
            request (Request): The incoming HTTP request.
            origin (str): The origin of the request.
            disallowed_headers (List[str]): List of disallowed headers.

        Returns:
            Optional[Response]: Custom response if provided, None otherwise.
        """
        if self.custom_response_handler:
            return self.custom_response_handler(request, origin, disallowed_headers)
        return None

