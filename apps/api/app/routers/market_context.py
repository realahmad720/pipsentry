from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.marketdata import cot, forexfactory, sentiment
from app.marketdata.correlation import compute_correlation_matrix
from app.marketdata.currency_strength import compute_currency_strength
from app.marketdata.session_clock import session_status
from app.marketdata.twelvedata import TwelveDataError, fetch_candles
from app.models.user import User

router = APIRouter(prefix="/market", tags=["market-context"])


@router.get("/candles")
def get_candles(symbol: str, interval: str = "1h", outputsize: int = 200, user: User = Depends(get_current_user)) -> list[dict]:
    """Section 19 page 5: Chart Workspace."""
    try:
        candles = fetch_candles(symbol, interval, outputsize)
    except TwelveDataError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    return [{"time": c.time.isoformat(), "open": c.open, "high": c.high, "low": c.low, "close": c.close} for c in candles]


@router.get("/calendar")
def get_calendar(currency: str | None = None, hours_ahead: int = 48, user: User = Depends(get_current_user)) -> list[dict]:
    """Section 19 page 6: Economic Calendar."""
    events = forexfactory.fetch_calendar()
    upcoming = forexfactory.upcoming_high_impact(events, currency, timedelta(hours=hours_ahead))
    return [
        {
            "title": e.title,
            "country": e.country,
            "impact": e.impact,
            "event_time": e.event_time.isoformat(),
            "forecast": e.forecast,
            "previous": e.previous,
            "actual": e.actual,
        }
        for e in upcoming
    ]


@router.get("/sentiment")
def get_sentiment(currency: str, user: User = Depends(get_current_user)) -> dict:
    """Section 19 page 7: News & Sentiment (surprise-based heuristic score;
    see marketdata/sentiment.py for what this does and doesn't do)."""
    return {"currency": currency.upper(), "score": sentiment.macro_sentiment_score(currency.upper())}


@router.get("/currency-strength")
def get_currency_strength(user: User = Depends(get_current_user)) -> dict:
    """Section 19 page 8."""
    try:
        return compute_currency_strength()
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc


@router.get("/correlation")
def get_correlation(user: User = Depends(get_current_user)) -> dict:
    """Section 19 page 9."""
    try:
        return compute_correlation_matrix()
    except Exception as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc


@router.get("/session-clock")
def get_session_clock() -> dict:
    """Section 19 page 10 — no auth needed, it's pure UTC calendar math."""
    return session_status()


@router.get("/cot")
def get_cot(currency: str, user: User = Depends(get_current_user)) -> dict:
    """Section 19 page 11."""
    try:
        return cot.fetch_cot_positioning(currency)
    except cot.CotError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.get("/cot/supported-currencies")
def get_cot_supported_currencies() -> list[str]:
    return cot.supported_currencies()
