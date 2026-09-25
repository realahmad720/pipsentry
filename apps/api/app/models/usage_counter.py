import uuid
from datetime import date as date_

from sqlalchemy import Date, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UsageCounter(Base):
    __tablename__ = "usage_counters"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_usage_counters_user_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    api_calls_made: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_estimate_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
