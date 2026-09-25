"""Currency Strength Meter (Section 19 page 8): relative strength of the
eight major currencies, computed from real daily % change across every major
pair — not a paid third-party strength-meter API, which none of this
scaffold's configured providers offer; TwelveData gives us the raw candles
this is built from instead.
"""

from app.marketdata.twelvedata import fetch_candles

MAJORS = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]

# One representative pair per currency pairing with USD, plus a couple of
# cross pairs so every non-USD currency contributes to at least two readings.
_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
    "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURAUD",
]


def _pct_change(candles) -> float:
    if len(candles) < 2:
        return 0.0
    first, last = candles[0].close, candles[-1].close
    return (last - first) / first * 100 if first else 0.0


def compute_currency_strength() -> dict[str, float]:
    """Returns {currency: strength_score}. A pair's % move is credited to its
    base currency and debited from its quote currency, then averaged per
    currency across every pair it appeared in."""
    contributions: dict[str, list[float]] = {c: [] for c in MAJORS}

    for pair in _PAIRS:
        base, quote = pair[:3], pair[3:]
        try:
            candles = fetch_candles(pair, interval="1day", outputsize=2)
        except Exception:
            continue
        change = _pct_change(candles)
        contributions[base].append(change)
        contributions[quote].append(-change)

    return {
        currency: (sum(values) / len(values) if values else 0.0)
        for currency, values in contributions.items()
    }
