import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.trade_journal_entry import TradeJournalEntry
from app.models.user import User
from app.schemas.trade_journal import TradeJournalEntryCreate, TradeJournalEntryOut

router = APIRouter(prefix="/trade-journal", tags=["trade-journal"])


@router.get("", response_model=list[TradeJournalEntryOut])
def list_entries(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[TradeJournalEntry]:
    return (
        db.query(TradeJournalEntry)
        .filter(TradeJournalEntry.user_id == user.id)
        .order_by(desc(TradeJournalEntry.opened_at))
        .all()
    )


@router.post("", response_model=TradeJournalEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    body: TradeJournalEntryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> TradeJournalEntry:
    entry = TradeJournalEntry(id=uuid.uuid4(), user_id=user.id, **body.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.patch("/{entry_id}/close", response_model=TradeJournalEntryOut)
def close_entry(
    entry_id: uuid.UUID,
    exit_price: float,
    pnl: float,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TradeJournalEntry:
    entry = (
        db.query(TradeJournalEntry)
        .filter(TradeJournalEntry.id == entry_id, TradeJournalEntry.user_id == user.id)
        .one_or_none()
    )
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trade journal entry not found")
    entry.exit_price = exit_price
    entry.pnl = pnl
    entry.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    entry = (
        db.query(TradeJournalEntry)
        .filter(TradeJournalEntry.id == entry_id, TradeJournalEntry.user_id == user.id)
        .one_or_none()
    )
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trade journal entry not found")
    db.delete(entry)
    db.commit()
