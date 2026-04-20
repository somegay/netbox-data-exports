import bcrypt
import re

PASSWORD_MIN_LENGTH = 8
_PASSWORD_UPPERCASE_RE = re.compile(r"[A-Z]")
_PASSWORD_NUMBER_RE = re.compile(r"\d")
_PASSWORD_SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")

def hash_password(password: str) -> str:
     return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

def valid_password(password: str) -> bool:
    if not isinstance(password, str):
        return False

    if len(password) < PASSWORD_MIN_LENGTH:
        return False

    if not _PASSWORD_UPPERCASE_RE.search(password):
        return False

    if not _PASSWORD_NUMBER_RE.search(password):
        return False

    if not _PASSWORD_SPECIAL_RE.search(password):
        return False

    return True