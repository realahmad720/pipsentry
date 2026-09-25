"""Grades open advisories against the live price feed: did SL or TP hit first?
Used both to keep the dashboard/Advisory Detail page (Section 19 page 4)
honest about outcomes, and to grade a watchlist entry's forward paper test
(Section 9.3 / Phase 6).
"""

import logging

from sqlalchemy.orm import Session

from app.marketdata.twelvedata import fetch_quote_price
from app.models.advisory import Advisory

logger = logging.getLogger(__name__)


def _outcome_for_price(action: str, price: float, zones: dict) -> str | None:
    stop_loss, tp1, tp2 = zones["stop_loss"], zones["take_profit_1"], zones["take_profit_2"]
    if action.startswith("BUY"):
        if price <= stop_loss:
            return "sl"
        if price >= tp2:
            return "tp2"
        if price >= tp1:
            return "tp1"
    elif action.startswith("SELL"):
        if price >= stop_loss:
            return "sl"
        if price <= tp2:
            return "tp2"
        if price <= tp1:
            return "tp1"
    return None


def grade_open_advisories(db: Session) -> int:
    """Returns the number of advisories newly graded."""
    from datetime import datetime, timezone

    open_advisories = db.query(Advisory).filter(Advisory.outcome == "open").all()
    graded = 0
    for advisory in open_advisories:
        zones = advisory.payload_json.get("execution_zones")
        if not zones or advisory.action not in ("BUY_LIMIT", "SELL_LIMIT"):
            continue
        try:
            price = fetch_quote_price(advisory.symbol)
        except Exception:
            logger.warning("Could not fetch price for %s while grading advisory %s", advisory.symbol, advisory.id)
            continue
        outcome = _outcome_for_price(advisory.action, price, zones)
        if outcome:
            advisory.outcome = outcome
            advisory.outcome_at = datetime.now(timezone.utc)
            graded += 1
    if graded:
        db.commit()
    return graded
