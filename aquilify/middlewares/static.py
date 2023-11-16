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
    List
)

from ..wrappers import (
    Response,
    Request
)

from ..responses import JsonResponse

class StaticMiddleware:
    def __init__(
        self,
        static_folders: Optional[Dict[str, str]] = None,
        cache_max_age: int = 3600,
        enable_gzip: bool = True,
        response_handler: Optional[Callable[[Response, str], Response]] = None,
        chunk_size: int = 65536
    ) -> None:
        self.static_folders: Dict[str, str] = static_folders if static_folders is not None else {'/static/': os.path.join(os.getcwd(), 'static')}
        self.cache_max_age: int = cache_max_age
        self.enable_gzip: bool = enable_gzip
        self.response_handler: Optional[Callable[[Response, str], Response]] = response_handler
        self.chunk_size: int = chunk_size

    async def __call__(self, request: Request, response: Response) -> Union[Response, JsonResponse]:
        path: str = request.path

        for url_prefix, static_folder in self.static_folders.items():
            if path.startswith(url_prefix):
                filename: str = path[len(url_prefix):]
                static_path: str = os.path.join(static_folder, filename)

                if not os.path.exists(static_path) or not os.access(static_path, os.R_OK):
                    return JsonResponse({"error": "Invalid path or permission error"}, status=400)

                if os.path.isfile(static_path):
                    mime, _ = mimetypes.guess_type(static_path)
                    
                    if mime:
                        content: bytes = await self.get_file_content(static_path, request)
                        response.headers["Content-Type"] = mime

                        if self.enable_gzip and "gzip" in await request.headers.get("accept-encoding", default=""):
                            content = await self.gzip_content(content)
                            response.headers["Content-Encoding"] = "gzip"

                        self.add_cache_headers(response)
                        self.add_etag(static_path, response)
                        self.__base_headers(response, static_path)

                        await response.content_disposition(filename, inline=True)
                        await response.last_modified(datetime.fromtimestamp(os.path.getmtime(static_path)))

                        if await self.is_resource_not_modified(request, response):
                            return JsonResponse({"detail": "Not Modified"}, status=304)

                        if self.response_handler:
                            response = self.response_handler(response, static_path)

                        if request.method == 'GET':
                            return Response(content, headers=response.headers)
                        else:
                            return response

                elif os.path.isdir(static_path):
                    return JsonResponse({"error": "Requested path is a directory"}, status=400)

        return response

    async def get_file_content(self, file_path: str, request: Request) -> bytes:
        range_header: Optional[str] = await request.headers.get("Range")
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
        response.headers["Cache-Control"] = f"max-age={self.cache_max_age}"
        expires: datetime = datetime.utcnow() + timedelta(seconds=self.cache_max_age)
        response.headers["Expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        response.headers["Vary"] = "Accept-Encoding"

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
        return etag in await request.headers.get('If-None-Match', default="")

    async def handle_not_modified(self, response: Response) -> Response:
        response.status_code = 304
        response.content = b""
        return response
