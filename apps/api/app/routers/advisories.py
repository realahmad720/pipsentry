import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.agents.budget import log_usage
from app.agents.graph import run_advisory_pipeline
from app.core.security import get_current_user
from app.db.session import get_db
from app.delivery.dispatch import deliver_advisory
from app.models.advisory import Advisory
from app.models.user import User
from app.schemas.advisory import AdvisoryOut, EvaluateRequest

router = APIRouter(prefix="/advisories", tags=["advisories"])


@router.get("", response_model=list[AdvisoryOut])
def list_advisories(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Advisory]:
    return (
        db.query(Advisory)
        .filter(Advisory.user_id == user.id)
        .order_by(desc(Advisory.delivered_at))
        .limit(100)
        .all()
    )


@router.get("/{advisory_id}", response_model=AdvisoryOut)
def get_advisory(
    advisory_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Advisory:
    """Section 19 page 4: Advisory Detail."""
    advisory = (
        db.query(Advisory).filter(Advisory.id == advisory_id, Advisory.user_id == user.id).one_or_none()
    )
    if advisory is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Advisory not found")
    return advisory


@router.post("/evaluate", response_model=AdvisoryOut)
def evaluate_advisory(
    body: EvaluateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Advisory:
    """Runs the full four-agent pipeline (Section 7) for one symbol/timeframe
    and persists + delivers the resulting advisory. Synchronous: this makes
    2-3 LLM calls, so it's slow (seconds), not instant — fine for an on-demand
    "Evaluate Setup" button (Section 16's signature motion moment), not for
    high-frequency polling. A scheduled candle-close evaluator is a queue-
    backed job (Section 12) and is out of scope for this pass.
    """
    final_state = run_advisory_pipeline(user.id, body.symbol, body.timeframe)
    payload = final_state["advisory"]

    advisory = Advisory(
        id=uuid.uuid4(),
        user_id=user.id,
        symbol=payload["symbol"],
        timeframe=payload["timeframe"],
        action=payload["action"],
        confidence_score=payload["confidence_score"],
        payload_json=payload,
    )
    db.add(advisory)
    db.commit()
    db.refresh(advisory)

    log_usage(db, user.id, final_state.get("tokens_used", 0))
    deliver_advisory(db, user, advisory.id, payload)

    return advisory
