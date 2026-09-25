"""Pure-Python technical indicators — no ta-lib/pandas dependency for a handful
of rolling-window calculations. Agent 2 (Technical & Price Action, Section 7)
uses these against candles from `twelvedata.fetch_candles`.
"""

from app.marketdata.twelvedata import Candle


def sma(closes: list[float], period: int) -> float | None:
    if len(closes) < period:
        return None
    return sum(closes[-period:]) / period


def ema_series(closes: list[float], period: int) -> list[float]:
    if not closes:
        return []
    k = 2 / (period + 1)
    out = [closes[0]]
    for price in closes[1:]:
        out.append(price * k + out[-1] * (1 - k))
    return out


def rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(candles: list[Candle], period: int = 14) -> float | None:
    if len(candles) < period + 1:
        return None
    true_ranges = []
    for i in range(1, len(candles)):
        c, prev = candles[i], candles[i - 1]
        true_ranges.append(
            max(c.high - c.low, abs(c.high - prev.close), abs(c.low - prev.close))
        )
    return sum(true_ranges[-period:]) / period


def swing_levels(candles: list[Candle], lookback: int = 30) -> tuple[float | None, float | None]:
    """Naive key-level proxy: highest high / lowest low over the lookback window."""
    window = candles[-lookback:]
    if not window:
        return None, None
    return max(c.high for c in window), min(c.low for c in window)
