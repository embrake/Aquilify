import base64
import datetime
import re
import unicodedata
from binascii import Error as BinasciiError
from email.utils import formatdate
from urllib.parse import quote, unquote
from urllib.parse import urlencode as original_urlencode
from urllib.parse import urlparse

from aquilify.utils.datastructures import MultiValueDict
from aquilify.utils.regex_helper import _lazy_re_compile

# Based on RFC 9110 Appendix A.
ETAG_MATCH = _lazy_re_compile(
    r"""
    \A(      # start of string and capture group
    (?:W/)?  # optional weak indicator
    "        # opening quote
    [^"]*    # any sequence of non-quote characters
    "        # end quote
    )\Z      # end of string and capture group
""",
    re.X,
)

MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()
__D = r"(?P<day>[0-9]{2})"
__D2 = r"(?P<day>[ 0-9][0-9])"
__M = r"(?P<mon>\w{3})"
__Y = r"(?P<year>[0-9]{4})"
__Y2 = r"(?P<year>[0-9]{2})"
__T = r"(?P<hour>[0-9]{2}):(?P<min>[0-9]{2}):(?P<sec>[0-9]{2})"
RFC1123_DATE = _lazy_re_compile(r"^\w{3}, %s %s %s %s GMT$" % (__D, __M, __Y, __T))
RFC850_DATE = _lazy_re_compile(r"^\w{6,9}, %s-%s-%s %s GMT$" % (__D, __M, __Y2, __T))
ASCTIME_DATE = _lazy_re_compile(r"^\w{3} %s %s %s %s$" % (__M, __D2, __T, __Y))

RFC3986_GENDELIMS = ":/?#[]@"
RFC3986_SUBDELIMS = "!$&'()*+,;="


def urlencode(query, doseq=False):
    if isinstance(query, MultiValueDict):
        query = query.lists()
    elif hasattr(query, "items"):
        query = query.items()
    query_params = []
    for key, value in query:
        if value is None:
            raise TypeError(
                "Cannot encode None for key '%s' in a query string. Did you "
                "mean to pass an empty string or omit the value?" % key
            )
        elif not doseq or isinstance(value, (str, bytes)):
            query_val = value
        else:
            try:
                itr = iter(value)
            except TypeError:
                query_val = value
            else:
                query_val = []
                for item in itr:
                    if item is None:
                        raise TypeError(
                            "Cannot encode None for key '%s' in a query "
                            "string. Did you mean to pass an empty string or "
                            "omit the value?" % key
                        )
                    elif not isinstance(item, bytes):
                        item = str(item)
                    query_val.append(item)
        query_params.append((key, query_val))
    return original_urlencode(query_params, doseq)


def http_date(epoch_seconds=None):
    return formatdate(epoch_seconds, usegmt=True)


def parse_http_date(date):
    for regex in RFC1123_DATE, RFC850_DATE, ASCTIME_DATE:
        m = regex.match(date)
        if m is not None:
            break
    else:
        raise ValueError("%r is not in a valid HTTP date format" % date)
    try:
        tz = datetime.timezone.utc
        year = int(m["year"])
        if year < 100:
            current_year = datetime.datetime.now(tz=tz).year
            current_century = current_year - (current_year % 100)
            if year - (current_year % 100) > 50:
                year += current_century - 100
            else:
                year += current_century
        month = MONTHS.index(m["mon"].lower()) + 1
        day = int(m["day"])
        hour = int(m["hour"])
        min = int(m["min"])
        sec = int(m["sec"])
        result = datetime.datetime(year, month, day, hour, min, sec, tzinfo=tz)
        return int(result.timestamp())
    except Exception as exc:
        raise ValueError("%r is not a valid date" % date) from exc


def parse_http_date_safe(date):
    try:
        return parse_http_date(date)
    except Exception:
        pass


def base36_to_int(s):
    if len(s) > 13:
        raise ValueError("Base36 input too large")
    return int(s, 36)


