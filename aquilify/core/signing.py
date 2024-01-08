
import base64
import datetime
import json
import time
import warnings
import zlib

from aquilify.settings import settings
from aquilify.utils.crypto import constant_time_compare, salted_hmac
from aquilify.utils.encoding import force_bytes
from aquilify.utils.module_loading import import_string
from aquilify.utils.regex_helper import _lazy_re_compile

_SEP_UNSAFE = _lazy_re_compile(r"^[A-z0-9-_=]*$")
BASE62_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


class BadSignature(Exception):
    """Signature does not match."""

    pass


class SignatureExpired(BadSignature):
    """Signature timestamp is older than required max_age."""

    pass


def b62_encode(s):
    if s == 0:
        return "0"
    sign = "-" if s < 0 else ""
    s = abs(s)
    encoded = ""
    while s > 0:
        s, remainder = divmod(s, 62)
        encoded = BASE62_ALPHABET[remainder] + encoded
    return sign + encoded


def b62_decode(s):
    if s == "0":
        return 0
    sign = 1
    if s[0] == "-":
        s = s[1:]
        sign = -1
    decoded = 0
    for digit in s:
        decoded = decoded * 62 + BASE62_ALPHABET.index(digit)
    return sign * decoded


def b64_encode(s):
    return base64.urlsafe_b64encode(s).strip(b"=")


def b64_decode(s):
    pad = b"=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def base64_hmac(salt, value, key, algorithm="sha1"):
    return b64_encode(
        salted_hmac(salt, value, key, algorithm=algorithm).digest()
    ).decode()


def _cookie_signer_key(key):
    return b"aquilify.http.cookies" + force_bytes(key)


def get_cookie_signer(salt="aquilify.core.signing.get_cookie_signer"):
    Signer = import_string(settings.SIGNING_BACKEND)
    return Signer(
        key=_cookie_signer_key(settings.SECRET_KEY),
        fallback_keys=map(_cookie_signer_key, settings.SECRET_KEY_FALLBACKS),
        salt=salt,
    )


class JSONSerializer:

    def dumps(self, obj):
        return json.dumps(obj, separators=(",", ":")).encode("latin-1")

    def loads(self, data):
        return json.loads(data.decode("latin-1"))


def dumps(
    obj, key=None, salt="aquilify.core.signing", serializer=JSONSerializer, compress=False
):
    return TimestampSigner(key=key, salt=salt).sign_object(
        obj, serializer=serializer, compress=compress
    )


def loads(
    s,
    key=None,
    salt="aquilify.core.signing",
    serializer=JSONSerializer,
    max_age=None,
    fallback_keys=None,
):
    """
    Reverse of dumps(), raise BadSignature if signature fails.

    The serializer is expected to accept a bytestring.
    """
    return TimestampSigner(
        key=key, salt=salt, fallback_keys=fallback_keys
    ).unsign_object(
        s,
        serializer=serializer,
        max_age=max_age,
    )


class Signer:
    def __init__(
        self,
        *args,
        key=None,
        sep=":",
        salt=None,
        algorithm=None,
        fallback_keys=None,
    ):
        self.key = key or settings.SECRET_KEY
        self.fallback_keys = (
            fallback_keys
            if fallback_keys is not None
            else settings.SECRET_KEY_FALLBACKS
        )
        self.sep = sep
        self.salt = salt or "%s.%s" % (
            self.__class__.__module__,
            self.__class__.__name__,
        )
        self.algorithm = algorithm or "sha256"
        if args:
            warnings.warn(
                f"Passing positional arguments to {self.__class__.__name__} is "
                f"deprecated.",
                stacklevel=2,
            )
            for arg, attr in zip(
                args, ["key", "sep", "salt", "algorithm", "fallback_keys"]
            ):
                if arg or attr == "sep":
                    setattr(self, attr, arg)
        if _SEP_UNSAFE.match(self.sep):
            raise ValueError(
                "Unsafe Signer separator: %r (cannot be empty or consist of "
                "only A-z0-9-_=)" % sep,
            )

    def signature(self, value, key=None):
        key = key or self.key
        return base64_hmac(self.salt + "signer", value, key, algorithm=self.algorithm)

    def sign(self, value):
        return "%s%s%s" % (value, self.sep, self.signature(value))

    def unsign(self, signed_value):
        if self.sep not in signed_value:
            raise BadSignature('No "%s" found in value' % self.sep)
        value, sig = signed_value.rsplit(self.sep, 1)
        for key in [self.key, *self.fallback_keys]:
            if constant_time_compare(sig, self.signature(value, key)):
                return value
        raise BadSignature('Signature "%s" does not match' % sig)

    def sign_object(self, obj, serializer=JSONSerializer, compress=False):
        data = serializer().dumps(obj)
        is_compressed = False

        if compress:
            compressed = zlib.compress(data)
            if len(compressed) < (len(data) - 1):
                data = compressed
                is_compressed = True
        base64d = b64_encode(data).decode()
        if is_compressed:
            base64d = "." + base64d
        return self.sign(base64d)

    def unsign_object(self, signed_obj, serializer=JSONSerializer, **kwargs):
        base64d = self.unsign(signed_obj, **kwargs).encode()
        decompress = base64d[:1] == b"."
        if decompress:
            base64d = base64d[1:]
        data = b64_decode(base64d)
        if decompress:
            data = zlib.decompress(data)
        return serializer().loads(data)


class TimestampSigner(Signer):
    def timestamp(self):
        return b62_encode(int(time.time()))

    def sign(self, value):
        value = "%s%s%s" % (value, self.sep, self.timestamp())
        return super().sign(value)

    def unsign(self, value, max_age=None):
        result = super().unsign(value)
        value, timestamp = result.rsplit(self.sep, 1)
        timestamp = b62_decode(timestamp)
        if max_age is not None:
            if isinstance(max_age, datetime.timedelta):
                max_age = max_age.total_seconds()
            age = time.time() - timestamp
            if age > max_age:
                raise SignatureExpired("Signature age %s > %s seconds" % (age, max_age))
        return value
