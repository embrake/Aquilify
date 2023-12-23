import importlib.util

class RateLimitConfigSettings:
    def __init__(self) -> None:
        self.settings_module_path: str = "./settings.py"

    def _fetch_limit_config(self):
        try:
            settings = self._load_settings_module()
            limit = getattr(settings, 'RATE_LIMITER_LIMIT', 60)
            window = getattr(settings, 'RATE_LIMITER_WINDOW', 60)
            exempt_paths = getattr(settings, 'RATE_LIMITER_EXEMPT_PATHS', [])
            headers = getattr(settings, 'RATE_LIMITER_HEADERS', {})
            dynamic_limit = getattr(settings, 'RATE_LIMITER_DYNAMIC_LIMIT', {})
            concurrency_control = getattr(settings, 'RATE_LIMITER_CONCURRENCY_CONTROL', False)
            expiry = getattr(settings, 'RATE_LIMITER_EXPIRY', {})
            monitoring_callback = self._fetch_response_handler_functions("RATE_LIMITER_MONITORING_CALLBACK") or None
            whitelist = getattr(settings, 'RATE_LIMITER_WHITELIST', [])
            blacklist = getattr(settings, 'RATE_LIMITER_BLACKLIST', [])
            endpoint = getattr(settings, 'RATE_LIMITER_BY_ENDPOINT', {})
            adjustments = getattr(settings, 'RATE_LIMITER_ADJUSTMENTS', {})
            expiry_policies = getattr(settings, 'RATE_LIMITER_EXPIRY_POLICIES', {})
            ip_rate_limits = getattr(settings, 'RATE_LIMITER_IP_RATE_LIMITS', {})
            bypass_token = getattr(settings, 'RATE_LIMITER_BYPASS_TOKEN', {})
            granular = getattr(settings, 'RATE_LIMITER_GRANULAR', {})
            automated_asjustments = self._fetch_response_handler_functions("RATE_LIMITER_AUTOMATED_ADJUSTMENTS") or None
            advance_monitiring_and_reporting = self._fetch_response_handler_functions("RATE_LIMITER_ADVANCE_MONITORING_AND_REPORTING") or None
            granular_callback = self._fetch_response_handler_functions("RATE_LIMITER_GRANULAR_CALLBACK") or None

            rate_limit_dict = {
                'limit': limit,
                'window': window,
                'exempt_paths': exempt_paths,
                'headers': headers,
                'dynamic_limit': dynamic_limit,
                'concurrency_control': concurrency_control,
                'expiry': expiry,
                'monitoring_callback': monitoring_callback,
                'whitelist': whitelist,
                'blacklist': blacklist,
                'endpoint': endpoint,
                'adjustments': adjustments,
                'expiry_policies': expiry_policies,
                'ip_rate_limits': ip_rate_limits,
                'bypass_token': bypass_token,
                'granular': granular,
                'automated_adjustments': automated_asjustments,
                'advance_monitoring_and_reporting': advance_monitiring_and_reporting,
                'granular_callback': granular_callback
            }
            return rate_limit_dict
                    
        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings
    
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

    def fetch(self):
        data = self._fetch_limit_config()
        return data