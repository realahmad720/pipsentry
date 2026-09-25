import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AdvisoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    symbol: str
    timeframe: str
    action: str
    confidence_score: float
    payload_json: dict
    outcome: str
    outcome_at: datetime | None
    delivered_at: datetime


class EvaluateRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
