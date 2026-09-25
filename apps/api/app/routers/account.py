from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.budget import month_to_date_tokens
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.subscription import Subscription
from app.models.usage_counter import UsageCounter
from app.models.user import User
from app.schemas.account import AccountOut

router = APIRouter(prefix="/account", tags=["account"])


@router.get("", response_model=AccountOut)
def get_account(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> AccountOut:
    """Section 19 page 20: Account & Billing. Stripe checkout itself is
    explicitly deferred (Section 21) — this surfaces the plan/usage data the
    `subscriptions`/`usage_counters` tables already carry, without a payment
    flow behind it yet."""
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).one_or_none()
    today_usage = (
        db.query(UsageCounter).filter(UsageCounter.user_id == user.id, UsageCounter.date == date.today()).one_or_none()
    )
    return AccountOut(
        id=user.id,
        email=user.email,
        plan_tier=user.plan_tier,
        telegram_linked=bool(user.telegram_chat_id_encrypted),
        subscription=subscription,
        month_to_date_tokens=month_to_date_tokens(db, user.id),
        today_usage=today_usage,
    )
