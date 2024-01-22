from aquilify.utils.http import parse_etags, parse_http_date_safe, quote_etag
from aquilify.utils._log import log_response
from aquilify.utils.regex_helper import _lazy_re_compile

from aquilify.wrappers import Response, Request

from typing import Any

from hashlib import md5

cc_delim_re = _lazy_re_compile(r"\s*,\s*")

def serialize_content(content: Any) -> bytes:
    if isinstance(content, (str, bytes, bytearray, memoryview)):
        return bytes(content, 'utf-8') if isinstance(content, str) else bytes(content)

    elif isinstance(content, (list, tuple, set, dict)):
        return str(content).encode('utf-8')

    else:
        raise TypeError(f"Unsupported content type: {type(content)}")

def set_response_etag(response: Response) -> Response:
    if not response.streaming and response.content:
        serialized_content = serialize_content(response.content)
        etag = md5(serialized_content).hexdigest()
        response.headers["ETag"] = quote_etag(etag)

    return response

def _precondition_failed(request):
    response = Response(status=412)
    log_response(
        "Precondition Failed: %s",
        request.path,
        response=response,
        request=request,
    )
    return response

def get_conditional_response(request: Request, etag=None, last_modified=None, response: Response=None):
    if response and not (200 <= response.status_code < 300):
        return response

    if_match_etags = parse_etags(request.headers.get("if-match", ""))
    if_unmodified_since = request.headers.get("if-unmodified-since")
    if_unmodified_since = if_unmodified_since and parse_http_date_safe(
        if_unmodified_since
    )
    if_none_match_etags = parse_etags(request.headers.get("if-none-match", ""))
    if_modified_since = request.headers.get("if-modified-since")
    if_modified_since = if_modified_since and parse_http_date_safe(if_modified_since)

    if if_match_etags and not _if_match_passes(etag, if_match_etags):
        return _precondition_failed(request)

    if (
        not if_match_etags
        and if_unmodified_since
        and not _if_unmodified_since_passes(last_modified, if_unmodified_since)
    ):
        return _precondition_failed(request)

    if if_none_match_etags and not _if_none_match_passes(etag, if_none_match_etags):
        if request.method in ("GET", "HEAD"):
            return response
        else:
            return _precondition_failed(request)
    if (
        not if_none_match_etags
        and if_modified_since
        and not _if_modified_since_passes(last_modified, if_modified_since)
        and request.method in ("GET", "HEAD")
    ):
        return response
    return response


def _if_match_passes(target_etag, etags):
    if not target_etag:
        return False
    elif etags == ["*"]:
        return True
    elif target_etag.startswith("W/"):
        return False
    else:
        return target_etag in etags


def _if_unmodified_since_passes(last_modified, if_unmodified_since):
    return last_modified and last_modified <= if_unmodified_since


def _if_none_match_passes(target_etag, etags):
    if not target_etag:
        return True
    elif etags == ["*"]:
        return False
    else:
        target_etag = target_etag.strip("W/")
        etags = (etag.strip("W/") for etag in etags)
        return target_etag not in etags


def _if_modified_since_passes(last_modified, if_modified_since):
    return not last_modified or last_modified > if_modified_since

def patch_vary_headers(response, newheaders):
    if response.headers.get("Vary"):
        vary_headers = cc_delim_re.split(response.headers["Vary"])
    else:
        vary_headers = []
    existing_headers = {header.lower() for header in vary_headers}
    additional_headers = [
        newheader
        for newheader in newheaders
        if newheader.lower() not in existing_headers
    ]
    vary_headers += additional_headers
    if "*" in vary_headers:
        response.headers["Vary"] = "*"
    else:
        response.headers["Vary"] = ", ".join(vary_headers)