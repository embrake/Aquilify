import secrets
import base64

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from aquilify.core import signing

from aquilify.wrappers import Request, Response
from aquilify.settings.sessions import SessionConfigSettings
from aquilify.utils.module_loading import import_string
from aquilify.settings import settings

_settings = SessionConfigSettings()

class BeforeSessionStage:
    def __init__(
        self
    ) -> None:
        self.sessions: Dict[str] = {}
        self.serializer = signing
        self.session_lifetime: timedelta = timedelta(minutes=_settings.fetch().get('session_lifetime'))
        self.cookie_name: str = _settings.fetch().get('cookie_name')

    async def __call__(self, request: Request) -> Any:
        session_id = self._get_session_id(request.cookies.get(self.cookie_name))
        if session_id is None:
            session_id = self._generate_session_id()
        storage = None
        
        for item in settings.STORAGE_BACKEND:
            if "sessions" in item and "cookie" in item["sessions"]:
                storage = item["sessions"]["cookie"]
                break
        if not storage:
            raise ValueError("Either storage SESSION_BACKEND isn't found! or may not been configured properly!")
        func = import_string(storage)
        request.scope['session'] = self.sessions.setdefault(session_id, func(session_id))
        self._cleanup_sessions()
        await self._regenerate_expired_session(request)
        return request

    def _generate_session_id(self) -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(64)).decode('utf-8')

    def _get_session_id(self, signed_session_id: Optional[str]) -> Optional[str]:
        if signed_session_id:
            try:
                return self.serializer.loads(signed_session_id, settings.SECRET_KEY, max_age=_settings.fetch().get('max_age'))
            except signing.BadSignature:
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

    async def _regenerate_expired_session(self, request: Request) -> None:
        if 'expired_session' in request.cookies:
            signed_session_id = request.cookies.get('expired_session')
            session_id = self._get_session_id(signed_session_id)
            if session_id in self.sessions:
                old_session = self.sessions.pop(session_id)
                self.sessions[old_session._session_id] = old_session

    def update_cookie_name(self, cookie_name: str) -> None:
        self.cookie_name = cookie_name

class AfterSessionStage:
    def __init__(
        self
    ) -> None:
        self.serializer = signing
        self.max_age: int = _settings.fetch().get('max_age')
        self.secure: bool = _settings.fetch().get('secure')
        self.httponly: bool = _settings.fetch().get('httponly')
        self.samesite: str = _settings.fetch().get('samesite')
        self.cookie_name: str = _settings.fetch().get('cookie_name')
        self.domain: str = getattr(settings, 'SESSION_COOKIE_DOMAIN', None)

    async def __call__(self, request: Request, response: Response) -> Any:
        session_id = request.scope['session']._session_id if 'session' in request.scope else None
        if session_id:
            await self._set_cookie(response, session_id)
            await self._regenerate_expired_session(request, response)
        return response

    async def _set_cookie(self, response: Response, session_id: str) -> None:
        signed_session_id = self.serializer.dumps(session_id, settings.SECRET_KEY)
        await response.set_cookie(
            self.cookie_name,
            signed_session_id,
            max_age=self.max_age,
            secure=self.secure,
            httponly=self.httponly,
            samesite=self.samesite,
            domain=self.domain
        )

    async def _regenerate_expired_session(self, request: Request, response: Response) -> None:
        if 'expired_session' in request.cookies:
            signed_session_id = request.cookies.get('expired_session')
            session_id = self._get_session_id(signed_session_id)
            if session_id in self.sessions:
                old_session = self.sessions.pop(session_id)
                self.sessions[old_session._session_id] = old_session
                await response.set_cookie('expired_session', '', max_age=0)
                await self._set_cookie(response, old_session._session_id)

