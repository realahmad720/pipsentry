import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


class IngestedSourceCreate(BaseModel):
    source_type: str  # youtube (pdf/txt go through the /sources/upload endpoint instead)
    source_url: str
    title: str | None = None
    tags: list[str] = []

    @model_validator(mode="after")
    def _only_youtube_via_json(self) -> "IngestedSourceCreate":
        if self.source_type != "youtube":
            raise ValueError("source_type must be 'youtube'; upload PDF/TXT via /knowledge/sources/upload")
        return self


class IngestedSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: str
    source_url: str | None
    title: str | None
    tags: list[str]
    chunk_count: int
    vector_collection_name: str
    status: str
    created_at: datetime
