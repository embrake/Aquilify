import hashlib
import hmac
import secrets

from ..settings import settings
from .encoding import force_bytes


class InvalidAlgorithm(ValueError):
    pass


def salted_hmac(key_salt, value, secret=None, *, algorithm="sha1"):
    if secret is None:
        secret = settings.SECRET_KEY

    key_salt = force_bytes(key_salt)
    secret = force_bytes(secret)
    try:
        hasher = getattr(hashlib, algorithm)
    except AttributeError as e:
        raise InvalidAlgorithm(
            "%r is not an algorithm accepted by the hashlib module." % algorithm
        ) from e
    key = hasher(key_salt + secret).digest()
    return hmac.new(key, msg=force_bytes(value), digestmod=hasher)


RANDOM_STRING_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def get_random_string(length, allowed_chars=RANDOM_STRING_CHARS):
    return "".join(secrets.choice(allowed_chars) for i in range(length))


def constant_time_compare(val1, val2):
    return secrets.compare_digest(force_bytes(val1), force_bytes(val2))


def pbkdf2(password, salt, iterations, dklen=0, digest=None):
    if digest is None:
        digest = hashlib.sha256
    dklen = dklen or None
    password = force_bytes(password)
    salt = force_bytes(salt)
    return hashlib.pbkdf2_hmac(digest().name, password, salt, iterations, dklen)