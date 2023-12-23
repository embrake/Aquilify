import importlib.util
import logging

class LoggingConfigSettings:
    def __init__(self) -> None:
        self.settings_module_path: str = "./settings.py"

    def _fetch_logging_config(self):
        try:
            settings = self._load_settings_module()
            file_path = getattr(settings, 'LOG_FILE_PATH', None)
            user_agent = getattr(settings, 'LOG_USER_AGENT', True)
            client_ip = getattr(settings, 'LOG_CLIENT_IP', True)
            format = getattr(settings, 'LOG_FORMAT', None)
            log_size = getattr(settings, 'MAX_LOG_SIZE', 10 * 1024 * 1024)
            backup_count = getattr(settings, 'BACKUP_COUNT', 5)
            log_level = getattr(settings, 'LOG_LEVEL', logging.INFO)
            output_stream = getattr(settings, 'OUTPUT_STREAM', 'file')
            append_logs = getattr(settings, 'APPEND_LOGS', False)
            timestamp_format = getattr(settings, 'TIMESTAMP_FORMAT', "%Y-%m-%d %H:%M:%S")
            log_response_time = getattr(settings, 'LOG_RESPONSE_TIME', True)
            log_pattern_url = getattr(settings, 'LOG_URL_PATTERN', None)
            
            return {
                "file_path": file_path, "user_agent": user_agent, "client_ip": client_ip, "format": format, "log_size": log_size,
                "backup_count": backup_count, "log_level": log_level, "output_stream": output_stream, "append_logs": append_logs,
                "timestamp_format": timestamp_format, "log_response_time": log_response_time, "log_pattern_url": log_pattern_url
            }
        
        except (FileNotFoundError, AttributeError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings


    def fetch(self):
        data = self._fetch_logging_config()
        return data