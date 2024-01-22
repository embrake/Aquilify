import os
import mimetypes
import gzip

try:
    import aiofiles
except ImportError:
    aiofiles = None
    
import hashlib
from datetime import datetime, timedelta

from typing import (
    Dict,
    Optional,
    Callable,
    Union,
    List,
    Any
)

from ..wrappers import (
    Response,
    Request
)

from ..responses import JsonResponse
from ..settings.core import BaseMiddlewareSettings

class StaticMiddleware:
    def __init__(
        self
    ) -> None:
        self.settings = BaseMiddlewareSettings().static_settings()
        self.static_folders: List[Any] = self.settings['static_folders']
        self.url_prefix = self.settings['url_prefix']
        self.cache_max_age: int = self.settings['cache_max_age']
        self.enable_gzip: bool = self.settings['enable_gzip']
        self.response_handler: Optional[Callable[[Response, str], Response]] = self.settings['response_handler']
        self.chunk_size: int = self.settings['chunk_size']

    async def __call__(self, request: Request, response: Response) -> Union[Response, JsonResponse]:
        try:
            if request.path.startswith(self.url_prefix):
                requested_file_path, filename = self.find_requested_file(request.path)

                if requested_file_path:
                    return await self.handle_requested_file(request, response, requested_file_path, filename)

                return JsonResponse({"error": "File not found"}, status=404)
            return response
        except Exception as e:
            return self.handle_error(str(e))

    def find_requested_file(self, path: str) -> Union[str, str]:
        for static_folder in self.static_folders:
            filename = path[len(self.url_prefix):]
            static_path = os.path.join(static_folder, filename)

            if os.path.isfile(static_path):
                return static_path, filename

        return None, None

    async def handle_requested_file(self, request: Request, response: Response, static_path: str, filename: str) -> Union[Response, JsonResponse]:
        if not self.is_supported_file(filename):
            return self.handle_error("File type not supported", status_code=400)

        mime = mimetypes.guess_type(filename)[0] or 'application/octet-stream'

        content: bytes = await self.get_file_content(static_path, request)
        response.headers["Content-Type"] = mime

        if self.enable_gzip and "gzip" in request.headers.get("accept-encoding", ""):
            content = await self.gzip_content(content)
            response.headers["Content-Encoding"] = "gzip"

        self.add_cache_headers(response)
        self.add_etag(static_path, response)
        self.__base_headers(response, static_path)

        await response.content_disposition(filename, inline=True)
        await response.last_modified(datetime.fromtimestamp(os.path.getmtime(static_path)))

        if await self.is_resource_not_modified(request, response):
            response.status_code = 304

        if self.response_handler:
            response = self.response_handler(response, static_path)

        return Response(content, headers=response.headers)

    def is_supported_file(self, filename: str) -> bool:
        allowed_extensions = ('.js', '.css')
        return os.path.splitext(filename)[1] in allowed_extensions

    def handle_error(self, error_message: str, status_code: int = 500) -> JsonResponse:
        return JsonResponse({"error": error_message}, status=status_code)

    async def get_file_content(self, file_path: str, request: Request) -> bytes:
        range_header: Optional[str] = request.headers.get("Range")
        file_size: int = os.path.getsize(file_path)
        start, end = 0, file_size - 1

        if range_header:
            parts: List[str] = range_header.replace("bytes=", "").split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1

        content: bytes = b""

        async with aiofiles.open(file_path, 'rb') as file:
            await file.seek(start)
            remaining_bytes: int = end - start + 1

            while remaining_bytes > 0:
                chunk: bytes = await file.read(min(self.chunk_size, remaining_bytes))
                if not chunk:
                    break
                content += chunk
                remaining_bytes -= len(chunk)

        return content

    async def gzip_content(self, content: bytes) -> bytes:
        return gzip.compress(content)

    def add_cache_headers(self, response: Response) -> None:
        if int(self.cache_max_age) != 0:
            response.headers["Cache-Control"] = f"max-age={self.cache_max_age}"
            expires: datetime = datetime.utcnow() + timedelta(seconds=self.cache_max_age)
            response.headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
            response.headers["Vary"] = "Accept-Encoding"
        else:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["Vary"] = "*"

    def add_etag(self, file_path: str, response: Response) -> None:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        etag: str = f'"{hash_md5.hexdigest()}"'
        response.headers["ETag"] = etag

    def __base_headers(self, response: Response, file_path: str) -> None:
        file_stats = os.stat(file_path)
        response.headers["Content-Length"] = str(file_stats.st_size)
        response.headers["Last-Modified"] = datetime.utcfromtimestamp(file_stats.st_mtime).strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.headers["Accept-Ranges"] = "bytes"

    async def is_resource_not_modified(self, request: Request, response: Response) -> bool:
        etag: Optional[str] = response.headers.get("ETag")
        return etag in request.headers.get('If-None-Match', default="")