from ..wrappers import Response
from .content import error404, error405, error400, error403, error500, error502, error429

class HTTPException(Exception):
    def __init__(self, detail, status_code):
        self.detail = detail
        self.status_code = status_code
        super().__init__(f"{self.status_code} {self.detail}")
        
class HTTPBaseException(Response, HTTPException):
    def __init__(self, details = '', status_code=500):
        super().__init__(details, status_code=status_code)
        
class ImproperlyConfigured(Exception):
    pass

class NotFound(Response, HTTPException):
    def __init__(self, status_code=404):
        super().__init__(error404(), status_code=status_code, content_type="text/html")

class BadRequest(Response, HTTPException):
    def __init__(self, detail="Bad Request", exception=None):
        self.detail = error400()
        self.exception = exception
        super().__init__(content=detail, status_code=400, content_type='text/html')

class Forbidden(Response, HTTPException):
    def __init__(self, detail=""):
        self.detail = error403(detail)
        super().__init__(content=self.detail, status_code=403, content_type='text/html')

class BadGateway(Response, HTTPException):
    def __init__(self, detail="Bad Gateway"):
        self.detail = error502()
        super().__init__(content=self.detail, status_code=502, content_type='text/html')

class Unauthorized(Response, HTTPException):
    def __init__(self, detail="Unauthorized"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=401, content_type='text/html')

class MethodNotAllowed(Response, HTTPException):
    def __init__(self, allowed_methods=None):
        super().__init__(content=error405(), status_code=405, content_type='text/html')

class InternalServerError(Response, HTTPException):
    def __init__(self, detail="Internal Server Error"):
        self.detail = error500(detail)
        super().__init__(content=self.detail, status_code=500, content_type='text/html')

class Conflict(Response, HTTPException):
    def __init__(self, detail="Conflict"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=409, content_type='text/html')

class Gone(Response, HTTPException):
    def __init__(self, detail="Gone"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=410, content_type='text/html')

class LengthRequired(Response, HTTPException):
    def __init__(self, detail="Length Required"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=411, content_type='text/html')

class ImATeapot(Response, HTTPException):
    def __init__(self, detail="ImATeapot"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=418, content_type='text/html')

class PreconditionRequired(Response, HTTPException):
    def __init__(self, detail="Preconditional Required"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=428, content_type='text/html')

class PreconditionFailed(Response, HTTPException):
    def __init__(self, detail="Precondition Failed"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=412, content_type='text/html')

class UnsupportedMediaType(Response, HTTPException):
    def __init__(self, detail="Unsupported Media Type"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=415, content_type='text/html')

class UnprocessableEntity(Response, HTTPException):
    def __init__(self, detail="Unprocessable Entity"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=422, content_type='text/html')

class TooManyRequests(Response, HTTPException):
    def __init__(self, detail=""):
        self.detail = error429(detail)
        super().__init__(content=self.detail, status_code=429, content_type='text/html')

class NotImplemented(Response, HTTPException):
    def __init__(self, detail="Not Implemented"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=501, content_type='text/html')

class ServiceUnavailable(Response, HTTPException):
    def __init__(self, detail="Service Unavailable"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=503, content_type='text/html')

class GatewayTimeout(Response, HTTPException):
    def __init__(self, detail="Gateway Timeout"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=504, content_type='text/html')

class HTTPVersionNotSupported(Response, HTTPException):
    def __init__(self, detail="HTTP Version Not Supported"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=505, content_type='text/html')

class VariantAlsoNegotiates(Response, HTTPException):
    def __init__(self, detail="Variant Also Negotiates"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=506, content_type='text/html')

class InsufficientStorage(Response, HTTPException):
    def __init__(self, detail="Insufficient Storage"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=507, content_type='text/html')

class LoopDetected(Response, HTTPException):
    def __init__(self, detail="Loop Detected"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=508, content_type='text/html')

class NotExtended(Response, HTTPException):
    def __init__(self, detail="Not Extended"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=510, content_type='text/html')

class NetworkAuthenticationRequired(Response, HTTPException):
    def __init__(self, detail="Network Authentication Required"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=511, content_type='text/html')

class RequestTimeout(Response, HTTPException):
    def __init__(self, detail="Request Timeout"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=408, content_type='text/html')

class NotAcceptable(Response, HTTPException):
    def __init__(self, detail="Not Acceptable"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=406, content_type='text/html')

class PaymentRequired(Response, HTTPException):
    def __init__(self, detail="Payement Required"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=402, content_type='text/html')

class PayloadTooLarge(Response, HTTPException):
    def __init__(self, detail="Payload Too Large"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=413, content_type='text/html')

class ProxyAuthenticationRequired(Response, HTTPException):
    def __init__(self, detail="Proxy Authentication Required"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=407, content_type='text/html')

class RequestURITooLong(Response, HTTPException):
    def __init__(self, detail="Request-URI Too Long"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=414, content_type='text/html')

class RequestedRangeNotSatisfiable(Response, HTTPException):
    def __init__(self, detail="Requested Range Not Satisfiable"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=416, content_type='text/html')

class ExpectationFailed(Response, HTTPException):
    def __init__(self, detail="Expectation Failed"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=417, content_type='text/html')

class MisdirectedRequest(Response, HTTPException):
    def __init__(self, detail="Misdirected Request"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=421, content_type='text/html')

class Locked(Response, HTTPException):
    def __init__(self, detail="Locked"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=423, content_type='text/html')

class FailedDependency(Response, HTTPException):
    def __init__(self, detail="Failed Dependency"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=424, content_type='text/html')

class UpgradeRequired(Response, HTTPException):
    def __init__(self, detail="Upgrade Required"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=426, content_type='text/html')

class RequestHeaderFieldsTooLarge(Response, HTTPException):
    def __init__(self, detail="Request Header Fields Too Large"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=431, content_type='text/html')

class UnavailableForLegalReasons(Response, HTTPException):
    def __init__(self, detail="Unavailable For Legal Reasons"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=451, content_type='text/html')

class ClientClosedRequest(Response, HTTPException):
    def __init__(self, detail="Client Closed Request"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=499, content_type='text/html')

class NetworkConnectTimeoutError(Response, HTTPException):
    def __init__(self, detail="Network Connect Timeout Error"):
        self.detail = f"""<h1>{detail}</h1>"""
        super().__init__(content=self.detail, status_code=599, content_type='text/html')
