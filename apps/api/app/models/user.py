import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    auth_provider_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    plan_tier: Mapped[str] = mapped_column(String, nullable=False, default="free")
    # Fernet ciphertext, never the raw chat id — see app.core.crypto (Section 11).
    telegram_chat_id_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def vector_collection_name(self) -> str:
        return f"kb_{self.id}"
