import codecs
import datetime
import locale
from decimal import Decimal
from types import NoneType
from urllib.parse import quote

from .functional import Promise


class AquilifyUnicodeDecodeError(UnicodeDecodeError):
    def __str__(self):
        return "%s. You passed in %r (%s)" % (
            super().__str__(),
            self.object,
            type(self.object),
        )


def smart_str(s, encoding="utf-8", strings_only=False, errors="strict"):
    if isinstance(s, Promise):
        return s
    return force_str(s, encoding, strings_only, errors)


_PROTECTED_TYPES = (
    NoneType,
    int,
    float,
    Decimal,
    datetime.datetime,
    datetime.date,
    datetime.time,
)


def is_protected_type(obj):
    return isinstance(obj, _PROTECTED_TYPES)


def force_str(s, encoding="utf-8", strings_only=False, errors="strict"):
    if issubclass(type(s), str):
        return s
    if strings_only and is_protected_type(s):
        return s
    try:
        if isinstance(s, bytes):
            s = str(s, encoding, errors)
        else:
            s = str(s)
    except UnicodeDecodeError as e:
        raise AquilifyUnicodeDecodeError(*e.args) from None
    return s


def smart_bytes(s, encoding="utf-8", strings_only=False, errors="strict"):
    if isinstance(s, Promise):
        return s
    return force_bytes(s, encoding, strings_only, errors)


def force_bytes(s, encoding="utf-8", strings_only=False, errors="strict"):
    if isinstance(s, bytes):
        if encoding == "utf-8":
            return s
        else:
            return s.decode("utf-8", errors).encode(encoding, errors)
    if strings_only and is_protected_type(s):
        return s
    if isinstance(s, memoryview):
        return bytes(s)
    return str(s).encode(encoding, errors)


def iri_to_uri(iri):
    if iri is None:
        return iri
    elif isinstance(iri, Promise):
        iri = str(iri)
    return quote(iri, safe="/#%[]=:;$&()+,!?*@'~")
_ascii_ranges = [[45, 46, 95, 126], range(65, 91), range(97, 123)]
_hextobyte = {
    (fmt % char).encode(): bytes((char,))
    for ascii_range in _ascii_ranges
    for char in ascii_range
    for fmt in ["%02x", "%02X"]
}
_hexdig = "0123456789ABCDEFabcdef"
_hextobyte.update(
    {(a + b).encode(): bytes.fromhex(a + b) for a in _hexdig[8:] for b in _hexdig}
)


def uri_to_iri(uri):
    if uri is None:
        return uri
    uri = force_bytes(uri)
    bits = uri.split(b"%")
    if len(bits) == 1:
        iri = uri
    else:
        parts = [bits[0]]
        append = parts.append
        hextobyte = _hextobyte
        for item in bits[1:]:
            hex = item[:2]
            if hex in hextobyte:
                append(hextobyte[item[:2]])
                append(item[2:])
            else:
                append(b"%")
                append(item)
        iri = b"".join(parts)
    return repercent_broken_unicode(iri).decode()


def escape_uri_path(path):
    return quote(path, safe="/:@&+$,-_.!~*'()")


def punycode(domain):
    return domain.encode("idna").decode("ascii")


def repercent_broken_unicode(path):
    changed_parts = []
    while True:
        try:
            path.decode()
        except UnicodeDecodeError as e:
            repercent = quote(path[e.start : e.end], safe=b"/#%[]=:;$&()+,!?*@'~")
            changed_parts.append(path[: e.start] + repercent.encode())
            path = path[e.end :]
        else:
            return b"".join(changed_parts) + path


def filepath_to_uri(path):
    if path is None:
        return path
    return quote(str(path).replace("\\", "/"), safe="/~!*()'")


def get_system_encoding():
    try:
        encoding = locale.getlocale()[1] or "ascii"
        codecs.lookup(encoding)
    except Exception:
        encoding = "ascii"
    return encoding


DEFAULT_LOCALE_ENCODING = get_system_encoding()