import re
from html.parser import HTMLParser
from typing import List, Optional, Tuple

class SanitizeHTMLParser(HTMLParser):
    def __init__(self, allowed_tags: Optional[List[str]] = None, allowed_attributes: Optional[List[str]] = None) -> None:
        super().__init__()
        self.allowed_tags: List[str] = allowed_tags or []
        self.allowed_attributes: List[str] = allowed_attributes or []
        self.sanitized_data: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in self.allowed_tags:
            sanitized_attrs: List[Tuple[str, str]] = [
                (attr, self.sanitize_sql_injection(value))
                for attr, value in attrs
                if attr in self.allowed_attributes and value is not None
            ]
            sanitized_starttag: str = f"<{tag} {' '.join([f'{attr}="{value}"' for attr, value in sanitized_attrs])}>"
            self.sanitized_data.append(sanitized_starttag)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.allowed_tags:
            self.sanitized_data.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.sanitized_data.append(data)

    @staticmethod
    def sanitize_sql_injection(value: str) -> str:
        return re.sub(r"[\'\";]", '', value)

def sanitize(input_string: str, sanitize_html: bool = True, sanitize_sql: bool = True, sanitize_nosql: bool = True) -> str:
    if sanitize_html:
        input_string = sanitize_html_input(input_string)

    if sanitize_sql:
        input_string = sanitize_sql_input(input_string)

    if sanitize_nosql:
        input_string = sanitize_nosql_input(input_string)

    return input_string

def sanitize_html_input(input_string: str) -> str:
    input_string: str = re.sub(r'<script.*?</script>', '', input_string, flags=re.DOTALL)
    input_string: str = re.sub(r'<style.*?</style>', '', input_string, flags=re.DOTALL)

    parser: SanitizeHTMLParser = SanitizeHTMLParser(
        allowed_tags=['p', 'br', 'strong', 'em', 'u'],
        allowed_attributes=['href', 'title']
    )
    parser.feed(input_string)

    return ''.join(parser.sanitized_data)

def sanitize_sql_input(input_string: str) -> str:
    return re.sub(r"[\'\";]", '', input_string)

def sanitize_nosql_input(input_string: str) -> str:
    return input_string.replace('$', '').replace('.', '')
