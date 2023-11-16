import os
import secrets
import base64
from typing import Dict, Any
from datetime import datetime, timedelta

class InMemorySession:
    def __init__(self, session_id: str, data: Dict[str, Any] = None) -> None:
        self._data: Dict[str, Any] = data if data else {}
        self._session_id: str = session_id
        self._created_at: datetime = datetime.now()
        self._updated_at: datetime = self._created_at

    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._updated_at = datetime.now()

    def __delitem__(self, key: str) -> None:
        if key in self._data:
            del self._data[key]
            self._updated_at = datetime.now()

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self._updated_at = datetime.now()

    def delete(self, key):
        if key in self._data:
            del self._data[key]
            self._updated_at = datetime.now()

    def clear(self):
        self._data.clear()
        self._updated_at = datetime.now()

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

    @property
    def updated_at(self):
        return self._updated_at

class InMemorySessionMiddleware:
    def __init__(self, session_lifetime_minutes: int = 30) -> None:
        self.sessions: Dict[str, InMemorySession] = {}
        self.session_lifetime: timedelta = timedelta(minutes=session_lifetime_minutes)

    async def __call__(self, request: Any, response: Any) -> Any:
        session_id = os.environ.get('X-SESSION_ID')
        if session_id is None or session_id not in self.sessions:
            session_id = self._generate_session_id()
            os.environ['X-SESSION_ID'] = session_id
            self.sessions[session_id] = InMemorySession(session_id)

        request.scope['session'] = self.sessions[session_id]
        self._cleanup_sessions()
        return response

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
