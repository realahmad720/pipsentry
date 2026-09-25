"""3-week forward paper test (Section 9.3 / Phase 6): once a watchlist entry
clears the backtest expectancy gate, it runs live for 21 days and is judged
by the same gate against its *actual* delivered advisories, not simulated
ones — before a strategy/symbol is trusted for real use.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.backtest.gate import passes_expectancy_gate
from app.backtest.scorecard import GradedTrade, build_scorecard
from app.models.advisory import Advisory
from app.models.watchlist import Watchlist

FORWARD_TEST_DURATION = timedelta(days=21)

_OUTCOME_R = {"tp1": 2.0, "tp2": 3.0, "sl": -1.0}  # matches the ATR multiples in backtest/strategy.py


def start_forward_test(watchlist: Watchlist) -> None:
    now = datetime.now(timezone.utc)
    watchlist.forward_test_status = "running"
    watchlist.forward_test_started_at = now
    watchlist.forward_test_ends_at = now + FORWARD_TEST_DURATION


def evaluate_forward_test(db: Session, watchlist: Watchlist) -> Watchlist:
    """No-op until the 21-day window has elapsed; grades it exactly once after."""
    if watchlist.forward_test_status != "running" or watchlist.forward_test_ends_at is None:
        return watchlist
    if datetime.now(timezone.utc) < watchlist.forward_test_ends_at:
        return watchlist

    advisories = (
        db.query(Advisory)
        .filter(
            Advisory.user_id == watchlist.user_id,
            Advisory.symbol == watchlist.symbol,
            Advisory.timeframe == watchlist.timeframe,
            Advisory.delivered_at >= watchlist.forward_test_started_at,
            Advisory.delivered_at <= watchlist.forward_test_ends_at,
            Advisory.outcome != "open",
        )
        .all()
    )

    graded = [
        GradedTrade(index=i, direction=a.action, entry=0.0, stop_loss=0.0, outcome=a.outcome, r_multiple=_OUTCOME_R.get(a.outcome, 0.0))
        for i, a in enumerate(advisories)
    ]
    scorecard = build_scorecard(graded)
    passed, _ = passes_expectancy_gate(scorecard)

    watchlist.forward_test_status = "passed" if passed else "failed"
    db.commit()
    return watchlist
