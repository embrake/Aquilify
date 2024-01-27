import base64
import json
import datetime
import hashlib
import hmac
from enum import Enum
from typing import Optional, Dict, Union, Type, Callable

from .encoder import EnumEncoder
from .exception import AXTokenException
from .types import JsonType

class Algorithm(Enum):
    HS256 = 'HS256'
    HS384 = 'HS384'
    HS512 = 'HS512'

class NotBefore:
    def __init__(self, nbf_time: int) -> None:
        """
        Initialize NotBefore object.

        Args:
            nbf_time (int): The Not Before time in seconds.
        """
        self.nbf_time = nbf_time

    def validate(self, current_time: int) -> None:
        """
        Validate the Not Before time.

        Args:
            current_time (int): The current time in seconds.

        Raises:
            AXTokenException: If the token is not yet valid.
        """
        if current_time < self.nbf_time:
            raise AXTokenException("Token is not yet valid")

class AXToken:
    def __init__(self, secret_key: str, algorithm: Algorithm = Algorithm.HS256) -> None:
        """
        Initialize AXToken object.

        Args:
            secret_key (str): The secret key for encoding and decoding.
            algorithm (Algorithm): The algorithm to be used for encoding and decoding.
        """
        self.secret_key: str = secret_key
        self.algorithm: Algorithm = algorithm
        self.headers: Dict[str, Union[str, Algorithm]] = {'typ': 'AXCipher', 'alg': algorithm}
        self.payload: Dict[str, JsonType] = {}

    def _generate_axi_id(self) -> str:
        """
        Generate AXI ID using HMAC.

        Returns:
            str: The generated AXI ID.
        """
        return base64.urlsafe_b64encode(hmac.new(self.secret_key.encode('utf-8'), b'axi', hashlib.sha256).digest()).decode('utf-8')

    def encode(self, exp: Optional[int] = None, nbf: Optional[NotBefore] = None, custom_claims: Optional[Dict[str, JsonType]] = None) -> str:
        """
        Encode a payload into an AXToken.

        Args:
            exp (Optional[int]): Expiration time of the token in seconds.
            nbf (Optional[NotBefore]): Not Before time of the token.
            custom_claims (Optional[Dict[str, JsonType]]): Additional custom claims.

        Returns:
            str: The encoded AXToken.
        """
        current_time: int = int(datetime.datetime.utcnow().timestamp())

        if nbf:
            nbf.validate(current_time)

        self.payload['iat'] = current_time
        self.payload['axi'] = self._generate_axi_id()

        if exp is not None:
            self.payload['exp'] = current_time + exp

        if custom_claims:
            self.payload.update(custom_claims)

        encoded_header: str = self._base64_encode(self.headers)
        encoded_payload: str = self._base64_encode(self.payload)

        signature: str = self._sign(encoded_header + '.' + encoded_payload)

        ax_token: str = f"{encoded_header}.{encoded_payload}.{signature}"
        return ax_token

    def decode(self, ax_token: str) -> Dict[str, JsonType]:
        """
        Decode an AXToken.

        Args:
            ax_token (str): The token to be decoded.

        Returns:
            Dict[str, JsonType]: The decoded payload.
        """
        try:
            encoded_header, encoded_payload, signature = ax_token.split('.')
            self.headers = json.loads(self._base64_decode(encoded_header))
            self.payload = json.loads(self._base64_decode(encoded_payload))

            algorithm: Algorithm = Algorithm(self.headers.get('alg', ''))
            if not algorithm:
                raise AXTokenException("Missing algorithm in header")

            self._validate_signature(encoded_header, encoded_payload, signature)

            current_time: int = int(datetime.datetime.utcnow().timestamp())

            for claim in ['exp', 'nbf', 'iat']:
                self._validate_claim(claim, current_time)

            return self.payload
        except Exception as e:
            raise AXTokenException(f"Error decoding token: {str(e)}")

    def _base64_encode(self, data: Dict[str, JsonType]) -> str:
        """
        Base64 encode a JSON data.

        Args:
            data (Dict[str, JsonType]): The data to be encoded.

        Returns:
            str: The base64 encoded string.
        """
        return base64.urlsafe_b64encode(json.dumps(data, cls=EnumEncoder).encode('utf-8')).decode('utf-8')

    def _base64_decode(self, data: str) -> str:
        """
        Base64 decode a string.

        Args:
            data (str): The base64 encoded string.

        Returns:
            str: The decoded string.
        """
        padding_length: int = 4 - (len(data) % 4)
        padded_data: str = data + '=' * padding_length
        return base64.urlsafe_b64decode(padded_data.encode('utf-8')).decode('utf-8')

    def _sign(self, data: str) -> str:
        """
        Sign the data using HMAC.

        Args:
            data (str): The data to be signed.

        Returns:
            str: The base64 encoded signature.
        """
        if self.algorithm == Algorithm.HS256:
            hash_algorithm: Type[Callable] = hashlib.sha256
        elif self.algorithm == Algorithm.HS384:
            hash_algorithm: Type[Callable] = hashlib.sha384
        elif self.algorithm == Algorithm.HS512:
            hash_algorithm: Type[Callable] = hashlib.sha512
        else:
            raise AXTokenException("Unsupported algorithm")

        key: bytes = self.secret_key.encode('utf-8')
        hashed: hmac.HMAC = hmac.new(key, msg=data.encode('utf-8'), digestmod=hash_algorithm)
        return base64.urlsafe_b64encode(hashed.digest()).decode('utf-8')

    def _validate_signature(self, encoded_header: str, encoded_payload: str, signature: str) -> None:
        """
        Validate the token signature.

        Args:
            encoded_header (str): The base64 encoded header.
            encoded_payload (str): The base64 encoded payload.
            signature (str): The signature to be validated.

        Raises:
            AXTokenException: If the signature is invalid.
        """
        calculated_signature: str = self._sign(encoded_header + '.' + encoded_payload)
        if not hmac.compare_digest(calculated_signature, signature):
            raise AXTokenException("Invalid signature")

    def _validate_claim(self, claim: str, current_time: int) -> None:
        """
        Validate a specific claim in the payload.

        Args:
            claim (str): The claim to be validated.
            current_time (int): The current time in seconds.

        Raises:
            AXTokenException: If the claim validation fails.
        """
        if claim in self.payload:
            claim_value: JsonType = self.payload[claim]

            if claim == 'exp' and current_time > claim_value:
                raise AXTokenException(f"Token {claim} has passed")

            if claim == 'nbf' and current_time < claim_value:
                raise AXTokenException(f"Token {claim} is not yet valid")

            if claim == 'iat' and not isinstance(claim_value, int):
                raise AXTokenException(f"Invalid {claim} claim in token")
