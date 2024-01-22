from functools import wraps

from aquilify.utils.functional import keep_lazy


class SafeData:
    __slots__ = ()

    def __html__(self):
        return self


class SafeString(str, SafeData):
    __slots__ = ()

    def __add__(self, rhs):
        t = super().__add__(rhs)
        if isinstance(rhs, SafeData):
            return SafeString(t)
        return t

    def __str__(self):
        return self


SafeText = SafeString 


def _safety_decorator(safety_marker, func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return safety_marker(func(*args, **kwargs))

    return wrapper


@keep_lazy(SafeString)
def mark_safe(s):
    if hasattr(s, "__html__"):
        return s
    if callable(s):
        return _safety_decorator(mark_safe, s)
    return SafeString(s)
