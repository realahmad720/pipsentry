import uuid
from datetime import datetime

from sqlalchemy import ARRAY, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IngestedSource(Base):
    __tablename__ = "ingested_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String, nullable=False)  # youtube | pdf | txt
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vector_collection_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")  # pending | indexed | failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
