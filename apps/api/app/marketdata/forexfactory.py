"""Economic calendar (Section 3 "Market Data" row: "ForexFactory + RSS feeds").

ForexFactory has never published an official calendar API. What most retail
tools (and this one) actually consume is the same static JSON snapshot the
ForexFactory widget itself fetches — no RSS parsing involved, since the RSS
feed ForexFactory used to publish was retired years ago. That substitution is
called out here rather than silently pretending we're parsing RSS.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings

# A handful of indicators where a bigger number is actually bad for the
# currency (unemployment, claims, inventories rising). Everything else
# defaults to "bigger beat than forecast = stronger currency" — a heuristic,
# not real NLP/economic modelling; see sentiment.py docstring.
_INVERSE_CORRELATION_KEYWORDS = ("unemployment", "jobless", "claims", "inventories", "deficit")

CalendarImpact = str  # "Holiday" | "Low" | "Medium" | "High"


@dataclass
class CalendarEvent:
    title: str
    country: str  # currency code, e.g. "USD"
    impact: CalendarImpact
    event_time: datetime
    forecast: float | None
    previous: float | None
    actual: float | None

    @property
    def is_inverse_correlated(self) -> bool:
        return any(kw in self.title.lower() for kw in _INVERSE_CORRELATION_KEYWORDS)


class CalendarError(Exception):
    pass


def _parse_number(raw: str | None) -> float | None:
    if not raw:
        return None
    match = re.search(r"-?\d+(\.\d+)?", raw.replace(",", ""))
    return float(match.group()) if match else None


def fetch_calendar() -> list[CalendarEvent]:
    response = httpx.get(settings.forexfactory_calendar_url, timeout=15.0)
    response.raise_for_status()
    raw_events = response.json()

    events: list[CalendarEvent] = []
    for item in raw_events:
        try:
            event_time = datetime.fromisoformat(item["date"])
        except (KeyError, ValueError):
            continue
        events.append(
            CalendarEvent(
                title=item.get("title", "Unknown event"),
                country=item.get("country", ""),
                impact=item.get("impact", "Low"),
                event_time=event_time,
                forecast=_parse_number(item.get("forecast")),
                previous=_parse_number(item.get("previous")),
                actual=_parse_number(item.get("actual")),
            )
        )
    return events


def upcoming_high_impact(events: list[CalendarEvent], currency: str | None, within: timedelta) -> list[CalendarEvent]:
    now = datetime.now(timezone.utc)
    horizon = now + within
    return [
        e
        for e in events
        if e.impact == "High"
        and now <= e.event_time.astimezone(timezone.utc) <= horizon
        and (currency is None or e.country == currency)
    ]


def is_no_trade_zone(events: list[CalendarEvent], currency: str, minutes: int = 45) -> list[CalendarEvent]:
    """Section 7, Agent 4: 'no high-impact news within 45 minutes'. Returns the
    blocking events (empty list means the pair is clear to trade)."""
    return upcoming_high_impact(events, currency, timedelta(minutes=minutes))
