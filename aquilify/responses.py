from .wrappers import Response as BaseResponse

from typing import (
    Dict,
    Optional,
    Union,
    Callable,
    Any,
    List
)

from urllib.parse import (
    urlencode, 
    urlsplit, 
    urlunsplit, 
    quote
)

import os
import gzip
import io
import time
import json
import hashlib

from datetime import datetime, timedelta
from mimetypes import MimeTypes

class PlainTextResponse(BaseResponse):
    def __init__(
        self,
        content: Union[str, bytes, Callable, None] = None,
        status: Optional[int] = 200,
        headers: Optional[Dict[str, Union[str, int]]] = None,
        content_type: str = 'text/plain',
        encoding: Optional[str] = 'utf-8',
    ) -> None:
        """
        Create a plain text response.

        Args:
            content (Union[str, bytes, Callable, None]): The response content.
            status (Optional[int]): The HTTP status code (default is 200).
            headers (Optional[Dict[str, Union[str, int]]]): Additional headers for the response.
            content_type (str): The content type for the response (default is 'text/plain').
            encoding (Optional[str]): The character encoding for text content (default is 'utf-8').

        """
        super().__init__(content, status, headers)
        self.headers.setdefault('Content-Type', content_type)
        if encoding:
            self.headers['Content-Type'] += f'; charset={encoding}'

class JsonResponse(BaseResponse):
    def __init__(
        self,
        content: Union[Dict, Callable, None] = {},
        status: Optional[int] = 200,
        headers: Optional[Dict[str, Union[str, int]]] = None,
        content_type: str = 'application/json',
        encoding: Optional[str] = 'utf-8',
        validate: Optional[bool] = False,
    ) -> None:
        """
        Create a JSON response.

        Args:
            content (Union[Dict, Callable, None]): The response content (as a dictionary).
            status (Optional[int]): The HTTP status code (default is 200).
            headers (Optional[Dict[str, Union[str, int]]]): Additional headers for the response.
            content_type (str): The content type for the response (default is 'application/json').
            encoding (Optional[str]): The character encoding for JSON content (default is 'utf-8').
            validate (Optional[bool]): Whether to validate the JSON data (default is False).

        """
        if validate:
            try:
                json.dumps(content)
            except ValueError:
                raise ValueError("Invalid JSON content")

        super().__init__(json.dumps(content, ensure_ascii=False), status, headers)
        self.headers.setdefault('Content-Type', f'{content_type}; charset={encoding}')
        
    def __str__(self) -> str:
        return self.content
    
    def __repr__(self) -> str:
        return "JsonResponse(content = %s, status = %s, headers = %s, encoding = %s)" %(
            self.content,
            self.status_code,
            self.headers,
            self.encoding
        )

class HTMLResponse(BaseResponse):
    def __init__(
        self,
        content: Union[str, bytes, Callable, None] = None,
        status: Optional[int] = 200,
        headers: Optional[Dict[str, Union[str, int]]] = None,
        content_type: str = 'text/html',
        encoding: Optional[str] = 'utf-8',
    ) -> None:
        """
        Create an HTML response.

        Args:
            content (Union[str, bytes, Callable, None]): The response content.
            status (Optional[int]): The HTTP status code (default is 200).
            headers (Optional[Dict[str, Union[str, int]]]): Additional headers for the response.
            content_type (str): The content type for the response (default is 'text/html').
            encoding (Optional[str]): The character encoding for text content (default is 'utf-8').

        """
        super().__init__(content, status, headers)
        self.headers.setdefault('Content-Type', f'{content_type}; charset={encoding}')
        
    def __str__(self):
        return f"HTMLResponse: Status={self.status_code}, Content-Type={self.content_type}, Content-Length={len(self.content)}"
    
    def __repr__(self) -> str:
        return f"HTMLResponse: Status={self.status_code}, Content-Type={self.content_type}, Content-Length={len(self.content)}"

class RedirectResponse(BaseResponse):
    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: Optional[Dict[str, Union[str, int]]] = None,
        query_params: Optional[Dict[str, Union[str, int]]] = None,
        anchor: Optional[str] = None,
        delay: float = 0.0,
        content: Optional[str] = None,
    ) -> None:
        super().__init__(
            content=content or b"", status_code=status_code, headers=headers or {}
        )

        if delay > 0:
            time.sleep(delay)

        parsed_url = urlsplit(url)

        if query_params:
            parsed_url = self._add_query_params(parsed_url, query_params)

        if anchor:
            parsed_url = self._add_anchor(parsed_url, anchor)

        self.headers["Location"] = self._quote_url(parsed_url)

    def _add_query_params(
        self, parsed_url, query_params: Dict[str, Union[str, int]]
    ) -> str:
        query_dict = self._parse_query(parsed_url.query)
        query_dict.update(query_params)

        encoded_query = urlencode(query_dict, doseq=True)
        modified_url = parsed_url._replace(query=encoded_query)
        return modified_url

    def _add_anchor(self, parsed_url, anchor: str) -> str:
        modified_url = parsed_url._replace(fragment=quote(anchor))
        return modified_url

    def _parse_query(self, query: str) -> Dict[str, List[str]]:
        parsed_query = {}
        if query:
            for key, value in map(lambda x: x.split('=', 1), query.split('&')):
                parsed_query.setdefault(key, []).append(value)
        return parsed_query

    def _quote_url(self, parsed_url) -> str:
        return urlunsplit(
            (parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.query, parsed_url.fragment)
        )
    

