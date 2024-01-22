import json
import typing
from http import cookies as http_cookies
from urllib.parse import parse_qs

import anyio

from ..utils._utils import AwaitableOrContextManager, AwaitableOrContextManagerWrapper
from ..datastructure.core import URL, Address, FormData, Headers, State
from ..exception.http_exception import HTTPException
from ..datastructure.formparser import FormParser, MultiPartException, MultiPartParser
from ..datastructure.user_agent import UserAgentParser
from ..types import Message, Receive, Scope, Send

try:
    from multipart.multipart import parse_options_header
except ModuleNotFoundError: 
    parse_options_header = None


SERVER_PUSH_HEADERS_TO_COPY = {
    "accept",
    "accept-encoding",
    "accept-language",
    "cache-control",
    "user-agent",
}


def cookie_parser(cookie_string: str) -> typing.Dict[str, str]:
    cookie_dict: typing.Dict[str, str] = {}
    for chunk in cookie_string.split(";"):
        if "=" in chunk:
            key, val = chunk.split("=", 1)
        else:
            key, val = "", chunk
        key, val = key.strip(), val.strip()
        if key or val:
            cookie_dict[key] = http_cookies._unquote(val)
    return cookie_dict


class ClientDisconnect(Exception):
    pass


class HTTPConnection(typing.Mapping[str, typing.Any]):

    def __init__(self, scope: Scope, receive: typing.Optional[Receive] = None) -> None:
        assert scope["type"] in ("http", "websocket")
        self.scope = scope

    def __getitem__(self, key: str) -> typing.Any:
        return self.scope[key]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.scope)

    def __len__(self) -> int:
        return len(self.scope)
    
    __eq__ = object.__eq__ 
    __hash__ = object.__hash__

    @property
    def app(self) -> typing.Any:
        return self.scope["app"]

    @property
    def url(self) -> URL:
        if not hasattr(self, "_url"):
            self._url = URL(scope=self.scope)
        return self._url

    @property
    def base_url(self) -> URL:
        if not hasattr(self, "_base_url"):
            base_url_scope = dict(self.scope)
            base_url_scope["path"] = "/"
            base_url_scope["query_string"] = b""
            base_url_scope["root_path"] = base_url_scope.get(
                "app_root_path", base_url_scope.get("root_path", "")
            )
            self._base_url = URL(scope=base_url_scope)
        return self._base_url

    @property
    def headers(self) -> Headers:
        if not hasattr(self, "_headers"):
            self._headers = Headers(scope=self.scope)
        return self._headers
    
    @property
    def origin(self):
        return self.headers.get('origin')
    
    @property
    def remote_addr(self) -> str:
        return self.scope.get('client', ('',))[0]
    
    @property
    def scheme(self) -> str:
        return self.scope.get('scheme', 'http')
    
    @property
    def server(self) -> typing.Dict[str, str]:
        return {
            'server_protocol': self.scope.get('server_protocol', ''),
            'server_name': self.scope.get('server_name', ''),
            'server_port': self.scope.get('server_port', ''),
        }
    
    @property
    def authorization(self) -> typing.Optional[str]:
        return self.headers.get('authorization')
    
    @property
    def user_agent(self) -> UserAgentParser:
        return UserAgentParser(self.headers.get('user-agent', ''))

    @property
    def referer(self) -> str:
        return self.headers.get('referer', '')

    @property
    def accept(self) -> str:
        return self.headers.get('accept', '')
    
    @property
    def host(self) -> str:
        return self.headers.get('host')
    
    @property
    def path(self) -> str:
        return self.scope.get('path', '/')

    @property
    def path_param(self) -> typing.Dict[str, typing.Any]:
        return self.scope.get("path_params", {})

    @property
    def cookies(self) -> typing.Dict[str, str]:
        if not hasattr(self, "_cookies"):
            cookies: typing.Dict[str, str] = {}
            cookie_header = self.headers.get("cookie")

            if cookie_header:
                cookies = cookie_parser(cookie_header)
            self._cookies = cookies
        return self._cookies

    @property
    def client(self) -> typing.Optional[Address]:
        # client is a 2 item tuple of (host, port), None or missing
        host_port = self.scope.get("client")
        if host_port is not None:
            return Address(*host_port)
        return None

    @property
    def session(self) -> typing.Dict[str, typing.Any]:
        assert (
            "session" in self.scope
        ), "SessionMiddleware must be installed to access request.session"
        return self.scope["session"]

    @property
    def auth(self) -> typing.Any:
        assert (
            "auth" in self.scope
        ), "AuthenticationMiddleware must be installed to access request.auth"
        return self.scope["auth"]

    @property
    def user(self) -> typing.Any:
        assert (
            "user" in self.scope
        ), "AuthenticationMiddleware must be installed to access request.user"
        return self.scope["user"]

    @property
    def state(self) -> State:
        if not hasattr(self, "_state"):
            self.scope.setdefault("state", {})
            self._state = State(self.scope["state"])
        return self._state

