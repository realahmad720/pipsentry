import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TradeJournalEntryCreate(BaseModel):
    advisory_id: uuid.UUID | None = None
    symbol: str
    direction: str  # long | short
    entry_price: float
    exit_price: float | None = None
    size: float
    stop_loss: float | None = None
    take_profit: float | None = None
    pnl: float | None = None
    notes: str | None = None


class TradeJournalEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    advisory_id: uuid.UUID | None
    symbol: str
    direction: str
    entry_price: float
    exit_price: float | None
    size: float
    stop_loss: float | None
    take_profit: float | None
    pnl: float | None
    notes: str | None
    opened_at: datetime
    closed_at: datetime | None
