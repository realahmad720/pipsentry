"""Macro sentiment scoring for Agent 1 (Section 7: "Sentiment score (-1 to +1)").

This is a deterministic surprise-based heuristic — how far each released
economic print beat/missed its forecast, averaged per currency — not an NLP
model reading news headlines. A real headline-sentiment model (Section 19
page 7, "News & Sentiment") needs a news API and an LLM call per headline;
that's a paid, per-request cost this scaffold doesn't spend by default. The
signature here (`macro_sentiment_score(currency) -> float`) is the seam a
headline-based model would plug into without changing Agent 1's caller.
"""

from datetime import datetime, timedelta, timezone

from app.marketdata.forexfactory import CalendarEvent, fetch_calendar


def _surprise(event: CalendarEvent) -> float | None:
    if event.actual is None or event.forecast is None or event.forecast == 0:
        return None
    surprise = (event.actual - event.forecast) / abs(event.forecast)
    return -surprise if event.is_inverse_correlated else surprise


def macro_sentiment_score(currency: str, events: list[CalendarEvent] | None = None, lookback_hours: int = 48) -> float:
    """Average clamped surprise for one currency's recently-released prints.
    0.0 (neutral) if nothing relevant has printed in the lookback window."""
    events = events if events is not None else fetch_calendar()
    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    surprises = [
        s
        for e in events
        if e.country == currency and e.event_time.astimezone(timezone.utc) >= since
        for s in [_surprise(e)]
        if s is not None
    ]
    if not surprises:
        return 0.0

    average = sum(surprises) / len(surprises)
    return max(-1.0, min(1.0, average))


def pair_sentiment_score(symbol: str, events: list[CalendarEvent] | None = None) -> float:
    """EURUSD's bias = base currency sentiment minus quote currency sentiment,
    clamped back into [-1, 1]."""
    symbol = symbol.upper().replace("/", "")
    if len(symbol) != 6:
        return 0.0
    base, quote = symbol[:3], symbol[3:]
    events = events if events is not None else fetch_calendar()
    score = macro_sentiment_score(base, events) - macro_sentiment_score(quote, events)
    return max(-1.0, min(1.0, score))
