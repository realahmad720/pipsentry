import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConnectorCreate(BaseModel):
    name: str
    endpoint_url: str
    credentials: str | None = None  # raw bearer token/header value; encrypted before storage, never echoed back
    category: str = "custom"  # market_data | broker_readonly | news | custom


class ConnectorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    endpoint_url: str
    category: str
    status: str
    discovered_tools: list[dict]
    last_health_check_at: datetime | None
    created_at: datetime
