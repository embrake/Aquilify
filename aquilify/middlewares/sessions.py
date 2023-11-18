from typing import Optional, Any, Union, Callable, Awaitable
from ..backend.sessions import CookieSessions, InMemorySession

class SESSION_MEMORY:
    pass

class SESSION_COOKIE:
    pass

class SessionInterface:
    def __init__(self, storage_type:  Optional[Union[SESSION_MEMORY, SESSION_COOKIE]]= 'cookies', session_middleware: Optional[Union[CookieSessions, InMemorySession]] = None):
        self.storage_type: str = storage_type
        self.session_middleware: Optional[CookieSessions] = session_middleware
        self.supported_sessions = {
            'cookies': CookieSessions,
            'memory': InMemorySession
        }

    async def __call__(self, request: Any, response: Any) -> Any:
        selected_session_type = self.supported_sessions.get(self.storage_type)

        if not selected_session_type:
            raise ValueError("Unsupported Storage Type. Only 'cookies' and 'memory' storage types are supported.")

        if self.session_middleware and not isinstance(self.session_middleware, selected_session_type):
            raise ValueError(f"{selected_session_type.__name__} instance not provided for '{self.storage_type}' storage type.")

        if not self.session_middleware:
            raise ValueError(f"No session middleware instance provided for '{self.storage_type}' storage type.")

        return await self.session_middleware(request, response)
