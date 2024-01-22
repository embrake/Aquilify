import json
import zlib
import gzip
import time
import base64
import hashlib
import random
import logging
import platform
import http.client

from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Union, Dict, Any, List

from .response import Response

class HttpException(Exception):
    def __init__(self, status_code: int, reason: str = None):
        self.status_code = status_code
        self.reason = reason
        super().__init__(f"HTTP {status_code} - {reason}")

    def __str__(self) -> str:
        error_message = f"HTTP {self.status_code} - {self.reason}\n"
        return error_message

class ClientSession:
    def __init__(self):
        self.default_timeout: int = 10 
        self.max_redirects: int = 5
        self.session: Optional[Any] = None
        self.connection_pool: Dict[str, http.client.HTTPConnection] = {}
        self.user_agents: List[str] = self._get_user_agent()
        self.logger: logging.Logger = self._configure_logger()
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=10)
        self.request_retries: int = 0
        self.cache: Dict[str, Any] = {}
        self.response_cache_max_size: int = 1000
        self.default_headers: Dict[str, str] = {} 
        self.proxy: Optional[Dict[str, Union[str, int]]] = None 
        self.use_response_cache: bool = True

    def _get_user_agent(self) -> List[str]:
        user_agent = f"Python/{platform.python_version()} ({platform.system()}; {platform.release()})"
        return [user_agent]

    def _configure_logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        return logger

    def close_connections(self) -> None:
        for conn in self.connection_pool.values():
            conn.close()
        self.connection_pool.clear()

    def get(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Union[str, int]]] = None, 
            timeout: Optional[float] = None, retries: Optional[int] = None, use_cache: bool = True, auth: Optional[Dict[str, str]] = None) -> Response:
        return self.request("GET", url, headers=headers, params=params, timeout=timeout, retries=retries, use_cache=use_cache, auth=auth)

    def post(self, url: str, headers: Optional[Dict[str, str]] = None, data: Optional[str] = None, json_data: Optional[Dict[str, Any]] = None,
             files: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None, retries: Optional[int] = None, use_cache: bool = True, 
             auth: Optional[Dict[str, str]] = None) -> Response:
        return self.request("POST", url, headers=headers, data=data, json_data=json_data, files=files, timeout=timeout, retries=retries, use_cache=use_cache, auth=auth)

    def put(self, url: str, headers: Optional[Dict[str, str]] = None, data: Optional[str] = None, json_data: Optional[Dict[str, Any]] = None,
            timeout: Optional[float] = None, retries: Optional[int] = None, use_cache: bool = True, auth: Optional[Dict[str, str]] = None) -> Response:
        return self.request("PUT", url, headers=headers, data=data, json_data=json_data, timeout=timeout, retries=retries, use_cache=use_cache, auth=auth)

    def delete(self, url: str, headers: Optional[Dict[str, str]] = None, timeout: Optional[float] = None, retries: Optional[int] = None, use_cache: bool = True, auth: Optional[Dict[str, str]] = None) -> Response:
        return self.request("DELETE", url, headers=headers, timeout=timeout, retries=retries, use_cache=use_cache, auth=auth)

    def head(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Union[str, int]]] = None, 
             timeout: Optional[float] = None, retries: Optional[int] = None, use_cache: bool = True, auth: Optional[Dict[str, str]] = None) -> Response:
        return self.request("HEAD", url, headers=headers, params=params, timeout=timeout, retries=retries, use_cache=use_cache, auth=auth)

    def patch(self, url: str, headers: Optional[Dict[str, str]] = None, data: Optional[str] = None, json_data: Optional[Dict[str, Any]] = None,
              timeout: Optional[float] = None, retries: Optional[int] = None, use_cache: bool = True, auth: Optional[Dict[str, str]] = None) -> Response:
        return self.request("PATCH", url, headers=headers, data=data, json_data=json_data, timeout=timeout, retries=retries, use_cache=use_cache, auth=auth)

    def options(self, url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Union[str, int]]] = None, 
                timeout: Optional[float] = None, retries: Optional[int] = None, use_cache: bool = True, auth: Optional[Dict[str, str]] = None) -> Response:
        return self.request("OPTIONS", url, headers=headers, params=params, timeout=timeout, retries=retries, use_cache=use_cache, auth=auth)

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Union[str, int]]] = None,
        data: Optional[str] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        retries: Optional[int] = None,
        use_cache: bool = True,
        auth: Optional[Dict[str, str]] = None
    ) -> Optional[Response]:
        if timeout is None:
            timeout = self.default_timeout
        if retries is None:
            retries = self.request_retries

        cache_key = self._generate_cache_key(method, url, headers, params, data, json_data)
        if use_cache and cache_key in self.cache:
            return self.cache[cache_key]

        for _ in range(retries + 1):
            try:
                response = self._make_request(method, url, headers, params, data, json_data, files, timeout, auth)
                if response is not None:
                    if use_cache:
                        self._cache_response(cache_key, response)
                    return response
            except HttpException as e:
                self.logger.error(f"Request error: {e}")
                time.sleep(2 ** _)  # Exponential backoff for retries
            except Exception as e:
                self.logger.error(f"Request error: {type(e).__name__}: {e}")
        return None

    def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]],
        params: Optional[Dict[str, Union[str, int]]],
        data: Optional[str],
        json_data: Optional[Dict[str, Any]],
        files: Optional[Dict[str, Any]],
        timeout: Optional[float],
        auth: Optional[Dict[str, str]]
    ) -> Optional[Response]:
        redirect_count = 0

        while redirect_count < self.max_redirects:
            # Parse the URL
            url_parsed = urlparse(url)
            path = url_parsed.path or '/'
            query = url_parsed.query

            # Extract the host
            host = url_parsed.hostname
            if host is None:
                raise ValueError("Invalid URL. Unable to extract hostname.")

            # Extract the port
            port = url_parsed.port or 80

            conn_key = f"{host}:{port}"
            if conn_key not in self.connection_pool:
                self.connection_pool[conn_key] = http.client.HTTPConnection(host, port, timeout=timeout)

            user_agent = random.choice(self.user_agents)
            headers = headers or {}
            headers["Host"] = conn_key
            headers["User-Agent"] = user_agent

            if auth:
                auth_header = self._generate_auth_header(auth)
                headers.update(auth_header)

            conn = self.connection_pool[conn_key]
            body = None
            if json_data:
                data = json.dumps(json_data)
                headers["Content-Type"] = "application/json"
                body = data.encode()

            if data:
                headers["Content-Length"] = str(len(data))
                body = data.encode()

            try:
                if self.proxy:
                    conn.set_tunnel(host, port, headers={'Host': url})
                    conn.connect(self.proxy['host'], self.proxy['port'])

                conn.request(method, path + '?' + query, body=body, headers=headers)
                response = conn.getresponse()

                if 300 <= response.status < 400:
                    location = response.getheader("Location")
                    if location:
                        if not location.startswith(('http://', 'https://')):
                            location = urljoin(url, location)
                        url = location
                        redirect_count += 1
                        continue

                response_text = self._decode_response(response)

                if response.status >= 400:
                    raise HttpException(response.status, response.reason)

                content_type = response.headers.get("Content-Type", "")
                response_obj = Response(response.status, response_text, response.headers, content_type)
                return response_obj
            except HttpException:
                raise 
            except Exception as e:
                self.logger.error(f"Request error: {type(e).__name__}: {e}")
                return None
            finally:
                conn.close()

    def _decode_response(self, response: http.client.HTTPResponse) -> str:
        content_encoding = response.headers.get('Content-Encoding', '')
        if 'gzip' in content_encoding:
            return gzip.decompress(response.read()).decode()
        elif 'deflate' in content_encoding:
            return zlib.decompress(response.read(), -zlib.MAX_WBITS).decode()
        else:
            return response.read().decode()

    def _generate_cache_key(self, method: str, url: str, headers: Optional[Dict[str, str]], params: Optional[Dict[str, Union[str, int]]], data: Optional[str], 
                            json_data: Optional[Dict[str, Any]]) -> str:
        cache_key = hashlib.sha1()
        cache_key.update(method.encode())
        cache_key.update(url.encode())
        cache_key.update(json.dumps(headers).encode())
        cache_key.update(json.dumps(params).encode() if params else b'')
        cache_key.update(data.encode() if data else b'')
        cache_key.update(json.dumps(json_data).encode() if json_data else b'')
        return cache_key.hexdigest()

    def _cache_response(self, cache_key: str, response: Response) -> None:
        if len(self.cache) >= self.response_cache_max_size:
            self.cache.popitem(last=False)
        self.cache[cache_key] = response

    def _generate_auth_header(self, auth: Dict[str, str]) -> Dict[str, str]:
        if auth['type'] == 'basic':
            user_pass = f"{auth['username']}:{auth['password']}"
            basic_auth = base64.b64encode(user_pass.encode()).decode()
            return {"Authorization": f"Basic {basic_auth}"}