def int_to_base36(i):
    char_set = "0123456789abcdefghijklmnopqrstuvwxyz"
    if i < 0:
        raise ValueError("Negative base36 conversion input.")
    if i < 36:
        return char_set[i]
    b36 = ""
    while i != 0:
        i, n = divmod(i, 36)
        b36 = char_set[n] + b36
    return b36


def urlsafe_base64_encode(s):
    return base64.urlsafe_b64encode(s).rstrip(b"\n=").decode("ascii")


def urlsafe_base64_decode(s):
    s = s.encode()
    try:
        return base64.urlsafe_b64decode(s.ljust(len(s) + len(s) % 4, b"="))
    except (LookupError, BinasciiError) as e:
        raise ValueError(e)


def parse_etags(etag_str):
    if etag_str.strip() == "*":
        return ["*"]
    else:
        etag_matches = (ETAG_MATCH.match(etag.strip()) for etag in etag_str.split(","))
        return [match[1] for match in etag_matches if match]


def quote_etag(etag_str):
    if ETAG_MATCH.match(etag_str):
        return etag_str
    else:
        return '"%s"' % etag_str


def is_same_domain(host, pattern):
    if not pattern:
        return False

    pattern = pattern.lower()
    return (
        pattern[0] == "."
        and (host.endswith(pattern) or host == pattern[1:])
        or pattern == host
    )


def url_has_allowed_host_and_scheme(url, allowed_hosts, require_https=False):
    if url is not None:
        url = url.strip()
    if not url:
        return False
    if allowed_hosts is None:
        allowed_hosts = set()
    elif isinstance(allowed_hosts, str):
        allowed_hosts = {allowed_hosts}
    return _url_has_allowed_host_and_scheme(
        url, allowed_hosts, require_https=require_https
    ) and _url_has_allowed_host_and_scheme(
        url.replace("\\", "/"), allowed_hosts, require_https=require_https
    )


def _url_has_allowed_host_and_scheme(url, allowed_hosts, require_https=False):
    if url.startswith("///"):
        return False
    try:
        url_info = urlparse(url)
    except ValueError:  # e.g. invalid IPv6 addresses
        return False
    if not url_info.netloc and url_info.scheme:
        return False
    if unicodedata.category(url[0])[0] == "C":
        return False
    scheme = url_info.scheme
    if not url_info.scheme and url_info.netloc:
        scheme = "http"
    valid_schemes = ["https"] if require_https else ["http", "https"]
    return (not url_info.netloc or url_info.netloc in allowed_hosts) and (
        not scheme or scheme in valid_schemes
    )


def escape_leading_slashes(url):
    if url.startswith("//"):
        url = "/%2F{}".format(url.removeprefix("//"))
    return url


def _parseparam(s):
    while s[:1] == ";":
        s = s[1:]
        end = s.find(";")
        while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
            end = s.find(";", end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        yield f.strip()
        s = s[end:]


def parse_header_parameters(line):
    parts = _parseparam(";" + line)
    key = parts.__next__().lower()
    pdict = {}
    for p in parts:
        i = p.find("=")
        if i >= 0:
            has_encoding = False
            name = p[:i].strip().lower()
            if name.endswith("*"):
                name = name[:-1]
                if p.count("'") == 2:
                    has_encoding = True
            value = p[i + 1 :].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
                value = value.replace("\\\\", "\\").replace('\\"', '"')
            if has_encoding:
                encoding, lang, value = value.split("'")
                value = unquote(value, encoding=encoding)
            pdict[name] = value
    return key, pdict


def content_disposition_header(as_attachment, filename):
    if filename:
        disposition = "attachment" if as_attachment else "inline"
        try:
            filename.encode("ascii")
            file_expr = 'filename="{}"'.format(
                filename.replace("\\", "\\\\").replace('"', r"\"")
            )
        except UnicodeEncodeError:
            file_expr = "filename*=utf-8''{}".format(quote(filename))
        return f"{disposition}; {file_expr}"
    elif as_attachment:
        return "attachment"
    else:
        return None
