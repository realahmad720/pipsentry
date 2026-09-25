import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.delivery.forward_test import evaluate_forward_test, start_forward_test
from app.models.user import User
from app.models.watchlist import Watchlist
from app.schemas.watchlist import WatchlistCreate, WatchlistOut

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


def _get_owned_entry(db: Session, watchlist_id: uuid.UUID, user: User) -> Watchlist:
    entry = (
        db.query(Watchlist)
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == user.id)
        .one_or_none()
    )
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Watchlist entry not found")
    return entry


@router.get("", response_model=list[WatchlistOut])
def list_watchlists(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Watchlist]:
    return db.query(Watchlist).filter(Watchlist.user_id == user.id).all()


@router.post("", response_model=WatchlistOut, status_code=status.HTTP_201_CREATED)
def create_watchlist_entry(
    body: WatchlistCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Watchlist:
    entry = Watchlist(
        id=uuid.uuid4(),
        user_id=user.id,
        symbol=body.symbol.upper(),
        timeframe=body.timeframe,
        active=True,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_entry(
    watchlist_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    entry = _get_owned_entry(db, watchlist_id, user)
    db.delete(entry)
    db.commit()


@router.post("/{watchlist_id}/forward-test/start", response_model=WatchlistOut)
def start_forward_test_endpoint(
    watchlist_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Watchlist:
    """Section 9.3: begin the 3-week forward paper test for this symbol."""
    entry = _get_owned_entry(db, watchlist_id, user)
    start_forward_test(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/{watchlist_id}/forward-test", response_model=WatchlistOut)
def get_forward_test_status(
    watchlist_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Watchlist:
    """Grades the test once its 21-day window has elapsed, then returns status."""
    entry = _get_owned_entry(db, watchlist_id, user)
    return evaluate_forward_test(db, entry)