class FileResponse(BaseResponse):
    def __init__(
        self,
        file_path: str,
        filename: Optional[str] = None,
        status: Optional[int] = 200,
        headers: Optional[Dict[str, Union[str, int]]] = None,
        content_type: Optional[str] = None,
        inline: bool = False,
        buffer_size: int = 8192,
        chunked: bool = False,
        compress: bool = False,
        max_age: int = 3600,
        stream_file: bool = False,
        content_disposition: Optional[str] = None,
    ) -> None:
        super().__init__(content=None, status_code=status, headers=headers or {})
        self.buffer_size = buffer_size

        if not os.path.exists(file_path):
            raise FileNotFoundError("File not found")

        if not filename:
            filename = os.path.basename(file_path)

        if not content_type:
            content_type, _ = MimeTypes().guess_type(filename)

        disposition_type = content_disposition or ("inline" if inline else "attachment")
        self.headers["Content-Disposition"] = f'{disposition_type}; filename="{quote(filename)}'
        self.headers["Content-Type"] = content_type

        last_modified_time = os.path.getmtime(file_path)
        last_modified = datetime.utcfromtimestamp(last_modified_time).strftime('%a, %d %b %Y %H:%M:%S GMT')
        self.headers["Last-Modified"] = last_modified

        with open(file_path, "rb") as file:
            file_data = file.read()
            etag = hashlib.md5(file_data).hexdigest()
            self.headers["ETag"] = etag

        if stream_file:
            self._stream_file(file_path, buffer_size)
        else:
            if chunked:
                self._read_file_chunked(file_path, buffer_size)
            else:
                self._read_file_entirely(file_path)

        if compress:
            self._compress_content()

        self.enable_caching(max_age)

    def _stream_file(self, file_path: str, buffer_size: int) -> None:
        self.headers["Transfer-Encoding"] = "chunked"

        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(buffer_size)
                if not chunk:
                    break
                chunk_size = hex(len(chunk))[2:]
                self.content += (f"{chunk_size}\r\n{chunk}\r\n").encode("utf-8")

        self.content += b"0\r\n\r\n"

    def _read_file_chunked(self, file_path: str, buffer_size: int) -> None:
        self.headers["Transfer-Encoding"] = "chunked"

        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(buffer_size)
                if not chunk:
                    break
                chunk_size = hex(len(chunk))[2:]
                self.content += (f"{chunk_size}\r\n{chunk}\r\n").encode("utf-8")

        self.content += b"0\r\n\r\n"

    def _read_file_entirely(self, file_path: str) -> None:
        with open(file_path, "rb") as file:
            self.content = file.read()

        self.headers["Content-Length"] = str(len(self.content))

    def _compress_content(self) -> None:
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb") as f:
            f.write(self.content)
        compressed_content = buffer.getvalue()
        self.headers["Content-Encoding"] = "gzip"
        self.content = compressed_content

    def is_not_modified(self, request_headers: Dict[str, str], file_path: str) -> bool:
        if "If-None-Match" in request_headers and request_headers["If-None-Match"] == self.headers.get("ETag"):
            return True
        if "If-Modified-Since" in request_headers:
            try:
                client_timestamp = datetime.strptime(request_headers["If-Modified-Since"], '%a, %d %b %Y %H:%M:S GMT')
                file_timestamp = datetime.utcfromtimestamp(os.path.getmtime(file_path))
                if file_timestamp <= client_timestamp:
                    return True
            except ValueError:
                pass
        return False

    def handle_range_request(self, request_headers: Dict[str, str], file_path: str) -> Union[None, int]:
        if "Range" in request_headers:
            byte_range = request_headers["Range"]
            start, end = byte_range.strip("bytes=").split("-")
            start = int(start) if start else 0
            end = int(end) if end else os.path.getsize(file_path) - 1

            if start < 0 or end >= os.path.getsize(file_path) or start > end:
                return 416

            self.status_code = 206
            self.headers["Content-Range"] = f"bytes {start}-{end}/{os.path.getsize(file_path)}"
            self.headers["Content-Length"] = str(end - start + 1)
            self.content = self._stream_range(file_path, start, end, self.buffer_size)
            return None

    def _stream_range(self, file_path: str, start: int, end: int, buffer_size: int) -> Any:
        with open(file_path, "rb") as file:
            file.seek(start)
            while start <= end:
                chunk_size = min(end - start + 1, buffer_size)
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
                start += len(chunk)

    def set_headers_for_conditional_request(self) -> None:
        self.headers["Date"] = format_date_time(datetime.utcnow())
        self.headers["Cache-Control"] = "public, max-age=0"

    def enable_caching(self, max_age: int = 3600) -> None:
        self.headers["Cache-Control"] = f"public, max-age={max_age}"
        expires = datetime.utcnow() + timedelta(seconds=max_age)
        self.headers["Expires"] = format_date_time(expires)

def format_date_time(dt: datetime) -> str:
    """
    Format a datetime object to the RFC 1123 date-time format.
    Args:
        dt (datetime): The datetime object to format.
    Returns:
        str: The formatted date-time string.
    """
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    months = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return f"{days[dt.weekday()]}, {dt.day:02d} {months[dt.month]} {dt.year} {dt.strftime('%H:%M:%S')} GMT"