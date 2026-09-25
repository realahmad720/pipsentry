import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    timeframe: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Forward paper-test tracking (Phase 6 / Section 9.3 gate to live use).
    # not_started -> running -> passed | failed. No separate table: a forward
    # test is a property of one watchlist entry's trial period, not an
    # independent entity the spec's data model (Section 4) calls out.
    forward_test_status: Mapped[str] = mapped_column(String, nullable=False, default="not_started")
    forward_test_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    forward_test_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
