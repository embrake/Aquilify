import http
import typing
import warnings

__all__ = ("HTTPException", "WebSocketException")


class HTTPException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: typing.Optional[str] = None,
        headers: typing.Optional[dict] = None,
    ) -> None:
        if detail is None:
            detail = http.HTTPStatus(status_code).phrase
        self.status_code = status_code
        self.detail = detail
        self.headers = headers

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"
