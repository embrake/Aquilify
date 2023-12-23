import importlib.util

class HTTPSConfigSettings:
    def __init__(self) -> None:
        self.settings_module_path: str = "./settings.py"

    def _fetch_https_config(self):
        try:
            settings = self._load_settings_module()
            strict = getattr(settings, 'HTTPS_REDIRECT_STRICT', True)
            allowed_host = getattr(settings, 'HTTPS_REDIRECT_ALLOWED_HOST', [])
            
            return {'strict': strict, 'allowed_host': allowed_host}
        
        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings


    def fetch(self):
        data = self._fetch_https_config()
        return data