"""Cost & token budget guardrail (Section 8): checks remaining balance before
invoking Agent 4, and every agent call logs its usage to `usage_counters`.
Over budget returns STATUS: BUDGET_EXCEEDED rather than silently degrading.
"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.subscription import Subscription
from app.models.usage_counter import UsageCounter


def month_to_date_tokens(db: Session, user_id: uuid.UUID) -> int:
    today = date.today()
    rows = (
        db.query(UsageCounter)
        .filter(
            UsageCounter.user_id == user_id,
            UsageCounter.date >= today.replace(day=1),
        )
        .all()
    )
    return sum(r.tokens_used for r in rows)


def has_budget_remaining(db: Session, user_id: uuid.UUID) -> bool:
    subscription = db.query(Subscription).filter(Subscription.user_id == user_id).one_or_none()
    if subscription is None or subscription.monthly_token_budget <= 0:
        # No subscription row or an explicit 0 budget both mean "not provisioned
        # for live advisories" (Section 5: Free tier is watchlist-only).
        return False
    return month_to_date_tokens(db, user_id) < subscription.monthly_token_budget


def log_usage(db: Session, user_id: uuid.UUID, tokens: int, cost_estimate_usd: float = 0.0) -> None:
    today = date.today()
    counter = (
        db.query(UsageCounter)
        .filter(UsageCounter.user_id == user_id, UsageCounter.date == today)
        .one_or_none()
    )
    if counter is None:
        counter = UsageCounter(id=uuid.uuid4(), user_id=user_id, date=today, tokens_used=0, api_calls_made=0, cost_estimate_usd=0.0)
        db.add(counter)
    counter.tokens_used += tokens
    counter.api_calls_made += 1
    counter.cost_estimate_usd += cost_estimate_usd
    db.commit()
