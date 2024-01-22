import time
import hmac
import hashlib
import base64
import secrets
import string

import typing

from aquilify.settings import settings

class AxOTPError(Exception):
    pass

class AxOTP:
    HASH_FUNCTIONS = {
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512
    }

    def __init__(
        self, 
        secret_key: typing.Union[str, typing.Hashable] = None, 
        interval: int = 30, 
        digits: int = 6, 
        hash_func: typing.Callable[[], typing.Hashable] ='sha1', 
        counter: int = 0
    ) -> None:
        self.interval: int = getattr(settings.AXOTP_INTERVAL, 30) or interval
        self.digits: int = getattr(settings.AXOTP_DIGITS, 30) or digits
        self.counter: int = getattr(settings.AXOTP_COUNTER, 30) or counter
        self.hash_func: typing.Callable[[], typing.Hashable] = self._get_hash_func(hash_func)
        
        if secret_key:
            self.secret_key: typing.Union[str, typing.Hashable] = getattr(settings.AXOTP_SECRET_KEY, 30) or self._decode_secret(secret_key)
        else:
            self.secret_key: typing.Union[str, typing.Hashable] = self.gen_secret_key()

    def _get_hash_func(
        self, 
        hash_func_name
    ) -> typing.Callable[[], typing.Hashable]:
        hash_func = self.HASH_FUNCTIONS.get(hash_func_name.lower())
        if not hash_func:
            raise AxOTPError(f"Hash function '{hash_func_name}' not supported")
        return hash_func

    def _decode_secret(
        self,
        secret_key
    ) -> typing.Union[bytes, typing.ByteString]:
        try:
            return base64.b32decode(secret_key, casefold=True)
        except (ValueError, TypeError):
            raise AxOTPError("Invalid secret key format")

    def gen_secret_key(
        self,
        length=16
    ) -> typing.Union[bytes, typing.ByteString]:
        alphabet = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length)).encode()

    def gen_base32_secret_key(
        self,
        length=16
    ) -> typing.Union[str, typing.AnyStr]:
        return base64.b32encode(self.gen_secret_key(length)).decode()

    def _generate_mackey(
        self,
        counter
    ) -> typing.Any:
        counter_bytes = int.to_bytes(counter, length=8, byteorder='big')
        hash_result = hmac.new(self.secret_key, counter_bytes, self.hash_func).digest()
        offset = hash_result[-1] & 0x0F
        code = hash_result[offset:offset + 4]
        value = int.from_bytes(code, 'big') & 0x7FFFFFFF
        return value % (10 ** self.digits)

    def generate(
        self,
        timestamp=None
    ) -> typing.Any:
        timestamp = int(time.time() / self.interval) if timestamp is None else timestamp
        return self._generate_mackey(timestamp)

    def verify(
        self,
        otp_input
    ) -> typing.Any:
        return self.generate() == int(otp_input)

    def hash_funcs(self) -> typing.List[typing.Callable[..., typing.Hashable]]:
        return list(self.HASH_FUNCTIONS.keys())