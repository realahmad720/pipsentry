"""Correlation Matrix (Section 19 page 9): Pearson correlation of daily
closes between every pair of majors, computed from real TwelveData candles.
"""

from app.marketdata.twelvedata import fetch_candles

DEFAULT_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]


def _pearson(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 2:
        return 0.0
    a, b = a[-n:], b[-n:]
    mean_a, mean_b = sum(a) / n, sum(b) / n
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    var_a = sum((x - mean_a) ** 2 for x in a)
    var_b = sum((y - mean_b) ** 2 for y in b)
    denom = (var_a * var_b) ** 0.5
    return cov / denom if denom else 0.0


def compute_correlation_matrix(pairs: list[str] | None = None, lookback: int = 60) -> dict:
    pairs = pairs or DEFAULT_PAIRS
    closes: dict[str, list[float]] = {}
    for pair in pairs:
        try:
            closes[pair] = [c.close for c in fetch_candles(pair, interval="1day", outputsize=lookback)]
        except Exception:
            closes[pair] = []

    matrix = {p1: {p2: round(_pearson(closes[p1], closes[p2]), 2) for p2 in pairs} for p1 in pairs}
    return {"pairs": pairs, "matrix": matrix}
