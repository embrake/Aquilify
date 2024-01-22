from __future__ import annotations

import hashlib
import hmac
import os
import posixpath
import secrets
from typing import Optional, Tuple

SALT_CHARS: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
DEFAULT_PBKDF2_ITERATIONS: int = 600_000

Salt = str
HashedPassword = str
HashMethod = str
HashTuple = Tuple[HashedPassword, HashMethod]
PathComponent = str
SafePath = Optional[str]

_os_alt_seps: list[str] = [
    sep for sep in [os.sep, os.path.altsep] if sep is not None and sep != "/"
]


def gen_salt(length: int) -> Salt:
    if length <= 0:
        raise ValueError("Salt length must be at least 1.")

    return "".join(secrets.choice(SALT_CHARS) for _ in range(length))


def _hash_internal(method: str, salt: str, password: str) -> HashTuple:
    method, *args = method.split(":")
    salt = salt.encode()
    password = password.encode()

    if method == "scrypt":
        if not args:
            n = 2 ** 15
            r = 8
            p = 1
        else:
            try:
                n, r, p = map(int, args)
            except ValueError:
                raise ValueError("'scrypt' takes 3 arguments.") from None

        maxmem = 132 * n * r * p
        return (
            hashlib.scrypt(password, salt=salt, n=n, r=r, p=p, maxmem=maxmem).hex(),
            f"scrypt:{n}:{r}:{p}",
        )
    elif method == "pbkdf2":
        len_args = len(args)

        if len_args == 0:
            hash_name = "sha256"
            iterations = DEFAULT_PBKDF2_ITERATIONS
        elif len_args == 1:
            hash_name = args[0]
            iterations = DEFAULT_PBKDF2_ITERATIONS
        elif len_args == 2:
            hash_name = args[0]
            iterations = int(args[1])
        else:
            raise ValueError("'pbkdf2' takes 2 arguments.")

        return (
            hashlib.pbkdf2_hmac(hash_name, password, salt, iterations).hex(),
            f"pbkdf2:{hash_name}:{iterations}",
        )
    else:
        raise ValueError(f"Invalid hash method '{method}'.")


def hashpw(
    password: str, method: str = "scrypt", salt_length: int = 16
) -> str:
    salt: Salt = gen_salt(salt_length)
    h, actual_method = _hash_internal(method, salt, password)
    return f"{actual_method}${salt}${h}"


def checkpw(pwhash: str, password: str) -> bool:
    try:
        method, salt, hashval = pwhash.split("$", 2)
    except ValueError:
        return False

    return hmac.compare_digest(_hash_internal(method, salt, password)[0], hashval)


def safe_join(directory: str, *pathnames: PathComponent) -> SafePath:
    if not directory:
        directory = "."

    parts = [directory]

    for filename in pathnames:
        if filename != "":
            filename = posixpath.normpath(filename)

        if (
            any(sep in filename for sep in _os_alt_seps)
            or os.path.isabs(filename)
            or filename == ".."
            or filename.startswith("../")
        ):
            return None

        parts.append(filename)

    return posixpath.join(*parts)
