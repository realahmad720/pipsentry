"""The reference signal generator the backtest harness replays candle-by-candle
(Section 9: "agents evaluate each candle close as if live").

Running the real four-agent LLM pipeline (Section 7) at every historical
candle close is what the spec describes, but it means 2-3 LLM calls per
candle — over a 6-month/1H window that's several thousand paid calls for a
single backtest run, which is cost-prohibitive to make the default. This
module is a deterministic stand-in using the same indicators Agent 2 uses
(SMA cross + ATR-sized SL/TP), so the *harness mechanics* — replay, scoring,
the expectancy gate — are real and correct. `harness.py`'s `signal_fn`
parameter is exactly the seam for swapping in the full LLM pipeline per
candle later without touching the scoring code.
"""

from dataclasses import dataclass

from app.marketdata import indicators
from app.marketdata.twelvedata import Candle

WARMUP_CANDLES = 50


@dataclass
class Signal:
    index: int
    direction: str  # long | short
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float


def generate_signal(candles: list[Candle], index: int) -> Signal | None:
    """Evaluate the candle at `index` using only candles up to and including it."""
    window = candles[: index + 1]
    if len(window) < WARMUP_CANDLES:
        return None

    closes = [c.close for c in window]
    sma20, sma50 = indicators.sma(closes, 20), indicators.sma(closes, 50)
    atr = indicators.atr(window, 14)
    if sma20 is None or sma50 is None or not atr:
        return None
    if sma20 == sma50:
        return None

    entry = closes[-1]
    direction = "long" if sma20 > sma50 else "short"
    sign = 1 if direction == "long" else -1
    return Signal(
        index=index,
        direction=direction,
        entry=entry,
        stop_loss=entry - sign * atr * 1.5,
        take_profit_1=entry + sign * atr * 3,
        take_profit_2=entry + sign * atr * 4.5,
    )
