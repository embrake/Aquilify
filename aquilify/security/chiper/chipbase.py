from .base import AXToken, NotBefore, JsonType, Algorithm
import typing

def encode(
    payload: typing.Dict[str, JsonType],
    secret_key: str,
    algorithm: Algorithm = Algorithm.HS256,
    exp: typing.Optional[int] = None,
    nbf: typing.Optional[NotBefore] = None,
    issuer: typing.Optional[str] = None,
    audience: typing.Optional[str] = None, 
    subject: typing.Optional[str] = None,
    custom_claims: typing.Optional[typing.Dict[str, JsonType]] = None
) -> typing.Union[typing.Callable[..., AXToken], str]:
    """
    Encode a payload into an AXToken.

    Args:
        payload (Dict[str, JsonType]): The payload to be encoded.
        secret_key (str): The secret key used for encoding.
        algorithm (Algorithm): The algorithm to be used for encoding.
        exp (Optional[int]): Expiration time of the token in seconds.
        nbf (Optional[NotBefore]): Not Before time of the token.
        issuer (Optional[str]): Token issuer.
        audience (Optional[str]): Token audience.
        subject (Optional[str]): Token subject.
        custom_claims (Optional[Dict[str, JsonType]]): Additional custom claims.

    Returns:
        Union[Callable[..., AXToken], str]: Either an AXToken instance or a string.

    """
    _axtoken = AXToken(secret_key, algorithm)
    _axtoken.payload: typing.Dict[str, JsonType] = {'sub': payload, 'type': 'basic'}
    
    if issuer:
        _axtoken.payload['iss'] = issuer

    if audience:
        _axtoken.payload['aud'] = audience

    if subject:
        _axtoken.payload['sub'] = subject
        
    return _axtoken.encode(exp=exp, nbf=nbf, custom_claims=custom_claims)
        
def decode(
    ax_token: str,
    secret_key: str,
    algorithm: Algorithm = Algorithm.HS256
) -> typing.Dict[str, JsonType]:
    """
    Decode an AXToken.

    Args:
        ax_token (str): The token to be decoded.
        secret_key (str): The secret key used for decoding.
        algorithm (Algorithm): The algorithm to be used for decoding.

    Returns:
        Dict[str, JsonType]: The decoded payload.

    """
    _axtoken = AXToken(secret_key, algorithm)
    return _axtoken.decode(ax_token)
