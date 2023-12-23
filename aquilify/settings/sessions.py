import importlib.util

class SessionConfigSettings:
    def __init__(self) -> None:
        self.settings_module_path: str = "./settings.py"

    def _fetch_sessions_config(self):
        try:
            settings = self._load_settings_module()
            sessions_config = getattr(settings, 'SESSIONS_CONFIG', None)

            session_backend = getattr(settings, 'SESSION_BACKEND', None)
            sessions_secret_key = getattr(settings, 'SESSION_SECRET_KEY', None)
            sessions_max_age = getattr(settings, 'SESSION_MAX_AGE', 1800)
            sessions_lifetime = getattr(settings, 'SESSION_LIFETIME', 30)
            sessions_secure = getattr(settings, 'SESSION_SECURE', True)
            sessions_httponly = getattr(settings, 'SESSION_HTTPONLY', True)
            sessions_samesite = getattr(settings, 'SESSION_SAMESITE', 'Lax')
            sessions_cookie_name = getattr(settings, 'SESSION_COOKIE_NAME', '_session_id')

            if sessions_config is None and session_backend is None:
                raise KeyError("Session backend cannot be none either use memory or cookie.")
            if sessions_config is None and sessions_secret_key is None:
                raise KeyError("Session secret_key can't be none! Use a strong key.")
            
            var_session_config = [{
                'backend': session_backend,
                'secret_key': sessions_secret_key,
                'max_age': sessions_max_age,
                'ifetime': sessions_lifetime,
                'secure': sessions_secure,
                'httponly': sessions_httponly,
                'samesite': sessions_samesite,
                'cookie_name': sessions_cookie_name
            }]

            if sessions_config is not None and var_session_config[0]['backend'] is not None:
                raise ValueError("Cannot use both session_config and config_variables simultaneously.")

            if sessions_config is None:
                return var_session_config

            return sessions_config

        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings

    def _set_settings_data(self, session_config):
        session_lifetime = session_config.get('session_lifetime', 30)
        secret_key = session_config.get('secret_key', )
        max_age = session_config.get('max_age', 1800)
        secure = session_config.get('secure', True)
        httponly = session_config.get('httponly', True)
        samesite = session_config.get('samesite', 'Lax')
        cookie_name = session_config.get('cookie_name', '_sessionid')

        return {
            'max_age': max_age,
            'session_lifetime': session_lifetime,
            'secure': secure,
            'httponly': httponly,
            'samesite': samesite,
            'cookie_name': cookie_name,
            'secret_key': secret_key
        }
    
    def _set_memory_settings_data(self, config):
        session_lifetime = config.get('session_lifetime', 30)
        secret_key = config.get('secret_key', "mysecret_key")

        return { 'session_lifetime': session_lifetime, 'secret_key': secret_key}

    def fetch(self):
        sessions_config = self._fetch_sessions_config()

        backend_types = set()
        for session_config in sessions_config:
            backend = session_config.get('backend')
            backend_types.add(backend)
            secret_key = session_config.get('secret_key')
            if not isinstance(secret_key, str):
                raise ValueError("The 'secret_key' must be a string.")
            if backend == 'cookie':
                return self._set_settings_data(session_config)
            elif backend == 'memory':
                return self._set_memory_settings_data(session_config)

        if len(backend_types) > 1:
            raise ValueError("Multiple session backends detected. Please use only one type of session backend (either cookies or memory-based sessions), not a mix of both.")