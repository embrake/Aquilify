import importlib.util

class Settings:
    def __init__(self, settings_module_path="./settings.py") -> None:
        self.settings_module_path = settings_module_path
        self._load_settings_config()

    def _load_settings_config(self):
        try:
            settings = self._load_settings_module()
            self._set_attributes(settings)

        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings

    def _set_attributes(self, settings):
        for attr_name in dir(settings):
            if not attr_name.startswith("__"):
                try:
                    setattr(self, attr_name, getattr(settings, attr_name))
                except AttributeError as e:
                    print(f"Error setting attribute {attr_name}: {e}")

settings = Settings()