import re

class UserAgentParser:
    def __init__(self, user_agent_string: str) -> None:
        self.user_agent_string: str = user_agent_string
        self.browser: str = ''
        self.browser_version: str = ''
        self.browser_engine: str = ''
        self.os: str = ''
        self.os_version: str = ''
        self.device: str = ''
        self.is_mobile: bool = False
        self.language: str = ''
        self.platform: str = ''
        self.is_bot_or_crawler: bool = False
        self.screen_resolution: str = ''
        self.viewport_size: str = ''
        self.js_enabled: bool = False
        self.referer: str = ''
        self.timezone: str = ''
        self._parse_user_agent()

    def _parse_user_agent(self) -> None:
        self.browser, self.browser_version = self._get_browser_info()
        self.browser_engine = self._get_browser_engine()
        self.os, self.os_version = self._get_os_info()
        self.device = self._get_device_info()
        self.is_mobile = self._check_mobile()
        self.language = self._get_language()
        self.platform = self._get_platform()
        self.is_bot_or_crawler = self._check_bot_or_crawler()
        self.screen_resolution = self._get_screen_resolution()
        self.viewport_size = self._get_viewport_size()
        self.js_enabled = self._check_javascript_enabled()
        self.referer = self._get_referer()
        self.timezone = self._get_timezone()

    def _get_browser_info(self):
        browsers = {
            'Opera': r'Opera\/([0-9.]+)',
            'Firefox': r'Firefox\/([0-9.]+)',
            'Edge': r'(?:Edg(?:e)?)\/([0-9.]+)',
            'Chrome': r'Chrome\/([0-9.]+)',
            'Safari': r'Safari\/([0-9.]+)',
            'IE': r'MSIE ([0-9.]+)|rv:([0-9.]+)'
        }
        
        browser_priority = ['Edge', 'Chrome', 'Firefox', 'Safari', 'Opera', 'IE']

        for browser in browser_priority:
            if browser in browsers:
                pattern = browsers[browser]
                match = re.search(pattern, self.user_agent_string)
                if match:
                    if browser == 'Edge':
                        version = match.group(1) or ''
                    else:
                        version = match.group(1) or match.group(2) or ''
                    return browser, version
        
        return 'Unknown', ''
    
    def _get_browser_engine(self):
        browser_engines = {
            'Blink': 'Blink',
            'WebKit': 'WebKit',
            'Gecko': 'Gecko',
            'Trident': 'Trident'
        }
        for engine, pattern in browser_engines.items():
            if pattern in self.user_agent_string:
                return engine
        return 'Unknown'

    def _get_os_info(self):
        operating_systems = {
            'Windows': r'Windows NT ([0-9.]+)',
            'Android': r'Android ([0-9.]+)',
            'Linux': r'Linux ([0-9_]+)',
            'iOS': r'OS ([0-9_]+) like Mac',
            'Mac': r'Mac OS X '
        }
        for os, pattern in operating_systems.items():
            match = re.search(pattern, self.user_agent_string)
            if match:
                version = match.group(1).replace('_', '.') if match.group(1) else ''
                return os, version
        return 'Unknown', ''

    def _get_device_info(self):
        devices = {
            'iPhone': r'iPhone(?:\sSimulator)?',
            'iPad': r'iPad(?:\sSimulator)?',
            'Mobile': r'Mobile',
            'Tablet': r'Tablet',
            'Desktop': r'Windows|Macintosh|Linux'
        }
        for device, pattern in devices.items():
            if re.search(pattern, self.user_agent_string):
                return device
        return 'Unknown'

    def _check_mobile(self):
        return 'Mobile' in self.user_agent_string

    def _get_language(self):
        match = re.search(r'(?<=\b(?:language=))(.*?)(?=[;|$])', self.user_agent_string)
        return match.group(1) if match else 'Unknown'

    def _get_platform(self):
        platforms = {
            'Windows': 'Windows',
            'Linux': 'Linux',
            'Mac': 'Macintosh'
        }
        for platform, pattern in platforms.items():
            if pattern in self.user_agent_string:
                return platform
        return 'Unknown'

    def _check_bot_or_crawler(self):
        bot_patterns = [
            'bot',
            'crawler',
            'spider',
            'googlebot',
            'bingbot',
            'slurp',
            'duckduckbot',
            'yandexbot'
        ]
        for bot_pattern in bot_patterns:
            if re.search(bot_pattern, self.user_agent_string, re.IGNORECASE):
                return True
        return False

    def _get_screen_resolution(self):
        match = re.search(r'(?<=\b(?:Screen: ))([0-9]+x[0-9]+)', self.user_agent_string)
        return match.group(1) if match else 'Unknown'

    def _get_viewport_size(self):
        match = re.search(r'(?<=\b(?:Viewport: ))([0-9]+x[0-9]+)', self.user_agent_string)
        return match.group(1) if match else 'Unknown'

    def _check_javascript_enabled(self):
        return 'JS' in self.user_agent_string

    def _get_referer(self):
        match = re.search(r'(?<=\b(?:Referer: ))(.*?)(?=[;|$])', self.user_agent_string)
        return match.group(1) if match else 'Unknown'

    def _get_timezone(self):
        match = re.search(r'(?<=\b(?:Timezone: ))(.*?)(?=[;|$])', self.user_agent_string)
        return match.group(1) if match else 'Unknown'
    
    def __str__(self) -> str:
        return str(self.user_agent_string)
    
    def __repr__(self) -> str:
        return f"UserAgentParser({self.user_agent_string})"

    def to_dict(self) -> dict:
        return {
            'user_agent_string': self.user_agent_string,
            'browser': self.browser,
            'browser_version': self.browser_version,
            'browser_engine': self.browser_engine,
            'os': self.os,
            'os_version': self.os_version,
            'device': self.device,
            'is_mobile': self.is_mobile,
            'language': self.language,
            'platform': self.platform,
            'is_bot_or_crawler': self.is_bot_or_crawler,
            'screen_resolution': self.screen_resolution,
            'viewport_size': self.viewport_size,
            'js_enabled': self.js_enabled,
            'referer': self.referer,
            'timezone': self.timezone
        }
