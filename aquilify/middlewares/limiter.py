import time
from typing import Callable, Awaitable, Dict, List, Optional, Tuple
from ..wrappers import Request, Response

class Limiter:
    def __init__(
        self,
        limit: int,
        window: int,
        exempt_paths: List[str] = [],
        custom_headers: Dict[str, str] = {},
        dynamic_limits: Dict[str, Callable[[int, int], Tuple[int, int]]] = {},
        concurrency_control: bool = False,
        rate_limit_expiry: Dict[str, int] = {},
        monitoring_callback: Optional[Callable[[str, int, int, int], Awaitable[None]]] = None,
        whitelist: List[str] = [],
        blacklist: List[str] = [],
        rate_limit_by_endpoint: Dict[str, Tuple[int, int]] = {},
        rate_limit_adjustments: Dict[str, Callable[[int, int], Tuple[int, int]]] = {},
        rate_limit_expiry_policies: Dict[str, Callable[[int, int], int]] = {},
        ip_rate_limits: Dict[str, Tuple[int, int]] = {},
        rate_limit_bypass_tokens: Dict[str, List[str]] = {},
        advanced_monitoring_and_reporting: Optional[Callable[[str, int, int, int], Awaitable[None]]] = None,
        granular_rate_limits: Dict[str, Tuple[int, int]] = {},
        automated_rate_limit_adjustment: Optional[Callable[[str, int, int], Awaitable[Tuple[int, int]]]] = None,
        granular_rate_limit_callback: Optional[Callable[[str, str], Awaitable[Tuple[int, int]]]] = None,
    ):
        self.default_limit = limit
        self.default_window = window
        self.exempt_paths = exempt_paths
        self.custom_headers = custom_headers
        self.dynamic_limits = dynamic_limits
        self.concurrency_control = concurrency_control
        self.rate_limit_expiry = rate_limit_expiry
        self.monitoring_callback = monitoring_callback
        self.whitelist = whitelist
        self.blacklist = blacklist
        self.requests: Dict[str, List[float]] = {}
        self.concurrent_requests: Dict[str, int] = {}
        self.rate_limit_by_endpoint = rate_limit_by_endpoint
        self.rate_limit_adjustments = rate_limit_adjustments
        self.rate_limit_expiry_policies = rate_limit_expiry_policies
        self.ip_rate_limits = ip_rate_limits
        self.rate_limit_bypass_tokens = rate_limit_bypass_tokens
        self.advanced_monitoring_report = advanced_monitoring_and_reporting
        self.granular_rate_limits = granular_rate_limits
        self.automated_rate_limit_adjustment = automated_rate_limit_adjustment
        self.granular_rate_limit_callback = granular_rate_limit_callback
        self.cache_size = 1000 
        self.rate_limit_cache = {}
        self.rate_limits = {}

    async def __call__(self, request: Request, response: Response) -> Response:
        client_ip: str = await request.remote_addr
        current_time: float = time.time()
        endpoint: str = request.path

        if self.is_exempt_path(endpoint) or self.is_whitelisted(client_ip) or await self.is_bypass_token(request) or client_ip in self.blacklist:
            return response

        limit, window = self.get_rate_limit(client_ip, endpoint)
        limit, window = self.apply_rate_limit_adjustments(client_ip, endpoint, limit, window)

        if self.is_concurrency_control_enabled(client_ip) and self.is_concurrency_exceeded(client_ip):
            return Response(status_code=429, content="Concurrency limit exceeded")

        if not self.track_request(client_ip, current_time, window, limit):
            error_response = self.create_rate_limit_exceeded_response(client_ip, limit, window, current_time)
            return error_response

        if self.is_rate_limit_expired(client_ip, current_time, window):
            self.clear_rate_limit(client_ip)

        if self.monitoring_callback:
            await self.monitoring_callback(client_ip, limit, len(self.requests[client_ip]), window)

        if self.advanced_monitoring_report:
            advanced_monitoring_data = self.generate_advanced_monitoring_data(client_ip, limit, len(self.requests[client_ip]), window, response, request)
            await self.advanced_monitoring_report(advanced_monitoring_data)

        if self.granular_rate_limit_callback:
            limit, window = await self.granular_rate_limit_callback(client_ip, endpoint)
            if limit and window:
                self.rate_limits[client_ip] = (limit, window)

        return response

    def is_exempt_path(self, endpoint: str) -> bool:
        return endpoint in self.exempt_paths

    def is_whitelisted(self, client_ip: str) -> bool:
        return client_ip in self.whitelist

    async def is_bypass_token(self, request: Request) -> bool:
        token = await request.headers.get("x-bypass-token")
        return any(token in tokens for tokens in self.rate_limit_bypass_tokens.values())

    def get_rate_limit(self, client_ip: str, endpoint: str) -> Tuple[int, int]:
        # Check the cache first
        cached_rate_limit = self.rate_limit_cache.get((client_ip, endpoint))
        if cached_rate_limit:
            return cached_rate_limit

        if endpoint in self.rate_limit_by_endpoint:
            rate_limit = self.rate_limit_by_endpoint[endpoint]
        elif client_ip in self.rate_limits:
            rate_limit = self.rate_limits[client_ip]
        elif client_ip in self.ip_rate_limits:
            rate_limit = self.ip_rate_limits[client_ip]
        elif endpoint in self.granular_rate_limits:
            rate_limit = self.granular_rate_limits[endpoint]
        else:
            rate_limit = (self.default_limit, self.default_window)

        if self.automated_rate_limit_adjustment:
            limit, window = self.automated_rate_limit_adjustment(client_ip, rate_limit[0], rate_limit[1])
            rate_limit = (limit, window)

        # Update the cache
        self.rate_limit_cache[(client_ip, endpoint)] = rate_limit

        return rate_limit

    def apply_rate_limit_adjustments(
        self, client_ip: str, endpoint: str, limit: int, window: int
    ) -> Tuple[int, int]:
        if endpoint in self.rate_limit_adjustments:
            return self.rate_limit_adjustments[endpoint](limit, window)
        if client_ip in self.dynamic_limits:
            return self.dynamic_limits[client_ip](limit, window)
        return limit, window

    def is_concurrency_control_enabled(self, client_ip: str) -> bool:
        return self.concurrency_control

    def is_concurrency_exceeded(self, client_ip: str) -> bool:
        if client_ip not in self.concurrent_requests:
            self.concurrent_requests[client_ip] = 0
        return self.concurrent_requests[client_ip] >= self.default_limit

    def track_request(self, client_ip: str, current_time: float, window: int, limit: int) -> bool:
        if client_ip not in self.requests:
            self.requests[client_ip] = [current_time]
        else:
            client_requests = self.requests[client_ip]
            while client_requests and client_requests[0] < current_time - window:
                client_requests.pop(0)
            if len(client_requests) < limit:
                client_requests.append(current_time)
                return True
            return False
        return True

    def create_rate_limit_exceeded_response(
        self, client_ip: str, limit: int, window: int, current_time: float
    ) -> Response:
        error_response = Response(status_code=429, content="Rate limit exceeded")
        for header, value in self.custom_headers.items():
            error_response.headers[header] = value
        error_response.headers['X-RateLimit-Limit'] = str(limit)
        error_response.headers['X-RateLimit-Remaining'] = str(max(0, limit - len(self.requests.get(client_ip, []))))
        error_response.headers['X-RateLimit-Reset'] = str(int(current_time + window))
        return error_response

    def is_rate_limit_expired(self, client_ip: str, current_time: float, window: int) -> bool:
        if client_ip in self.rate_limit_expiry and (current_time - self.rate_limit_expiry[client_ip]) >= window:
            return True
        return False

    def clear_rate_limit(self, client_ip: str):
        self.rate_limits.pop(client_ip, None)
        self.requests.pop(client_ip, None)

    def get_rate_limit_expiry_time(self, client_ip: str, endpoint: str) -> int:
        if endpoint in self.rate_limit_expiry_policies:
            return self.rate_limit_expiry_policies[endpoint](client_ip)
        return self.rate_limit_expiry.get(client_ip, 0)
    
    def generate_advanced_monitoring_data(self, client_ip: str, limit: int, request_count: int, window: int, response: Response, request: Request):
        advanced_monitoring_data = {
            'client_ip': client_ip,
            'limit': limit,
            'requests': request_count,
            'window': window,
        }

        if response:
            advanced_monitoring_data['response_status'] = response.status_code
            advanced_monitoring_data['response_headers'] = dict(response.headers)

        if request:
            advanced_monitoring_data['request_method'] = request.method
            advanced_monitoring_data['request_path'] = request.path
            advanced_monitoring_data['request_headers'] = dict(request.headers)

        return advanced_monitoring_data

