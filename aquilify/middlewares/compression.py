from gzip import compress as gzip_compress, decompress as gzip_decompress
from zlib import compress as deflate_compress, decompress as deflate_decompress

class CompressionMiddleware:
    def __init__(self, app):
        self.app = app
        self.compression_methods = {
            'gzip': {
                'compress': gzip_compress,
                'decompress': gzip_decompress
            },
            'deflate': {
                'compress': deflate_compress,
                'decompress': deflate_decompress
            }
        }

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope["headers"])
            supported_encodings = headers.get(b"accept-encoding", b"").split(b",")
            supported_encodings = [encoding.strip() for encoding in supported_encodings]

            for encoding in supported_encodings:
                if encoding.decode() in self.compression_methods:
                    scope["compression"] = encoding.decode()
                    break
            else:
                scope["compression"] = None

        if scope["type"] == "http":
            await self._handle_http(scope, receive, send)
        elif scope["type"] == "websocket":
            await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)

    async def _handle_http(self, scope, receive, send):
        if scope["method"] in ("PUT", "POST", "PATCH", "DELETE") and scope["compression"]:
            body = await self._receive_body(scope, receive)
            decompressed_body = self.compression_methods[scope["compression"]]['decompress'](body)
            scope["body"] = decompressed_body

        await self.app(scope, receive, await self._compress_send(send, scope["compression"]))

    async def _compress_send(self, send, compression_type):
        async def wrapper(message):
            if message.get("type") == "http.response.start":
                headers = [
                    (key, value) for key, value in message.get("headers", [])
                    if key.lower() not in (b"content-length", b"content-encoding")
                ]
                headers.append((b"content-encoding", compression_type.encode()))
                await send({
                    "type": "http.response.start",
                    "headers": headers
                })
            elif message.get("type") == "http.response.body":
                body = message.get("body", b"")
                compressed_body = self.compression_methods[compression_type]['compress'](body)
                await send({
                    "type": "http.response.body",
                    "body": compressed_body,
                    "more_body": False
                })
            else:
                await send(message)
        return wrapper

    async def _receive_body(self, scope, receive):
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
        return body
