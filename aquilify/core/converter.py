import re

from typing import Pattern, Tuple

class Converter:
    def _regex_converter(
        self,
        path: str,
        strict_slashes: bool,
        prefix: str = ""
    ) -> Tuple[str, Pattern]:
        
        if strict_slashes:
            pattern = re.sub(r"{([^}]+)}", rf"{prefix}(?P<\1>[^/]+)", path)
        else:
            pattern = re.sub(r"{([^}]+)}", rf"{prefix}(?P<\1>[^/]+/?)", path)
        pattern = f"^{pattern}$"
        path_regex = re.compile(pattern)
        return pattern, path_regex