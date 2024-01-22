import secrets
import logging
import asyncio

from datetime import datetime, timedelta

from aquilify.core import signing

from ..wrappers import Request, Response

from ..settings.csrf import CSRFConfigSettings

try:
    _config_settings = CSRFConfigSettings()
    _config_settings.fetch()
    _settings = _config_settings.csrf_data[0]
except Exception as e:
    raise Exception("CSRF Configuration Not Found in settings.py, configure the CSRF settings before you use.")

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
        self
    ):
        self.secret_key = _settings['options'].get('secret_key')
        self.expiration = _settings['options'].get('expiration') or timedelta(hours=1)
        self.csrf_token_key = _settings['options'].get('token_key') or "_csrf_token"
        self.cookie_options = _settings['options'].get('cookie_options') or {"httponly": True, "secure": True, "samesite": 'strict'}
        self.protected_methods = _settings['options'].get('protected_methods') or ["POST", "PUT", "DELETE"]
        self.logger = _settings['options'].get('logger') or logging.getLogger(__name__)
        self.ip_verification = _settings['options'].get('ip_verification') or True
        self.trusted_ips = set(_settings['options'].get('trusted_ips')) if _settings['options'].get('trusted_ips') else set()
        self.rate_limit = None
        self.rate_limiter = RateLimiter(max_requests=self.rate_limit["max_requests"], time_window=self.rate_limit["time_window"]) if self.rate_limit else None
        self.max_token_lifetime = _settings['options'].get('max_token_lifetime') or timedelta(days=7)
        self.token_refresh_interval = _settings['options'].get('token_refresh_interval') or timedelta(days=6)
        self.serializer = signing
        self.revoked_tokens = set()

        assert _settings.get('backend') == 'aquilify.security.csrf.CSRF', "Invalid backend for CSRF Protection."

    async def generate_csrf_token(self, client_ip: str) -> str:
        token = secrets.token_hex(32)
        csrf_data = {"token": token, "ip": client_ip, "_created": datetime.utcnow().timestamp()}
        csrf_token = await asyncio.to_thread(self.serializer.dumps, csrf_data, self.secret_key)
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
            decoded_submitted_token = await asyncio.to_thread(self.serializer.loads, submitted_token, self.secret_key)

            if self.ip_verification and decoded_csrf_token.get("ip") != request.client.host:
                self.logger.warning("CSRF token validation failed: IP address mismatch.")
                return False

            if self.trusted_ips and '*' not in self.trusted_ips and request.client.host not in self.trusted_ips:
                self.logger.warning("CSRF token validation failed: Untrusted IP address.")
                return False

            return csrf_token is not None and decoded_csrf_token == decoded_submitted_token
        except (signing.BadSignature, signing.SignatureExpired) as e:
            self.logger.warning(f"CSRF token validation failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error validating CSRF token: {e}")
            raise CSRFTokenError("Error validating CSRF token")

    async def _is_within_lifetime(self, csrf_token: str, current_time: datetime) -> bool:
        if not self.max_token_lifetime:
            return True

        try:
            token_data = await asyncio.to_thread(self.serializer.loads, csrf_token, self.secret_key)
            created_time = datetime.fromtimestamp(token_data["_created"])
            return (current_time - created_time) <= self.max_token_lifetime
        except Exception as e:
            self.logger.warning(f"Failed to extract creation time from CSRF token: {e}")
            return False

    async def should_refresh_csrf_token(self, csrf_token: str) -> bool:
        if not self.token_refresh_interval:
            return False

        try:
            token_data = await asyncio.to_thread(self.serializer.loads, csrf_token, self.secret_key)
            created_time = datetime.fromtimestamp(token_data["_created"])
            return (datetime.utcnow() - created_time) >= self.token_refresh_interval
        except Exception as e:
            self.logger.warning(f"Failed to extract creation time from CSRF token: {e}")
            return False

    def get_client_ip(self, request: Request) -> str:
        return request.headers.get("X-Real-IP") or request.client.host or "127.0.0.1"

    def revoke_csrf_token(self, csrf_token: str):
        self.revoked_tokens.add(csrf_token)
