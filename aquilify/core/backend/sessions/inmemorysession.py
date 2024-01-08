import os
import secrets
import base64

from typing import Dict, Any
from datetime import datetime, timedelta

from aquilify.settings.sessions import SessionConfigSettings
from aquilify.settings import settings
from aquilify.utils.module_loading import import_string

_settings = SessionConfigSettings()

class InMemorySessionBeforeStage:
    def __init__(self) -> None:
        self.sessions: Dict[str] = {}
        self.session_lifetime: timedelta = timedelta(minutes=_settings.fetch().get('session_lifetime', 30))
        self.secret_key = _settings.fetch().get('secret_key', os.urandom(32))

    async def __call__(self, request: Any) -> Any:
        session_id = os.environ.get('X-SESSION_ID')
        if session_id is None or session_id not in self.sessions:
            session_id = self._generate_session_id()
            os.environ['X-SESSION_ID'] = session_id
            storage = None
            
            for item in settings.STORAGE_BACKEND:
                if "sessions" in item and "memory" in item["sessions"]:
                    storage = item["sessions"]["memory"]
                    break
            if not storage:
                raise ValueError("Either storage SESSION_BACKEND isn't found! or may not been configured properly!")
            func = import_string(storage)
            self.sessions[session_id] = func(session_id, self.secret_key)

        request.scope['session'] = self.sessions[session_id]
        self._cleanup_sessions()

    def _generate_session_id(self) -> str:
        return base64.urlsafe_b64encode(secrets.token_bytes(64)).decode('utf-8')

    def _cleanup_sessions(self) -> None:
        now = datetime.now()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if now - session.updated_at > self.session_lifetime
        ]
        for sid in expired_sessions:
            self.sessions.pop(sid)

    def invalidate_session(self, session_id: str) -> None:
        if session_id in self.sessions:
            self.sessions.pop(session_id)
            os.environ.pop('X-SESSION_ID', None)
