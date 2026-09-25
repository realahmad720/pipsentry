import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WatchlistCreate(BaseModel):
    symbol: str
    timeframe: str


class WatchlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    timeframe: str
    active: bool
    forward_test_status: str
    forward_test_started_at: datetime | None
    forward_test_ends_at: datetime | None
