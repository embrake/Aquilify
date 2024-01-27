from typing import Dict, Optional
from .base import AXToken, Algorithm
from .types import JsonType
from .exception import AXTokenException

TOKEN_TYPE_ACCESS = 'access'
TOKEN_TYPE_REFRESH = 'refresh'

class AXTokenVerifier:
    def __init__(self, secret_key: str, algorithm: Algorithm = Algorithm.HS256) -> None:
        """
        Initialize AXTokenVerifier.

        Args:
            secret_key (str): The secret key for verification.
        """
        self.secret_key: str = secret_key
        self.algorithm: Algorithm = algorithm

    def verify(self, ax_token: str, verify_type: Optional[str] = None) -> Dict[str, JsonType]:
        """
        Verify an AXToken.

        Args:
            ax_token (str): The token to be verified.
            verify_type (Optional[str]): The expected token type.

        Returns:
            Dict[str, JsonType]: The decoded payload.

        Raises:
            AXTokenException: If verification fails.
        """
        decoded_token: Dict[str, JsonType] = AXToken(self.secret_key, self.algorithm).decode(ax_token)

        if verify_type:
            self._verify_token_type(decoded_token, verify_type)

        return decoded_token

    def _verify_token_type(self, decoded_token: Dict[str, JsonType], expected_type: str) -> None:
        """
        Verify the token type.

        Args:
            decoded_token (Dict[str, JsonType]): The decoded token payload.
            expected_type (str): The expected token type.

        Raises:
            AXTokenException: If the token type is invalid.
        """
        token_type: str = decoded_token.get('type', '')
        if token_type != expected_type:
            raise AXTokenException(f"Invalid token type. Expected {expected_type} token.")

class AXAccessToken(AXToken):
    def __init__(self, secret_key: str, exp: Optional[int] = None, algorithm: Algorithm = Algorithm.HS256) -> None:
        """
        Initialize AXAccessToken.

        Args:
            secret_key (str): The secret key for encoding and decoding.
            exp (Optional[int]): Expiration time for the token.
        """
        super().__init__(secret_key, algorithm)
        self.exp: Optional[int] = exp

    def encode(self, user_id: str, issuer: Optional[str] = None, audience: Optional[str] = None, subject: Optional[str] = None,
               ax_id: Optional[str] = None, custom_claims: Optional[Dict[str, JsonType]] = None) -> str:
        """
        Encode an access token.

        Args:
            user_id (str): The user ID.
            issuer (Optional[str]): Token issuer.
            audience (Optional[str]): Token audience.
            subject (Optional[str]): Token subject.
            ax_id (Optional[str]): AXI ID.
            custom_claims (Optional[Dict[str, JsonType]]): Additional custom claims.

        Returns:
            str: The encoded access token.
        """
        self.payload = {'sub': user_id, 'type': TOKEN_TYPE_ACCESS}

        if issuer:
            self.payload['iss'] = issuer

        if audience:
            self.payload['aud'] = audience

        if subject:
            self.payload['sub'] = subject

        if ax_id:
            self.payload['axi'] = ax_id

        return super().encode(exp=self.exp, custom_claims=custom_claims)

class AXRefreshToken(AXToken):
    def __init__(self, secret_key: str, exp: Optional[int] = None, algorithm: Algorithm = Algorithm.HS256) -> None:
        """
        Initialize AXRefreshToken.

        Args:
            secret_key (str): The secret key for encoding and decoding.
            exp (Optional[int]): Expiration time for the token.
        """
        super().__init__(secret_key, algorithm)
        self.exp: Optional[int] = exp

    def encode(self, user_id: str, ax_id: Optional[str] = None, custom_claims: Optional[Dict[str, JsonType]] = None) -> str:
        """
        Encode a refresh token.

        Args:
            user_id (str): The user ID.
            ax_id (Optional[str]): AXI ID.
            custom_claims (Optional[Dict[str, JsonType]]): Additional custom claims.

        Returns:
            str: The encoded refresh token.
        """
        self.payload = {'sub': user_id, 'type': TOKEN_TYPE_REFRESH}

        if ax_id:
            self.payload['axi'] = ax_id

        return super().encode(exp=self.exp, custom_claims=custom_claims)

