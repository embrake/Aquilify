import os
import json
import secrets
import hashlib
import base64
import asyncio

try:
    import aiofiles
except ImportError:
    aiofiles = None

import http.client

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable, List, Tuple

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

class SessionManager:
    def __init__(
        self,
        secret_key: Optional[str] = None,
        session_folder: str = 'sessions',
        session_lifetime: timedelta = timedelta(hours=1),
        encryption_key: Optional[str] = None,
        timeout_handler: Optional[Callable[[Dict[str, Any]], None]] = None,
        rotate_sessions: bool = False,
        fingerprint_sessions: bool = False,
        user_agent_verification: bool = False,
        session_id_prefix: str = ''
    ) -> None:

        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.session_folder = session_folder
        self.session_lifetime = session_lifetime
        self.loaded_session = None
        self.encryption_key = encryption_key
        self.timeout_handler = timeout_handler
        self.rotate_sessions = rotate_sessions
        self.fingerprint_sessions = fingerprint_sessions
        self.user_agent_verification = user_agent_verification
        self.session_id_prefix = session_id_prefix

        if not os.path.exists(self.session_folder):
            os.makedirs(self.session_folder)

    def generate_session_id(self) -> str:
        return self.session_id_prefix + secrets.token_hex(32)

    def regenerate_session_id(self, session_id: str) -> str:
        new_session_id = self.generate_session_id()
        old_session_file = os.path.join(self.session_folder, session_id)
        new_session_file = os.path.join(self.session_folder, new_session_id)

        if os.path.exists(old_session_file):
            os.rename(old_session_file, new_session_file)

        return new_session_id
    
    def encrypt(data, encryption_key):
        data_bytes = data.encode()
        encrypted_data = base64.b64encode(data_bytes)
        return encrypted_data
    
    def decrypt(encrypted_data, encryption_key):
        decoded_data = base64.b64decode(encrypted_data)
        return decoded_data.decode()

    async def save_session(self, data: Dict[str, Any], custom_lifetime: Optional[timedelta] = None,
                session_id: Optional[str] = None, regenerate_id: bool = False) -> Dict[str, str]:
        if not session_id:
            session_id = self.generate_session_id()

        session_file = os.path.join(self.session_folder, session_id)

        session_data = {
            'data': data,
            'expiration': datetime.now() + (custom_lifetime or self.session_lifetime),
            'timeout': None,
            'user_agent': self.get_user_agent_hash() if self.user_agent_verification else None,
        }

        session_data_json = json.dumps(session_data, cls=DateTimeEncoder)
        if self.encryption_key:
            session_data_encrypted = self.encrypt(session_data_json, self.encryption_key)
        else:
            session_data_encrypted = session_data_json.encode()

        async with aiofiles.open(session_file, mode='wb') as f:
            await f.write(session_data_encrypted)

        if self.rotate_sessions:
            self.rotate_user_sessions(session_id)

        if regenerate_id:
            session_id = self.regenerate_session_id(session_id)

        self.loaded_session = session_id
        return {'session_id': session_id}

    async def load_session(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not session_id and self.loaded_session:
            session_id = self.loaded_session

        if not session_id:
            return None

        session_file = os.path.join(self.session_folder, session_id)

        if os.path.exists(session_file):
            async with aiofiles.open(session_file, mode='rb') as f:
                session_data_encrypted = await f.read()

            if self.encryption_key:
                session_data_json = self.decrypt(session_data_encrypted, self.encryption_key)
            else:
                session_data_json = session_data_encrypted.decode()

            session_data = json.loads(session_data_json)

            expiration = session_data.get('expiration')
            if (
                expiration and
                datetime.fromisoformat(expiration) > datetime.now() and
                (not self.user_agent_verification or self.verify_user_agent(session_data)) and
                (not self.fingerprint_sessions or self.verify_session_fingerprint(session_id))
            ):
                if session_data['timeout'] and self.timeout_handler:
                    self.timeout_handler(session_data)
                return session_data['data']
            else:
                await self.delete_session(session_id)
                return None
        else:
            return None

    async def delete_session(self, session_id: str) -> None:
        session_file = os.path.join(self.session_folder, session_id)

        if os.path.exists(session_file):
            os.remove(session_file)

    async def clear_expired_sessions(self) -> None:
        while True:
            current_time = datetime.now()
            for filename in os.listdir(self.session_folder):
                session_id = os.path.splitext(filename)[0]
                session_data = await self.load_session(session_id)

                if session_data and session_data.get('expiration') and session_data['expiration'] < current_time:
                    await self.delete_session(session_id)

            await asyncio.sleep(3600)

    def set_session_id_prefix(self, prefix: str) -> None:
        self.session_id_prefix = prefix

    async def session_exists(self, session_id: str) -> bool:
        session_file = os.path.join(self.session_folder, session_id)
        return os.path.exists(session_file)

    async def set_session(self, data: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, str]:
        return await self.save_session(data, session_id=session_id)

    async def get_session(self) -> Optional[Dict[str, Any]]:
        return await self.load_session()

    async def clear_session(self) -> None:
        self.loaded_session = None

    async def set_session_timeout(self, session_id: str, timeout_seconds: int) -> None:
        session_data = await self.load_session(session_id)
        if session_data:
            session_data['timeout'] = datetime.now() + timedelta(seconds=timeout_seconds)
            await self.save_session(session_data, session_id=session_id)

    async def check_session_timeout(self, session_id: str) -> bool:
        session_data = await self.load_session(session_id)
        if session_data and session_data['timeout'] and datetime.now() > session_data['timeout']:
            return True
        return False

    async def rotate_user_sessions(self, current_session_id: str) -> None:
        user_agent_hash = self.get_user_agent_hash()
        for filename in os.listdir(self.session_folder):
            session_id = os.path.splitext(filename)[0]
            if session_id != current_session_id:
                session_data = await self.load_session(session_id)
                if session_data and 'user_agent' in session_data and session_data['user_agent'] == user_agent_hash:
                    await self.delete_session(session_id)
                    
    def get_user_agent_hash(self) -> str:
        user_agent = self.get_user_agent()  # Get user agent using socket
        return base64.urlsafe_b64encode(hashlib.sha256(user_agent.encode()).digest()).decode()

    async def verify_user_agent(self, session_data: Dict[str, Any]) -> bool:
        user_agent_hash = self.get_user_agent_hash()
        return 'user_agent' in session_data and session_data['user_agent'] == user_agent_hash

    def verify_session_fingerprint(self, session_id: str) -> bool:
        return session_id.startswith(self.get_user_agent_hash())

    async def set(self, key: str, value: Any, session_id: Optional[str] = None) -> None:
        session_data = await self.load_session(session_id) or {}
        session_data[key] = value
        await self.save_session(session_data, session_id=session_id)

    async def get(self, key: str, session_id: Optional[str] = None, default: Any = None) -> Any:
        session_data = await self.load_session(session_id)
        return session_data.get(key, default) if session_data else default

    async def pop(self, key: str, session_id: Optional[str] = None, default: Any = None) -> Any:
        session_data = await self.load_session(session_id)
        value = session_data.pop(key, default) if session_data else default
        if session_data:
            await self.save_session(session_data, session_id=session_id)
        return value

    async def clear(self, session_id: Optional[str] = None) -> None:
        await self.save_session({}, session_id=session_id)

    async def keys(self, session_id: Optional[str] = None) -> List[str]:
        session_data = await self.load_session(session_id)
        return list(session_data.keys()) if session_data else []

    async def values(self, session_id: Optional[str] = None) -> List[Any]:
        session_data = await self.load_session(session_id)
        return list(session_data.values()) if session_data else []

    async def items(self, session_id: Optional[str] = None) -> List[Tuple[str, Any]]:
        session_data = await self.load_session(session_id)
        return list(session_data.items()) if session_data else []

    async def has_key(self, key: str, session_id: Optional[str] = None) -> bool:
        session_data = await self.load_session(session_id)
        return key in session_data if session_data else False

    def get_user_agent(self) -> str:
        try:
            conn = http.client.HTTPConnection("ifconfig.me")
            conn.request("GET", "/ua")
            res = conn.getresponse()
        except Exception as e:
            print(f"Error getting user agent: {e}")
            return ""

        user_agent = res.read().decode().strip()
        return user_agent
    
    async def setdefault(self, key: str, default: Any = None, session_id: Optional[str] = None) -> Any:
        session_data = await self.load_session(session_id) or {}
        value = session_data.setdefault(key, default)
        await self.save_session(session_data, session_id=session_id)
        return value

    async def update(self, other_dict: Dict[str, Any], session_id: Optional[str] = None) -> None:
        session_data = await self.load_session(session_id) or {}
        session_data.update(other_dict)
        await self.save_session(session_data, session_id=session_id)

    async def get_or_create(self, key: str, default: Any = None, session_id: Optional[str] = None) -> Any:
        session_data = await self.load_session(session_id) or {}
        value = session_data.get(key, default)
        if value is None:
            session_data[key] = default
            await self.save_session(session_data, session_id=session_id)
        return value
    
    async def popitem(self, session_id: Optional[str] = None) -> Optional[Tuple[str, Any]]:
        session_data = await self.load_session(session_id) or {}
        if session_data:
            key, value = session_data.popitem()
            await self.save_session(session_data, session_id=session_id)
            return key, value

    async def set_many(self, data_dict: Dict[str, Any], session_id: Optional[str] = None) -> None:
        session_data = await self.load_session(session_id) or {}
        session_data.update(data_dict)
        await self.save_session(session_data, session_id=session_id)

    async def get_many(self, keys: List[str], session_id: Optional[str] = None) -> Dict[str, Any]:
        session_data = await self.load_session(session_id) or {}
        return {key: session_data[key] for key in keys if key in session_data}

    async def delete_many(self, keys: List[str], session_id: Optional[str] = None) -> None:
        session_data = await self.load_session(session_id) or {}
        for key in keys:
            session_data.pop(key, None)
        await self.save_session(session_data, session_id=session_id)

    async def increment(self, key: str, amount: int = 1, session_id: Optional[str] = None) -> int:
        session_data = await self.load_session(session_id) or {}
        current_value = session_data.get(key, 0)
        session_data[key] = current_value + amount
        await self.save_session(session_data, session_id=session_id)
        return session_data[key]

    async def decrement(self, key: str, amount: int = 1, session_id: Optional[str] = None) -> int:
        session_data = await self.load_session(session_id) or {}
        current_value = session_data.get(key, 0)
        session_data[key] = max(0, current_value - amount)
        await self.save_session(session_data, session_id=session_id)
        return session_data[key]

    async def extend_session(self, session_id: str, custom_lifetime: Optional[timedelta] = None) -> None:
        session_data = await self.load_session(session_id)
        if session_data:
            session_data['expiration'] += (custom_lifetime or self.session_lifetime)
            await self.save_session(session_data, session_id=session_id)
