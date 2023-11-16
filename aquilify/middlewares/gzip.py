import zlib
from io import BytesIO
from typing import List, Callable, Optional
from ..wrappers import Response, Request

class GzipMiddleware:
    def __init__(
        self,
        compress_level: int = 6,
        min_length: int = 500,
        exclude_content_types: Optional[List[str]] = None,
        condition: Optional[Callable[[str, int], bool]] = None,
        skip_paths: Optional[List[str]] = None,
    ):
        self.compress_level = compress_level
        self.min_length = min_length
        self.exclude_content_types = exclude_content_types or []
        self.condition = condition or self.default_condition
        self.skip_paths = skip_paths or []

    async def __call__(self, request: Request, response: Response):
        accept_encoding = await request.headers.get("accept-encoding", "")
        content_length = response.headers.get("content-length")
        content_type = response.headers.get("content-type")
        path = request.path

        should_compress = (
            "gzip" in accept_encoding
            and content_length
            and self.condition(content_type, int(content_length))
            and content_type not in self.exclude_content_types
            and not any(path.startswith(skip_path) for skip_path in self.skip_paths)
        )

        if should_compress:
            if response.streaming:
                response = await self._gzip_stream(response)
            else:
                response = await self._gzip_compress(response)

        return response

    async def _gzip_compress(self, response):
        if not response.content:
            return response

        try:
            compressed_data = self._compress_data(response.content)
            if compressed_data:
                compressed_buffer = BytesIO(compressed_data)
                response.content = compressed_buffer.getvalue()

                # Update necessary headers for compressed response
                response.headers["content-encoding"] = "gzip"
                response.headers["vary"] = "Accept-Encoding"
                response.headers["content-length"] = str(len(response.content))
        except Exception as e:
            # Handle compression failure
            print(f"Compression failed: {e}")

        return response

    def _compress_data(self, content: bytes) -> Optional[bytes]:
        compressed_data = zlib.compress(content, self.compress_level)
        return compressed_data

    async def _gzip_stream(self, response):
        try:
            # Compressing streaming response
            async for chunk in response.content:
                compressed_chunk = self._compress_data(chunk)
                if compressed_chunk:
                    response.send(compressed_chunk)
        except Exception as e:
            # Handle compression failure for streaming response
            print(f"Streaming compression failed: {e}")

        return response

    @staticmethod
    def default_condition(content_type: str, content_length: int) -> bool:
        return content_type.startswith('text/') or content_length > 1024
