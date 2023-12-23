import secrets
import base64
import json
import os

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
try:
    from itsdangerous import URLSafeSerializer, BadSignature
except ImportError:
    URLSafeSerializer, BadSignature = None, None

from ....wrappers import Request, Response
from ....settings.sessions import SessionConfigSettings

class SessionData(Dict[str, Any]):
    pass

_settings = SessionConfigSettings()

_serilizer = URLSafeSerializer(_settings.fetch().get('secret_key'))

CACHE_DIR = ".aquilify/cache/session/cookie/"
CONFIG_FILE = ".aquilify/cache/session/config.json"
AQUILIFY_CONFIG_FILE = ".aquilify/config.json"

class Session:
    def __init__(self, session_id: str) -> None:
        self._data: SessionData = {}
        self._session_id: str = session_id
        self._created_at: datetime = datetime.now()
        self._updated_at: datetime = self._created_at
        self._cache_file = os.path.join(CACHE_DIR, f"{self._session_id}.cache")

        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

        self._update_config()

        self._load_from_cache()
        self._update_aquilify_config()

    def _serialize(self, data: Dict[str, Any]) -> str:
        return json.dumps(data)

    def _deserialize(self, data: str) -> Dict[str, Any]:
        return json.loads(data)

    def __getitem__(self, key: str) -> Any:
        encrypted_data = self._data.get(key)
        if encrypted_data:
            return self._decrypt(encrypted_data)
        return None

    def __setitem__(self, key: str, value: Any) -> None:
        encrypted_value = self._encrypt(str(value))
        self._data[key] = encrypted_value
        self._save_to_cache()
        self._updated_at = datetime.now()

    def __delitem__(self, key: str) -> None:
        if key in self._data:
            del self._data[key]
            self._updated_at = datetime.now()

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key, default=None):
        encrypted_data = self._data.get(key)
        if encrypted_data:
            return self._decrypt(encrypted_data)
        return None

    def set(self, key, value):
        encrypted_value = self._encrypt(str(value))
        self._data[key] = encrypted_value
        self._save_to_cache()
        self._updated_at = datetime.now()

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
    
    def _encrypt(self, data: str) -> str:
        encrypted = []
        key = _settings.fetch().get('secret_key').encode() 
        data_bytes = data.encode()
        for i in range(len(data_bytes)):
            encrypted.append(chr(data_bytes[i] ^ key[i % len(key)]))
        return base64.urlsafe_b64encode("".join(encrypted).encode()).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        decrypted = []
        key = _settings.fetch().get('secret_key').encode()
        decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
        for i in range(len(decoded_data)):
            decrypted.append(chr(decoded_data[i] ^ key[i % len(key)]))
        return "".join(decrypted)

    def _load_from_cache(self) -> None:
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, "r") as file:
                    encrypted_data = file.read()
                    decrypted_data = self._decrypt(encrypted_data)
                    self._data = self._deserialize(decrypted_data)
        except Exception as e:
            print(f"Error loading cache: {e}")

    def _save_to_cache(self) -> None:
        try:
            with open(self._cache_file, "w") as file:
                encrypted_data = self._encrypt(self._serialize(self._data))
                file.write(encrypted_data)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _update_config(self) -> None:
        try:
            with open(CONFIG_FILE, "r") as file:
                config_data = json.load(file)
        except FileNotFoundError:
            config_data = {"$session": []}

        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        session_entry = {
            "session_id": self._session_id,
            "backend": "cookie",
            "cache": True,
            "encryption": "base64",
            "timestamp": time_stamp
        }

        session_ids = [entry['session_id'] for entry in config_data['$session']]
        if self._session_id not in session_ids:
            config_data["$session"].append(session_entry)

        with open(CONFIG_FILE, "w") as file:
            json.dump(config_data, file, indent=4)

    def _update_aquilify_config(self) -> None:
        session_entry = {
            "backend": "cookie",
            "cache": True,
            "encryption": "base64",
            "$path": [os.path.join(CACHE_DIR, "config.json")]
        }

        if os.path.exists(AQUILIFY_CONFIG_FILE):
            with open(AQUILIFY_CONFIG_FILE, "r") as aquilify_file:
                aquilify_config = json.load(aquilify_file)
        else:
            aquilify_config = {}

        session_exists = False
        if "$session" in aquilify_config:
            for entry in aquilify_config["$session"]:
                if entry.get("backend") == "cookie":
                    session_exists = True
                    break

        if not session_exists:
            existing_compression = aquilify_config.get("$compression", [])

            if "$session" not in aquilify_config:
                aquilify_config["$session"] = []
            aquilify_config["$session"].append(session_entry)

            with open(AQUILIFY_CONFIG_FILE, "w") as aquilify_file:
                aquilify_config["$compression"] = existing_compression
                json.dump(aquilify_config, aquilify_file, indent=4)

    @property
    def session_id(self):
        return self._session_id

    @property
    def created_at(self):
        return self._created_at

    @property
    def updated_at(self):
        return self._updated_at
    
    def clear_cache(self) -> None:
        try:
            if os.path.exists(self._cache_file):
                os.remove(self._cache_file)
        except Exception as e:
            print(f"Error clearing cache: {e}")

class BeforeSessionStage:
    def __init__(
        self
    ) -> None:
        self.sessions: Dict[str, Session] = {}
        self.serializer: URLSafeSerializer = _serilizer
        self.session_lifetime: timedelta = timedelta(minutes=_settings.fetch().get('session_lifetime'))
        self.cookie_name: str = _settings.fetch().get('cookie_name')

    async def __call__(self, request: Request) -> Any:
        session_id = self._get_session_id(request.cookies.get(self.cookie_name))
        if session_id is None:
            session_id = self._generate_session_id()
        request.scope['session'] = self.sessions.setdefault(session_id, Session(session_id))
        self._cleanup_sessions()
        await self._regenerate_expired_session(request)
        return request

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
        self.serializer: URLSafeSerializer = _serilizer
        self.max_age: int = _settings.fetch().get('max_age')
        self.secure: bool = _settings.fetch().get('secure')
        self.httponly: bool = _settings.fetch().get('httponly')
        self.samesite: str = _settings.fetch().get('samesite')
        self.cookie_name: str = _settings.fetch().get('cookie_name')

    async def __call__(self, request: Request, response: Response) -> Any:
        session_id = request.scope['session']._session_id if 'session' in request.scope else None
        if session_id:
            await self._set_cookie(response, session_id)
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

    async def _regenerate_expired_session(self, request: Request, response: Response) -> None:
        if 'expired_session' in request.cookies:
            signed_session_id = request.cookies.get('expired_session')
            session_id = self._get_session_id(signed_session_id)
            if session_id in self.sessions:
                old_session = self.sessions.pop(session_id)
                self.sessions[old_session._session_id] = old_session
                await response.set_cookie('expired_session', '', max_age=0)
                await self._set_cookie(response, old_session._session_id)

