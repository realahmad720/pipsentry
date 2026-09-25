"""Symmetric encryption for values that must be encrypted at rest (Section 11):
per-user Telegram chat ids and user-registered connector credentials.

Fernet (AES-128-CBC + HMAC) rather than a hand-rolled scheme — it's the
standard "encrypt a small secret with one key" primitive in `cryptography`,
authenticated so tampered ciphertext fails to decrypt rather than silently
returning garbage.
"""

from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class EncryptionNotConfigured(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    if not settings.field_encryption_key:
        raise EncryptionNotConfigured("FIELD_ENCRYPTION_KEY is not configured")
    return Fernet(settings.field_encryption_key)


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Could not decrypt value — wrong key or corrupted data") from exc
