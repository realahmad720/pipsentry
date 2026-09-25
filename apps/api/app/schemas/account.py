import uuid
from datetime import date as date_
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    plan: str
    status: str
    renewal_date: datetime | None
    monthly_token_budget: int


class UsageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    usage_date: date_ = Field(alias="date")
    tokens_used: int
    api_calls_made: int
    cost_estimate_usd: float


class AccountOut(BaseModel):
    id: uuid.UUID
    email: str
    plan_tier: str
    telegram_linked: bool
    subscription: SubscriptionOut | None
    month_to_date_tokens: int
    today_usage: UsageOut | None
