"""Telegram account-linking codes: `GET /telegram/link-code` (authenticated)
hands the dashboard a short-lived token; the user sends it to the bot as
`/start <token>`, and the webhook (routers/telegram.py) resolves it back to
a user id. No extra table — it's a signed, self-expiring Fernet token (the
same key that encrypts chat ids at rest, Section 11), not a stored secret.
"""

import uuid

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

LINK_CODE_TTL_SECONDS = 600


def _fernet() -> Fernet:
    if not settings.field_encryption_key:
        raise RuntimeError("FIELD_ENCRYPTION_KEY is not configured")
    return Fernet(settings.field_encryption_key)


def generate_linking_code(user_id: uuid.UUID) -> str:
    return _fernet().encrypt(str(user_id).encode("utf-8")).decode("utf-8")


def resolve_linking_code(code: str) -> uuid.UUID | None:
    try:
        raw = _fernet().decrypt(code.encode("utf-8"), ttl=LINK_CODE_TTL_SECONDS)
        return uuid.UUID(raw.decode("utf-8"))
    except (InvalidToken, ValueError):
        return None
