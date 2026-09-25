import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Connector(Base):
    """A user-registered MCP server (Section 20). `credentials_encrypted` holds
    a Fernet ciphertext blob (app.core.crypto) of whatever auth header/token the
    server needs; it is never returned to the client once set."""

    __tablename__ = "connectors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    endpoint_url: Mapped[str] = mapped_column(String, nullable=False)
    credentials_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False, default="custom")  # market_data|broker_readonly|news|custom
    status: Mapped[str] = mapped_column(String, nullable=False, default="unverified")  # unverified|healthy|unreachable|unauthorized
    discovered_tools: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    last_health_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
