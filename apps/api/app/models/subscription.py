import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String, nullable=False, default="free")
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    renewal_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    monthly_token_budget: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
