from __future__ import annotations

import json
import secrets
import gzip 
import io

from typing import Optional, List, Union, Callable, Type, Any, Dict
from datetime import datetime, timedelta
from aquilify.exception.__handler import handle_exception
from aquilify.wrappers._http_status import HTTP_STATUS_PHRASE

class HTTPStatus:
    def __init__(self, code: int, phrase: str):
        self.code = code
        self.phrase = phrase

    def __str__(self):
        return f"{self.code} {self.phrase}"

class Response:
    def __init__(
        self,
        content: Union[str, bytes, Callable, None] = None,
        status_code: int = 200,
        headers: Optional[Dict[bytes, bytes]] = None,
        content_type: str = "text/plain",
        compress: bool = False,
    ):
        self.status_code = status_code
        self.headers = headers or {}
        self.content_type = content_type
        self.content = content
        self.streaming = callable(content)
        self.compress = compress
        self.encoding = 'utf-8'

    async def __call__(self, scope, receive, send):
        response_headers = {
            b'Content-Type': f"{self.content_type}; charset={self.encoding}".encode(),
            **self.headers,
        }

        response_headers = {key.encode() if isinstance(key, str) else key: value.encode() if isinstance(value, str) else value for key, value in response_headers.items()}

        try:
            content_length = 0
            if self.content:
                if isinstance(self.content, str):
                    content_length = len(self.content.encode('utf-8'))
                elif isinstance(self.content, bytes):
                    content_length = len(self.content)
                elif callable(self.content):
                    content_length = await self.get_stream_content_length(scope, receive, send)

            response_headers[b'Content-Length'] = str(content_length).encode()
            
            if self.compress:
                response_headers[b'Content-Encoding'] = b'gzip'
                await send({
                    'type': 'http.response.start',
                    'status': self.status_code,
                    'headers': list(response_headers.items()),
                })

                if self.streaming:
                    await self._send_streaming_response_compressed(scope, receive, send)
                else:
                    await self._send_standard_response_compressed(send)
            else:
                # No compression
                await send({
                    'type': 'http.response.start',
                    'status': self.status_code,
                    'headers': list(response_headers.items()),
                })

                if self.streaming:
                    await self._send_streaming_response(scope, receive, send)
                else:
                    await self._send_standard_response(send)

        except Exception as e:
            await handle_exception(e)

    async def _send_streaming_response_compressed(self, scope, receive, send):
        try:
            if callable(self.content):
                gzip_buffer = io.BytesIO()
                gzip_stream = gzip.GzipFile(fileobj=gzip_buffer, mode='w')
                async for chunk in self.content(scope, receive, send):
                    gzip_stream.write(chunk)
                    await send({
                        'type': 'http.response.body',
                        'body': gzip_buffer.getvalue(),
                        'more_body': True,
                    })
                    gzip_buffer.truncate(0)
                    gzip_buffer.seek(0)

                gzip_stream.close()
        except Exception as e:
            await handle_exception(e)

    async def _send_standard_response_compressed(self, send):
        try:
            if self.content is not None:
                if isinstance(self.content, str):
                    compressed_content = gzip.compress(self.content.encode('utf-8'))
                    await send({
                        'type': 'http.response.body',
                        'body': compressed_content,
                    })
                elif isinstance(self.content, bytes):
                    compressed_content = gzip.compress(self.content)
                    await send({
                        'type': 'http.response.body',
                        'body': compressed_content,
                    })
                else:
                    # Default to JSON serialization for other types
                    content_str = json.dumps(self.content)
                    compressed_content = gzip.compress(content_str.encode('utf-8'))
                    await send({
                        'type': 'http.response.body',
                        'body': compressed_content,
                    })

        except Exception as e:
            await handle_exception(e)

    async def _send_streaming_response(self, scope, receive, send):
        try:
            if self.content:
                async for chunk in self.content(scope, receive, send):
                    await send({
                        'type': 'http.response.body',
                        'body': chunk.encode('utf-8') if isinstance(chunk, str) else chunk,
                    })

        except Exception as e:
            await handle_exception(e)

    async def _send_standard_response(self, send):
        try:
            if self.content is not None:
                if isinstance(self.content, str):
                    await send({
                        'type': 'http.response.body',
                        'body': self.content.encode('utf-8'),
                    })
                elif isinstance(self.content, bytes):
                    await send({
                        'type': 'http.response.body',
                        'body': self.content,
                    })
                else:
                    # Default to JSON serialization for other types
                    content_str = json.dumps(self.content)
                    await send({
                        'type': 'http.response.body',
                        'body': content_str.encode('utf-8'),
                    })

        except Exception as e:
            await handle_exception(e)

    async def get_stream_content_length(self, scope, receive, send):
        content_length = 0
        async for chunk in self.content(scope, receive, send):
            if isinstance(chunk, str):
                content_length += len(chunk.encode('utf-8'))
            elif isinstance(chunk, bytes):
                content_length += len(chunk)
        return content_length

    @property
    def max_cookie_size(self):
        return int(self.headers.get("Set-Cookie-Size", 4096))

    async def set_cookie(
        self,
        key: str,
        value: str,
        max_age: int = None,
        expires: Optional[Union[int, datetime]] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None,
    ):
        try:
            cookie_parts = [f"{key}={value}"]

            if max_age is not None:
                cookie_parts.append(f"Max-Age={max_age}")
            if expires is not None:
                if isinstance(expires, int):
                    expires = datetime.now() + timedelta(seconds=expires)
                cookie_parts.append(f"Expires={expires.strftime('%a, %d %b %Y %H:%M:%S GMT')}")
            if path:
                cookie_parts.append(f"Path={path}")
            if domain:
                cookie_parts.append(f"Domain={domain}")
            if secure:
                cookie_parts.append("Secure")
            if httponly:
                cookie_parts.append("HttpOnly")
            if samesite:
                cookie_parts.append(f"SameSite={samesite}")

            self.headers["Set-Cookie"] = "; ".join(cookie_parts)

        except Exception as e:
            await handle_exception(e)
            
    def _set_cookie(
        self,
        key: str,
        value: str = None,
        max_age: int = None,
        expires: Optional[Union[int, datetime]] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None,
    ):
        try:
            cookie_parts = [f"{key}={value}"]

            if max_age is not None:
                cookie_parts.append(f"Max-Age={max_age}")
            if expires is not None:
                if isinstance(expires, int):
                    expires = datetime.now() + timedelta(seconds=expires)
                cookie_parts.append(f"Expires={expires.strftime('%a, %d %b %Y %H:%M:%S GMT')}")
            if path:
                cookie_parts.append(f"Path={path}")
            if domain:
                cookie_parts.append(f"Domain={domain}")
            if secure:
                cookie_parts.append("Secure")
            if httponly:
                cookie_parts.append("HttpOnly")
            if samesite:
                cookie_parts.append(f"SameSite={samesite}")

            self.headers["Set-Cookie"] = "; ".join(cookie_parts)

        except Exception as e:
            raise e

    async def delete_cookie(self, key: str):
        try:
            # Create a new dictionary for the Set-Cookie header with Expires in the past
            expires = datetime(1970, 1, 1).strftime('%a, %d %b %Y %H:%M:%S GMT')
            self.headers["Set-Cookie"] = f"{key}=; Expires={expires}; Max-Age=0; Path=/"
        except Exception as e:
            await handle_exception(e)
            
    def _del_cookie(self, key, path="/", domain=None, samesite=None):
        # Browsers can ignore the Set-Cookie header if the cookie doesn't use
        # the secure flag and:
        # - the cookie name starts with "__Host-" or "__Secure-", or
        # - the samesite is "none".
        secure = key.startswith(("__Secure-", "__Host-")) or (
            samesite and samesite.lower() == "none"
        )
        self._set_cookie(
            key,
            max_age=0,
            path=path,
            domain=domain,
            secure=secure,
            expires=datetime(1970, 1, 1),
            samesite=samesite,
        )

    async def get_cookie(self, key: str) -> Optional[str]:
        try:
            cookies = self.headers.get("Cookie")
            if cookies:
                for cookie in cookies.split("; "):
                    name, value = cookie.split("=")
                    if name == key:
                        return value
            return None

        except Exception as e:
            await handle_exception(e)

    async def generate_secure_cookie(self, key: str, max_age: int = 3600) -> str:
        try:
            secure_token = secrets.token_hex(32)

            # Store the token in a cookie
            await self.set_cookie(key, secure_token, max_age=max_age, secure=True, httponly=True, samesite="Strict")

            return secure_token

        except Exception as e:
            await handle_exception(e)

    async def verify_secure_cookie(self, key: str, token: str) -> bool:
        try:
            stored_token = await self.get_cookie(key)
            return stored_token == token

        except Exception as e:
            await handle_exception(e)

    async def last_modified(self, date: datetime):
        try:
            self.headers["Last-Modified"] = date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        except Exception as e:
            await handle_exception(e)

    async def etag(self, value: str):
        try:
            self.headers["ETag"] = value
        except Exception as e:
            await handle_exception(e)

    async def cache_for(
        self,
        seconds: int,
        public: bool = True,
        immutable: bool = False,
    ):
        try:
            directives = []
            if public:
                directives.append("public")
            if immutable:
                directives.append("immutable")
            directives.append(f"max-age={seconds}")
            self.cache_control({"no-store": False, "private": False, "no-cache": False, "max-age": seconds})
            self.expires(datetime.now() + timedelta(seconds=seconds))

        except Exception as e:
            await handle_exception(e)

    async def no_cache(self):
        try:
            self.cache_control({"no-store": True, "private": False, "no-cache": True})
        except Exception as e:
            await handle_exception(e)

    async def content_disposition(self, filename: str, inline: bool = False):
        try:
            disposition = "inline" if inline else "attachment"
            self.headers["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        except Exception as e:
            await handle_exception(e)

    async def json(self, content: Any, status_code: int = 200):
        try:
            self.content_type = "application/json"
            self.status_code = status_code
            self.content = content
            self.streaming = False
        except Exception as e:
            await handle_exception(e)

    async def stream(self, content: Union[str, bytes, Callable] = None):
        try:
            self.streaming = True
            if content is not None:
                self.content = content
        except Exception as e:
            await handle_exception(e)

    @property
    def status_text(self):
        return f"{self.status_code} {HTTP_STATUS_PHRASE(self.status_code, 'Unknown')}"

    async def vary(self, headers: List[str]):
        try:
            self.headers["Vary"] = ", ".join(headers)
        except Exception as e:
            await handle_exception(e)

    async def calculate_content_length(self):
        try:
            if self.content is not None:
                if isinstance(self.content, str):
                    return len(self.content.encode("utf-8"))
                elif isinstance(self.content, bytes):
                    return len(self.content)
                else:
                    # Default to JSON serialization for other types
                    content_str = json.dumps(self.content)
                    return len(content_str.encode("utf-8"))
            return 0
        except Exception as e:
            await handle_exception(e)

    async def date(self, date_str: str):
        try:
            self.headers["Date"] = date_str
        except Exception as e:
            await handle_exception(e)

    async def expires(self, expires_str: str):
        try:
            self.headers["Expires"] = expires_str
        except Exception as e:
            await handle_exception(e)
            
    @property
    def location(self):
        return self.headers.get("Location")

    @location.setter
    async def location(self, value):
        try:
            self.headers["Location"] = value
        except Exception as e:
            await handle_exception(e)

    async def accept_ranges(self, ranges: str):
        try:
            self.headers["Accept-Ranges"] = ranges
        except Exception as e:
            await handle_exception(e)

    async def age(self, age: int):
        try:
            self.headers["Age"] = str(age)
        except Exception as e:
            await handle_exception(e)

    async def allow(self, methods: List[str]):
        try:
            self.headers["Allow"] = ", ".join(methods)
        except Exception as e:
            await handle_exception(e)

    async def cache_control(self, directives: Dict[str, Union[str, int]]):
        try:
            directives_str = ", ".join([f"{key}={value}" for key, value in directives.items()])
            self.headers["Cache-Control"] = directives_str
        except Exception as e:
            await handle_exception(e)

    async def access_control_allow_credentials(self, allow: bool):
        try:
            self.headers["Access-Control-Allow-Credentials"] = str(allow).lower()
        except Exception as e:
            await handle_exception(e)

    async def access_control_allow_headers(self, headers: List[str]):
        try:
            self.headers["Access-Control-Allow-Headers"] = ", ".join(headers)
        except Exception as e:
            await handle_exception(e)

    async def access_control_allow_methods(self, methods: List[str]):
        try:
            self.headers["Access-Control-Allow-Methods"] = ", ".join(methods)
        except Exception as e:
            await handle_exception(e)

    async def access_control_allow_origin(self, origin: str):
        try:
            self.headers["Access-Control-Allow-Origin"] = origin
        except Exception as e:
            await handle_exception(e)

    async def access_control_expose_headers(self, headers: List[str]):
        try:
            self.headers["Access-Control-Expose-Headers"] = ", ".join(headers)
        except Exception as e:
            await handle_exception(e)

    async def add_etag(self):
        try:
            if 'ETag' not in self.headers:
                self.etag(self.get_etag())
        except Exception as e:
            await handle_exception(e)

    async def autocorrect_location_header(self):
        try:
            if self.status_code in {301, 302, 303, 307, 308} and 'Location' not in self.headers:
                self.location("/")
        except Exception as e:
            await handle_exception(e)

    async def automatically_set_content_length(self):
        try:
            if 'Content-Length' not in self.headers:
                content_length = await self.calculate_content_length()
                if content_length > 0:
                    self.headers['Content-Length'] = str(content_length)
        except Exception as e:
            await handle_exception(e)

    async def content_security_policy(self, policy: str):
        try:
            self.headers["Content-Security-Policy"] = policy
        except Exception as e:
            await handle_exception(e)

    async def content_security_policy_report_only(self, policy: str):
        try:
            self.headers["Content-Security-Policy-Report-Only"] = policy
        except Exception as e:
            await handle_exception(e)

    async def cross_origin_embedder_policy(self, policy: str):
        try:
            self.headers["Cross-Origin-Embedder-Policy"] = policy
        except Exception as e:
            await handle_exception(e)

    async def cross_origin_opener_policy(self, policy: str):
        try:
            self.headers["Cross-Origin-Opener-Policy"] = policy
        except Exception as e:
            await handle_exception(e)

    async def get_etag(self) -> str:
        try:
            return self.headers.get("ETag", "")
        except Exception as e:
            await handle_exception(e)

    async def implicit_sequence_conversion(self, enabled: bool):
        try:
            self.headers["Implicit-Sequence-Conversion"] = str(enabled).lower()
        except Exception as e:
            await handle_exception(e)

    @property
    def max_cookie_size(self) -> int:
        return int(self.headers.get("Set-Cookie-Size", 4096))

    async def www_authenticate(self, value: str):
        try:
            self.headers["WWW-Authenticate"] = value
        except Exception as e:
            await handle_exception(e)

    async def make_conditional(self, is_conditional: bool = True):
        try:
            if is_conditional:
                self.headers["Cache-Control"] = "no-cache"
        except Exception as e:
            await handle_exception(e)

