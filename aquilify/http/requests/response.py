from typing import Optional, Union
import json
import xml.etree.ElementTree as ET

class Response:
    def __init__(self, status_code: int, text: str, headers: dict, content_type: str):
        self.status_code = status_code
        self.text = text
        self.headers = headers
        self.content_type = content_type

    def texts(self) -> Optional[str]:
        if "text/plain" in self.content_type.lower():
            return self.text
        return None

    def body(self) -> str:
        return self.text
    
    def json(self) -> Optional[dict]:
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return None

    def xml(self) -> Optional[ET.Element]:
        if "application/xml" in self.content_type:
            return ET.fromstring(self.text)
        return None

    def header(self) -> dict:
        return self.headers

    def statusCode(self) -> int:
        return self.status_code

    def ContentType(self) -> str:
        return self.content_type

    def get_header(self, key: str) -> Union[str, None]:
        return self.headers.get(key)

    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def is_redirect(self) -> bool:
        return 300 <= self.status_code < 400

    def is_client_error(self) -> bool:
        return 400 <= self.status_code < 500

    def is_server_error(self) -> bool:
        return 500 <= self.status_code < 600

    def has_header(self, key: str) -> bool:
        return key in self.headers

    def cookie(self, name: str) -> Union[str, None]:
        cookies = self.headers.get('Set-Cookie', '').split(';')
        for cookie in cookies:
            parts = cookie.strip().split('=')
            if len(parts) == 2 and parts[0] == name:
                return parts[1]
        return None

    def cookies(self):
        cookies = {}
        cookie_header = self.headers.get('Set-Cookie', '')
        cookie_parts = cookie_header.split(';')
        for part in cookie_parts:
            key_value = part.strip().split('=')
            if len(key_value) == 2:
                cookies[key_value[0]] = key_value[1]
        return cookies
