import importlib.util

class TimeoutConfigSettings:
    def __init__(self) -> None:
        self.settings_module_path: str = "./settings.py"

    def _fetch_timeout_config(self):
        try:
            settings = self._load_settings_module()
            seconds = getattr(settings, 'TIMEOUT_SECONDS', 10)
            response = getattr(settings, 'TIMEOUT_RESPONSE', "Gateway Timeout")

            return { 'seconds': seconds, 'response': response }
                    
        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings

    def fetch(self):
        data = self._fetch_timeout_config()
        return data