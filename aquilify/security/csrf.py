import secrets
import logging
import asyncio

from functools import wraps
from typing import Optional
from datetime import datetime, timedelta
from itsdangerous import (
    URLSafeTimedSerializer,
    BadTimeSignature,
    SignatureExpired
)

from ..wrappers import Request, Response
from ..exception.base import TooManyRequests

class CSRFTokenError(Exception):
    pass

class RateLimiter:
    def __init__(self, max_requests: int, time_window: timedelta):
        self.max_requests = max_requests
        self.time_window = time_window
        self.tokens = {}
    
    def check(self, client_ip: str) -> bool:
        current_time = datetime.utcnow()
        self.cleanup_expired_tokens(current_time)

        if client_ip not in self.tokens:
            self.tokens[client_ip] = {"count": 1, "start_time": current_time}
            return True

        if self.tokens[client_ip]["count"] < self.max_requests:
            self.tokens[client_ip]["count"] += 1
            return True

        return False

    def cleanup_expired_tokens(self, current_time):
        expired_ips = [ip for ip, data in self.tokens.items() if (current_time - data["start_time"]).total_seconds() > self.time_window.total_seconds()]
        for ip in expired_ips:
            del self.tokens[ip]

class CSRF:
    def __init__(
        self,
        secret_key: str,
        expiration: Optional[timedelta] = timedelta(hours=1),
        csrf_token_key: str = "_csrf_token",
        cookie_options: Optional[dict] = None,
        protected_methods: Optional[list] = ["POST", "PUT", "DELETE"],
        logger: Optional[logging.Logger] = None,
        token_length: int = 32,
        enforce_https: bool = True,
        min_entropy: float = 3.5,
        ip_verification: bool = True,
        trusted_ips: Optional[list] = None,
        rate_limit: Optional[dict] = None,
        token_revocation_expiration: Optional[timedelta] = timedelta(days=1),
        max_token_lifetime: Optional[timedelta] = timedelta(days=7),
        token_refresh_interval: Optional[timedelta] = timedelta(hours=6),
    ):
        self.secret_key = secret_key
        self.expiration = expiration
        self.csrf_token_key = csrf_token_key
        self.cookie_options = cookie_options or {"httponly": True, "secure": enforce_https}
        self.protected_methods = protected_methods
        self.logger = logger or logging.getLogger(__name__)
        self.token_length = token_length
        self.enforce_https = enforce_https
        self.min_entropy = min_entropy
        self.ip_verification = ip_verification
        self.trusted_ips = set(trusted_ips) if trusted_ips else set()
        self.rate_limit = rate_limit
        self.rate_limiter = RateLimiter(max_requests=rate_limit["max_requests"], time_window=rate_limit["time_window"]) if rate_limit else None
        self.token_revocation_expiration = token_revocation_expiration
        self.max_token_lifetime = max_token_lifetime
        self.token_refresh_interval = token_refresh_interval
        self.serializer = URLSafeTimedSerializer(secret_key)
        self.request_tokens = {}
        self.revoked_tokens = set()

    async def generate_csrf_token(self, client_ip: str) -> str:
        token = secrets.token_hex(32)
        csrf_data = {"token": token, "ip": client_ip, "_created": datetime.utcnow().timestamp()}
        csrf_token = await asyncio.to_thread(self.serializer.dumps, csrf_data)
        self.logger.info(f"CSRF token generated for IP {client_ip}")
        return csrf_token

    async def inject_csrf_token(self, response: Response, csrf_token: str) -> Response:
        try:
            await response.set_cookie(
                self.csrf_token_key,
                csrf_token,
                max_age=self.expiration.total_seconds() if self.expiration else None,
                **self.cookie_options
            )
            self.logger.info("CSRF token injected into the response")
            return response
        except Exception as e:
            self.logger.error(f"Failed to inject CSRF token: {e}")
            raise CSRFTokenError("Failed to inject CSRF token")

    async def validate_csrf_token(self, request: Request) -> bool:
        try:
            csrf_token = request.cookies.get(self.csrf_token_key)
            form = await request.form()
            submitted_token = form["_csrf_token"]

            current_time = await asyncio.to_thread(datetime.utcnow)
            if self.max_token_lifetime and not await self._is_within_lifetime(csrf_token, current_time):
                self.logger.warning("CSRF token validation failed: Token has expired.")
                return False

            if csrf_token in self.revoked_tokens:
                self.logger.warning("CSRF token validation failed: Token has been revoked.")
                return False

            decoded_csrf_token = await asyncio.to_thread(self.serializer.loads, csrf_token)
            decoded_submitted_token = await asyncio.to_thread(self.serializer.loads, submitted_token)

            if self.ip_verification and decoded_csrf_token.get("ip") != request.client.host:
                self.logger.warning("CSRF token validation failed: IP address mismatch.")
                return False

            if self.trusted_ips and request.client.host not in self.trusted_ips:
                self.logger.warning("CSRF token validation failed: Untrusted IP address.")
                return False

            await self._cleanup_revoked_tokens()

            return csrf_token is not None and decoded_csrf_token == decoded_submitted_token
        except (BadTimeSignature, SignatureExpired) as e:
            self.logger.warning(f"CSRF token validation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error validating CSRF token: {e}")
            raise CSRFTokenError("Error validating CSRF token")

    def csrf_protect(self, func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if request.method in self.protected_methods:
                try:
                    if not await self.validate_csrf_token(request):
                        return Response("CSRF Token Validation Failed", status_code=403)
                except CSRFTokenError:
                    return Response("CSRF Token Validation Error", status_code=500)

                client_ip = self.get_client_ip(request)

                if self.rate_limiter and not self.rate_limiter.check(client_ip):
                    self.logger.warning(f"Rate limit exceeded for IP {client_ip}")
                    return TooManyRequests("Rate limit exceeded")

                if self.token_refresh_interval and await self.should_refresh_csrf_token(request.cookies.get(self.csrf_token_key)):
                    new_csrf_token = await self.generate_csrf_token(client_ip)
                    return await self.inject_csrf_token(Response(), new_csrf_token)

            return await func(request, *args, **kwargs)

        return wrapper

    async def _cleanup_revoked_tokens(self):
        current_time = await asyncio.to_thread(datetime.utcnow)
        self.revoked_tokens = {token for token in self.revoked_tokens if await self.is_within_lifetime(token, current_time())}

    async def _is_within_lifetime(self, csrf_token: str, current_time: datetime) -> bool:
        if not self.max_token_lifetime:
            return True

        try:
            token_data = await asyncio.to_thread(self.serializer.loads, csrf_token)
            created_time = datetime.fromtimestamp(token_data["_created"])
            return (current_time - created_time) <= self.max_token_lifetime
        except Exception as e:
            self.logger.warning(f"Failed to extract creation time from CSRF token: {e}")
            return False

    async def should_refresh_csrf_token(self, csrf_token: str) -> bool:
        if not self.token_refresh_interval:
            return False

        try:
            token_data = await asyncio.to_thread(self.serializer.loads, csrf_token)
            created_time = datetime.fromtimestamp(token_data["_created"])
            return (datetime.utcnow() - created_time) >= self.token_refresh_interval
        except Exception as e:
            self.logger.warning(f"Failed to extract creation time from CSRF token: {e}")
            return False

    def get_client_ip(self, request: Request) -> str:
        return request.headers.get("X-Real-IP") or request.client.host or "127.0.0.1"

    def revoke_csrf_token(self, csrf_token: str):
        self.revoked_tokens.add(csrf_token)
