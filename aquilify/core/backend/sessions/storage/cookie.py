import base64
import json
import os

from typing import Dict, Any
from datetime import datetime

from aquilify.settings import settings

class SessionData(Dict[str, Any]):
    pass


CACHE_DIR = ".aquilify/cache/session/cookie/"
CONFIG_FILE = ".aquilify/cache/session/config.json"
AQUILIFY_CONFIG_FILE = ".aquilify/config.json"

class CookieSessionStorage:
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
        secret_key = getattr(settings, 'SECRET_KEY')
        key = secret_key.encode()
        data_bytes = data.encode()
        for i in range(len(data_bytes)):
            encrypted.append(chr(data_bytes[i] ^ key[i % len(key)]))
        return base64.urlsafe_b64encode("".join(encrypted).encode()).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        decrypted = []
        secret_key = getattr(settings, 'SECRET_KEY')
        key = secret_key.encode()
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