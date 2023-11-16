import datetime
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Optional

class LoggingMiddleware:
    def __init__(
        self,
        log_file_path: Optional[str] = None,
        log_user_agent: bool = True,
        log_client_ip: bool = True,
        log_format: Optional[str] = None,
        max_log_size: int = 10 * 1024 * 1024,  # 10MB default max log file size
        backup_count: int = 5,  # Default backup count for log files
        log_level: int = logging.INFO,  # Default log level is INFO
        output_stream: Optional[str] = 'file',  # Default output to log file
        append_logs: bool = False,  # Overwrite logs by default
        timestamp_format: Optional[str] = "%Y-%m-%d %H:%M:%S",  # Default timestamp format
        log_response_time: bool = True,  # Log response times
        url_patterns_to_log: Optional[list] = None,  # List of URL patterns to log
    ):
        self.log_file_path = log_file_path
        self.log_user_agent = log_user_agent
        self.log_client_ip = log_client_ip
        self.max_log_size = max_log_size
        self.backup_count = backup_count
        self.log_level = log_level
        self.output_stream = output_stream
        self.append_logs = append_logs
        self.timestamp_format = timestamp_format
        self.log_response_time = log_response_time
        self.url_patterns_to_log = url_patterns_to_log or []

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        self._setup_logging(log_format)

    def _setup_logging(self, log_format: Optional[str]):
        log_formatter = log_format or '%(asctime)s - %(levelname)s - %(message)s'

        if self.log_file_path and self.output_stream == 'file':
            if not os.path.exists(os.path.dirname(self.log_file_path)):
                os.makedirs(os.path.dirname(self.log_file_path))

            if self.append_logs:
                file_handler = logging.FileHandler(self.log_file_path)
            else:
                file_handler = TimedRotatingFileHandler(
                    self.log_file_path,
                    when='midnight',  # Rotate logs at midnight
                    interval=1,  # Rotate daily
                    backupCount=self.backup_count
                )
            file_handler.setFormatter(logging.Formatter(log_formatter))
            self.logger.addHandler(file_handler)
        else:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(log_formatter))
            self.logger.addHandler(console_handler)

    async def log_request(self, request):
        if not self._should_log_request(request):
            return

        start_time = datetime.datetime.now()
        log_entry = self._create_log_entry(request)

        if self.log_response_time:
            request.context['start_time'] = start_time
            request.context['log_entry'] = log_entry

    async def log_response(self, response, context):
        log_entry = context.get('log_entry')
        start_time = context.get('start_time')

        if log_entry and start_time:
            log_entry['status_code'] = response.status_code
            end_time = datetime.datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000  # milliseconds
            log_entry['response_time_ms'] = response_time

            log_message = self._format_log_entry(log_entry)
            self.logger.info(log_message)

    def _should_log_request(self, request):
        if not self.url_patterns_to_log:
            return True

        for pattern in self.url_patterns_to_log:
            if pattern in request.url:
                return True
        return False

    def _create_log_entry(self, request):
        log_entry = {
            'timestamp': datetime.datetime.now().strftime(self.timestamp_format),
            'method': request.method,
            'url': request.url,
        }

        if self.log_user_agent:
            log_entry['user_agent'] = request.headers.get('user-agent')

        if self.log_client_ip:
            log_entry['client_ip'] = request.client

        return log_entry

    def _format_log_entry(self, log_entry):
        formatted_log = f"[{log_entry['timestamp']}] - {log_entry['method']} {log_entry['url']}"
        if 'status_code' in log_entry:
            formatted_log += f" - Status Code: {log_entry['status_code']}"
        if 'user_agent' in log_entry:
            formatted_log += f" - User Agent: {log_entry['user_agent']}"
        if 'client_ip' in log_entry:
            formatted_log += f" - Client IP: {log_entry['client_ip']}"
        if 'response_time_ms' in log_entry:
            formatted_log += f" - Response Time: {log_entry['response_time_ms']} ms"
        return formatted_log

    async def __call__(self, request, response):
        context = {
            'request': request,
        }
        await self.log_request(request)
        await self.log_response(response, request.context)
        return response
