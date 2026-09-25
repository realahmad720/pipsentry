"""Local-disk storage for uploaded PDF/TXT source files, keyed by user/source
id so files never collide across tenants. Swap for S3-compatible blob storage
before running the API as more than one instance (see app.config.uploads_dir).
"""

import uuid
from pathlib import Path

from app.config import settings


def _tenant_dir(user_id: uuid.UUID) -> Path:
    path = Path(settings.uploads_dir) / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_uploaded_file(user_id: uuid.UUID, source_id: uuid.UUID, filename: str, raw_bytes: bytes) -> str:
    suffix = Path(filename).suffix
    path = _tenant_dir(user_id) / f"{source_id}{suffix}"
    path.write_bytes(raw_bytes)
    return str(path)


def load_uploaded_file(path: str) -> bytes:
    return Path(path).read_bytes()


def delete_uploaded_file(path: str) -> None:
    Path(path).unlink(missing_ok=True)