class AXTokenManager:
    def __init__(self, secret_key: str, algorithm: Algorithm = Algorithm.HS256, access_exp: int = 15 * 60, refresh_exp: int = 7 * 24 * 60 * 60) -> None:
        """
        Initialize AXTokenManager.

        Args:
            secret_key (str): The secret key for encoding and decoding.
            algorithm (Algorithm): The algorithm for encoding and decoding.
            access_exp (int): Expiration time for access tokens.
            refresh_exp (int): Expiration time for refresh tokens.
        """
        self.secret_key: str = secret_key
        self.algorithm: Algorithm = algorithm
        self.access_exp: int = access_exp
        self.refresh_exp: int = refresh_exp
        self.access_token: AXAccessToken = AXAccessToken(secret_key, exp=self.access_exp, algorithm=self.algorithm)
        self.refresh_token: AXRefreshToken = AXRefreshToken(secret_key, exp=self.refresh_exp, algorithm=self.algorithm)

    def generate_tokens(self, user_id: str, issuer: Optional[str] = None, audience: Optional[str] = None, subject: Optional[str] = None,
                        ax_id: Optional[str] = None, custom_claims: Optional[Dict[str, JsonType]] = None) -> Dict[str, str]:
        """
        Generate access and refresh tokens.

        Args:
            user_id (str): The user ID.
            issuer (Optional[str]): Token issuer.
            audience (Optional[str]): Token audience.
            subject (Optional[str]): Token subject.
            ax_id (Optional[str]): AXI ID.
            custom_claims (Optional[Dict[str, JsonType]]): Additional custom claims.

        Returns:
            Dict[str, str]: A dictionary containing 'access_token' and 'refresh_token'.

        Raises:
            AXTokenException: If an error occurs during token generation.
        """
        try:
            access_token: str = self.access_token.encode(user_id, issuer=issuer, audience=audience, subject=subject, ax_id=ax_id, custom_claims=custom_claims)
            refresh_token: str = self.refresh_token.encode(user_id, ax_id=ax_id, custom_claims=custom_claims)
            return {'access_token': access_token, 'refresh_token': refresh_token}
        except AXTokenException as e:
            raise AXTokenException(f"Error generating tokens: {str(e)}")

    def verify_access_token(self, access_token: str) -> Dict[str, JsonType]:
        """
        Verify an access token.

        Args:
            access_token (str): The access token to be verified.

        Returns:
            Dict[str, JsonType]: The decoded payload.

        Raises:
            AXTokenException: If an error occurs during verification.
        """
        try:
            verify_type: Optional[str] = TOKEN_TYPE_ACCESS
            return AXTokenVerifier(self.secret_key, self.algorithm).verify(access_token, verify_type=verify_type)
        except AXTokenException as e:
            raise AXTokenException(f"Error verifying access token: {str(e)}")

    def refresh_access_token(self, refresh_token: str, ax_id: Optional[str] = None) -> str:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token (str): The refresh token.
            ax_id (Optional[str]): AXI ID.

        Returns:
            str: The refreshed access token.

        Raises:
            AXTokenException: If an error occurs during token refresh.
        """
        try:
            decoded_token: Dict[str, JsonType] = AXToken(self.secret_key, algorithm=self.algorithm).decode(refresh_token)

            AXTokenVerifier(self.secret_key, self.algorithm)._verify_token_type(decoded_token, TOKEN_TYPE_REFRESH)

            if ax_id and decoded_token.get('axi') != ax_id:
                raise AXTokenException("Mismatched ax_id in refresh token")

            user_id: str = decoded_token.get('sub', '')
            custom_claims: Dict[str, JsonType] = {key: decoded_token[key] for key in decoded_token if key not in ('sub', 'exp', 'iat')}
            return self.access_token.encode(user_id, subject=user_id, ax_id=ax_id, custom_claims=custom_claims)
        except AXTokenException as e:
            raise AXTokenException(f"Error refreshing access token: {str(e)}")