async def empty_receive() -> typing.NoReturn:
    raise RuntimeError("Receive channel has not been made available")


async def empty_send(message: Message) -> typing.NoReturn:
    raise RuntimeError("Send channel has not been made available")


class Request(HTTPConnection):
    _form: typing.Optional[FormData]

    def __init__(
        self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send
    ):
        super().__init__(scope)
        assert scope["type"] == "http"
        self._receive = receive
        self._send = send
        self._stream_consumed = False
        self._is_disconnected = False
        self._form = None
        self.path_params = None
        self.query_params: typing.Dict[str, str] = {}
        self.context: typing.Dict[str, str] = {}
        self.executed_middlewares = set()

    @property
    def method(self) -> str:
        return self.scope["method"]
    
    @property
    def args(self) -> typing.Dict[str, str]:
        self._parse_query_params()
        return self.query_params

    @property
    def receive(self) -> Receive:
        return self._receive

    async def stream(self) -> typing.AsyncGenerator[bytes, None]:
        if hasattr(self, "_body"):
            yield self._body
            yield b""
            return
        if self._stream_consumed:
            raise RuntimeError("Stream consumed")
        self._stream_consumed = True
        while True:
            message = await self._receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    yield body
                if not message.get("more_body", False):
                    break
            elif message["type"] == "http.disconnect":
                self._is_disconnected = True
        yield b""

    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            chunks: "typing.List[bytes]" = []
            async for chunk in self.stream():
                chunks.append(chunk)
            self._body = b"".join(chunks)
        return self._body

    async def json(self) -> typing.Any:
        if not hasattr(self, "_json"):
            body = await self.body()
            self._json = json.loads(body)
        return self._json
    
    def _parse_query_params(self):
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        self.query_params = {k: v[0] for k, v in parse_qs(query_string).items()}

    async def _get_form(
        self,
        *,
        max_files: typing.Union[int, float] = 1000,
        max_fields: typing.Union[int, float] = 1000,
    ) -> FormData:
        if self._form is None:
            assert (
                parse_options_header is not None
            ), "The `python-multipart` library must be installed to use form parsing."
            content_type_header = self.headers.get("Content-Type")
            content_type: bytes
            content_type, _ = parse_options_header(content_type_header)
            if content_type == b"multipart/form-data":
                try:
                    multipart_parser = MultiPartParser(
                        self.headers,
                        self.stream(),
                        max_files=max_files,
                        max_fields=max_fields,
                    )
                    self._form = await multipart_parser.parse()
                except MultiPartException as exc:
                    if "app" in self.scope:
                        raise HTTPException(status_code=400, detail=exc.message)
                    raise exc
            elif content_type == b"application/x-www-form-urlencoded":
                form_parser = FormParser(self.headers, self.stream())
                self._form = await form_parser.parse()
            else:
                self._form = FormData()
        return self._form

    def form(
        self,
        *,
        max_files: typing.Union[int, float] = 1000,
        max_fields: typing.Union[int, float] = 1000,
    ) -> AwaitableOrContextManager[FormData]:
        return AwaitableOrContextManagerWrapper(
            self._get_form(max_files=max_files, max_fields=max_fields)
        )

    async def close(self) -> None:
        if self._form is not None:
            await self._form.close()

    async def is_disconnected(self) -> bool:
        if not self._is_disconnected:
            message: Message = {}

            with anyio.CancelScope() as cs:
                cs.cancel()
                message = await self._receive()

            if message.get("type") == "http.disconnect":
                self._is_disconnected = True

        return self._is_disconnected

    async def send_push_promise(self, path: str) -> None:
        if "http.response.push" in self.scope.get("extensions", {}):
            raw_headers: "typing.List[typing.Tuple[bytes, bytes]]" = []
            for name in SERVER_PUSH_HEADERS_TO_COPY:
                for value in self.headers.getlist(name):
                    raw_headers.append(
                        (name.encode("latin-1"), value.encode("latin-1"))
                    )
            await self._send(
                {"type": "http.response.push", "path": path, "headers": raw_headers}
            )
