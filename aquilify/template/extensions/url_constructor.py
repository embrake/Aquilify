from jinja2 import nodes
from jinja2.ext import Extension
from urllib.parse import urljoin, urlencode

from ...settings import settings

class URLConstructor(Extension):
    tags = {'static', 'redirect', 'media'}

    def __init__(self, environment):
        super().__init__(environment)
        self.static_base_url = getattr(settings, 'STATIC_URL', None)
        self.media_url = settings.MEDIA_URL
        self.static_multi_url = getattr(settings, 'STATIC_MULTI_URLS', [])

    def parse(self, parser):
        tag_name = parser.stream.current.value
        if tag_name in self.tags:
            return self._parse_tag(parser, tag_name)
        else:
            self._raise_invalid_tag_error(tag_name)

    def _parse_tag(self, parser, tag_name):
        line_number = parser.stream.expect(f'name:{tag_name}').lineno
        if tag_name == 'static':
            return self._parse_static_tag(parser, line_number)
        elif tag_name == 'redirect':
            return self._parse_redirect_tag(parser, line_number)
        elif tag_name == 'media':
            return self._parse_media_tag(parser, line_number)

    def _parse_static_tag(self, parser, line_number):
        filename_expr = parser.parse_expression()
        if isinstance(filename_expr, nodes.Const) and filename_expr.value.startswith('multi:'):
            key = filename_expr.value.split(':', 1)[-1].strip()
            return self._create_call_block('_build_multi_static_url', [nodes.Const(key)], line_number)
        else:
            return self._create_call_block('_build_static_url', [filename_expr], line_number)

    def _parse_media_tag(self, parser, line_number):
        filename_expr = parser.parse_expression()
        return self._create_call_block('_build_media_url', [filename_expr], line_number)

    def _parse_redirect_tag(self, parser, line_number):
        url_expr = parser.parse_expression()
        args_expr = parser.parse_expression()
        return self._create_redirect_call_block('_build_redirect_url', [url_expr, args_expr], line_number)

    def _create_call_block(self, method_name, expr_list, line_number):
        return nodes.CallBlock(
            self.call_method(method_name, expr_list),
            [], [], []
        ).set_lineno(line_number)

    def _create_redirect_call_block(self, method_name, expr_list, line_number):
        return nodes.CallBlock(
            self.call_method(method_name, expr_list),
            [], [], []
        ).set_lineno(line_number)

    def _build_static_url(self, filename, caller=None):
        return self._build_url(filename, self.static_base_url, "STATIC_URL")

    def _build_multi_static_url(self, key, caller=None):
        return self._build_multi_url(key, self.static_multi_url, "STATIC_MULTI_URL")

    def _build_media_url(self, filename, caller=None):
        return self._build_url(filename, self.media_url, "MEDIA_URL")

    def _build_redirect_url(self, location, args={}, caller=None):
        self._check_string_type(location, "Invalid redirect location. It must be a string.")
        if args:
            location = urljoin(location, f'?{urlencode(args)}')
        return location

    def _build_url(self, filename, base_url, config_name):
        self._check_string_type(filename, f"Invalid filename. It must be a string for {config_name}.")
        if base_url:
            return urljoin(base_url, filename)
        else:
            raise ValueError(f"No valid URL found in {config_name} configuration.")

    def _build_multi_url(self, key, multi_config, config_name):
        self._check_string_type(key, f"Invalid key. It must be a string for {config_name}.")
        for url_config in multi_config:
            if key in url_config:
                return url_config[key]
        raise ValueError(f"URL for '{key}' not found in {config_name}")

    def _raise_invalid_tag_error(self, tag):
        raise ValueError(f"Invalid tag '{tag}'")

    def _check_string_type(self, value, error_message):
        if not isinstance(value, str):
            raise ValueError(error_message)
