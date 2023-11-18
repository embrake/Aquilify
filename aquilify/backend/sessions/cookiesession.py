import secrets
import base64

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
try:
    from itsdangerous import URLSafeSerializer, BadSignature
except ImportError:
    URLSafeSerializer, BadSignature = None, None

from ...wrappers import Request, Response


class SessionData(Dict[str, Any]):
    pass


class Session:
    def __init__(self, session_id: str) -> None:
        self._data: SessionData = {}
        self._session_id: str = session_id
        self._created_at: datetime = datetime.now()

    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        if key in self._data:
            del self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def delete(self, key):
        if key in self._data:
            del self._data[key]

    def clear(self):
        self._data.clear()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    @property
    def session_id(self):
        return self._session_id

    @property
    def created_at(self):
        return self._created_at

class CookieSessions:
    def __init__(
        self,
        secret_key: str,
        session_lifetime_minutes: int = 30,
        max_age: int = 1800,
        secure: bool = True,
        httponly: bool = True,
        samesite: str = 'Lax',
        cookie_name: str = '_sessionid'
    ) -> None:
        self.sessions: Dict[str, Session] = {}
        self.serializer: URLSafeSerializer = URLSafeSerializer(secret_key)
        self.session_lifetime: timedelta = timedelta(minutes=session_lifetime_minutes)
        self.max_age: int = max_age
        self.secure: bool = secure
        self.httponly: bool = httponly
        self.samesite: str = samesite
        self.cookie_name: str = cookie_name

    async def __call__(self, request: Request, response: Response) -> Any:
        session_id = self._get_session_id(request.cookies.get(self.cookie_name))
        if session_id is None:
            session_id = self._generate_session_id()
        request.scope['session'] = self.sessions.setdefault(session_id, Session(session_id))
        await self._set_cookie(response, session_id)
        self._cleanup_sessions()
        await self._regenerate_expired_session(request, response)
        return response

    async def _set_cookie(self, response: Response, session_id: str) -> None:
        signed_session_id = self.serializer.dumps(session_id)
        await response.set_cookie(
            self.cookie_name,
            signed_session_id,
            max_age=self.max_age,
            secure=self.secure,
            httponly=self.httponly,
            samesite=self.samesite
        )

    def _generate_session_id(self) -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(64)).decode('utf-8')

    def _get_session_id(self, signed_session_id: Optional[str]) -> Optional[str]:
        if signed_session_id:
            try:
                return self.serializer.loads(signed_session_id)
            except BadSignature:
                pass
        return None

    def _cleanup_sessions(self) -> None:
        now = datetime.now()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if now - session._created_at > self.session_lifetime
        ]
        for sid in expired_sessions:
            self.sessions.pop(sid)

    async def _regenerate_expired_session(self, request: Request, response: Response) -> None:
        if 'expired_session' in request.cookies:
            signed_session_id = request.cookies.get('expired_session')
            session_id = self._get_session_id(signed_session_id)
            if session_id in self.sessions:
                old_session = self.sessions.pop(session_id)
                self.sessions[old_session._session_id] = old_session
                await response.set_cookie('expired_session', '', max_age=0)
                await self._set_cookie(response, old_session._session_id)

    def invalidate(self, request: Request, response: Response) -> None:
        session_id = request.cookies.get(self.cookie_name)
        if session_id in self.sessions:
            self.sessions.pop(session_id)
            response.delete_cookie(self.cookie_name)

    def update_cookie_settings(
        self,
        max_age: Optional[int] = None,
        secure: Optional[bool] = None,
        httponly: Optional[bool] = None,
        samesite: Optional[str] = None,
        cookie_name: Optional[str] = None
    ) -> None:
        if max_age is not None:
            self.max_age = max_age
        if secure is not None:
            self.secure = secure
        if httponly is not None:
            self.httponly = httponly
        if samesite is not None:
            self.samesite = samesite
        if cookie_name is not None:
            self.cookie_name = cookie_name
