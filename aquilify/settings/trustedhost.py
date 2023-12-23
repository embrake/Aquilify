import importlib.util

class TrustedHostConfigSettings:
    def __init__(self) -> None:
        self.settings_module_path: str = "./settings.py"

    def _fetch_trustedhost_config(self):
        try:
            settings = self._load_settings_module()
            allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', ['*'])
            allow_subdomains = getattr(settings, 'ALLOW_SUBDOMAINS', True)
            redirect_on_fails = getattr(settings, 'REDIRECT_ON_FAILS', False)
            redirect_url = getattr(settings, 'REDIRECT_URL', None)
            enforce_https = getattr(settings, 'ENFORCE_HTTPS', False)
            www_redirect = getattr(settings, 'WWW_REDIRECT', False)

            return { 'allowed_hosts': allowed_hosts, 'allow_subdomains': allow_subdomains, 'redirect_on_fails': redirect_on_fails,
                'redirect_url': redirect_url, "enforce_https": enforce_https, "www_redirect": www_redirect }
                    
        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings

    def fetch(self):
        data = self._fetch_trustedhost_config()
        return data