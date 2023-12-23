import importlib.util

from datetime import timedelta

class CSRFConfigSettings:
    def __init__(self, settings_module_path: str = "./settings.py") -> None:
        self.settings_module_path = settings_module_path
        self.csrf_data = []

    def fetch(self) -> None:
        try:
            with open(self.settings_module_path) as file:
                settings = self._load_settings_module()
                templates = getattr(settings, 'CSRF', [])
                self._extract_csrf(templates)

        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings

    def _extract_csrf(self, templates: list) -> None:
        for csrf in templates:
            extracted_data = self._extract_csrf_data(csrf)
            self.csrf_data.append(extracted_data)

    def _extract_csrf_data(self, csrf: dict) -> dict:
        backend = self._get_backend(csrf)
        options = self._get_options(csrf)

        return {
            'backend': backend,
            'options': {
                'secret_key': options.get('secret_key', ''),
                'expiration': options.get('expiration', timedelta(hours=1)),
                'token_key': options.get('token_key', "_csrf_token"),
                'logger': options.get('logger', None),
                'cookie_options': options.get('cookie_options', {"httponly": True, "secure": True, "samesite": 'strict'}),
                'protected_methods': options.get('protected_methods', ["POST", "PUT", "DELETE"]),
                'ip_verification': options.get('ip_verification', True),
                'trusted_ips': options.get('trusted_ips', ["*"]),
                'max_token_lifetime': options.get('max_token_lifetime', timedelta(hours=7)),
                'token_refresh_interval': options.get('token_refresh_interval', timedelta(hours=6)) 
            }
        }

    def _get_backend(self, csrf: dict) -> str:
        backend = csrf.get('BACKEND', None)
        return backend if backend else ""

    def _get_options(self, csrf: dict) -> dict:
        return csrf.get('OPTIONS', {})