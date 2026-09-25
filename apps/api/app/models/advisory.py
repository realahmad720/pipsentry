import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Advisory(Base):
    __tablename__ = "advisories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    timeframe: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Graded after the fact by app.delivery.outcomes against entry/SL/TP inside
    # payload_json["execution_zones"] — no separate columns for those prices,
    # the payload is already the source of truth (Section 10).
    outcome: Mapped[str] = mapped_column(String, nullable=False, default="open")  # open|tp1|tp2|sl|expired
    outcome_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
