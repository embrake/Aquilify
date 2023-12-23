import importlib.util

class CORSConfigSettings:
    def __init__(self) -> None:
        self.settings_module_path: str = "./settings.py"

    def _fetch_sessions_config(self):
        try:
            settings = self._load_settings_module()

            allowed_origin = getattr(settings, "CORS_ALLOWED_ORIGIN", ["*"])
            allowed_method = getattr(settings, "CORS_ALLOWED_METHOD", ["*"])
            allowed_headers = getattr(settings, "CORS_ALLOWED_HEADERS", ["*"])
            allowed_credentials = getattr(settings, "CORS_ALLOWED_CREDENTIALS", False)
            expose_headers = getattr(settings, "CORS_EXPOSED_HEADERS", set())
            max_age = getattr(settings, "CORS_MAX_AGE", 600)
            security_headers = getattr(settings, "CORS_SECURITY_HEADERS", {})
            preflight_response = getattr(settings, "CORS_PREFLIGHT_RESPONSE", None)
            preflight_cache = getattr(settings, "CORS_PREFLIGHT_CACHE", True)
            origin_whitelist = getattr(settings, "CORS_ORIGIN_WHITELIST", None)
            automatic_preflight_handling = getattr(settings, "CORS_AUTOMATIC_PREFLIGHT_HANDLIGN", True)
            dynamic_headers_whitelist = getattr(settings, "CORS_DYNAMIC_HEADERS_WHITELIST", None)
            log_request = getattr(settings, "CORS_LOG_REQUEST", True)
            exclude_paths = getattr(settings, "CORS_EXCLUDE_PATHS", [])
            response_handler = self._fetch_response_handler_functions("CORS_RESPONSE_HANDLER")

            if security_headers is None:
                pass

            cors_settings = {
                "allowed_origin": allowed_origin,
                "allowed_method": allowed_method,
                "allowed_credentials": allowed_credentials,
                "allowed_headers": allowed_headers,
                "expose_headers": expose_headers,
                "max_age": max_age,
                "security_headers": security_headers,
                "preflight_cache": preflight_cache,
                "preflight_response": preflight_response,
                "origin_whitelist": origin_whitelist,
                "automatic_preflight_handling": automatic_preflight_handling,
                "dynamic_headers_whitelist": dynamic_headers_whitelist,
                "log_request": log_request,
                "response_handler": response_handler,
                "exclude_paths": exclude_paths
            }
            return cors_settings

        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")
        
    def _fetch_security_headers(self, settings):
        try:
            security_headers = getattr(settings, "CORS_SECURITY_HEADERS", {})
            return security_headers if security_headers else {}
        except AttributeError:
            return {}

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings
    
    def fetch(self):
        cors_setting = self._fetch_sessions_config()
        if cors_setting is None:
            raise KeyError("CORS Configuration missing in settings.py")
        return cors_setting
    
    def _fetch_response_handler_functions(self, object):
        settings = self._load_settings_module()
        
        if settings:
            path_to_callback = getattr(settings, object, None)
            
            if path_to_callback:
                try:
                    parts = path_to_callback.split('.')
                    module_path = '.'.join(parts[:-1])
                    callback_name = parts[-1]
                    callback_module = importlib.import_module(module_path)
                    callback_obj = getattr(callback_module, callback_name)
                    if isinstance(callback_obj, type):
                        callback_obj = callback_obj()
                    
                    return callback_obj
                except (AttributeError, ImportError, ValueError) as e:
                    print(f"Error fetching callback: {e}")
        
        return None
