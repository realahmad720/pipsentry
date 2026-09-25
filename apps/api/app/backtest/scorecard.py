"""Advisory scorecard (Section 9.2): for every historical signal, walk forward
through the candles to see whether SL or TP hit first, then aggregate win
rate, average R-multiple, and max drawdown across the run.
"""

from dataclasses import dataclass, field

from app.backtest.strategy import Signal
from app.marketdata.twelvedata import Candle


@dataclass
class GradedTrade:
    index: int
    direction: str
    entry: float
    stop_loss: float
    outcome: str  # tp1 | tp2 | sl | open (ran off the end of the data)
    r_multiple: float
    # How many candles after `index` the trade resolved (0 if still open) —
    # the harness uses this to skip past it instead of opening an overlapping
    # trade on the very next candle.
    resolved_offset: int = 0


@dataclass
class Scorecard:
    trades: list[GradedTrade] = field(default_factory=list)
    win_rate: float = 0.0
    avg_r_multiple: float = 0.0
    max_drawdown_r: float = 0.0
    expectancy_r: float = 0.0


def _risk(signal: Signal) -> float:
    return abs(signal.entry - signal.stop_loss)


def grade_trade(signal: Signal, future_candles: list[Candle]) -> GradedTrade:
    risk = _risk(signal)

    for offset, candle in enumerate(future_candles, start=1):
        hit_sl = candle.low <= signal.stop_loss if signal.direction == "long" else candle.high >= signal.stop_loss
        hit_tp2 = candle.high >= signal.take_profit_2 if signal.direction == "long" else candle.low <= signal.take_profit_2
        hit_tp1 = candle.high >= signal.take_profit_1 if signal.direction == "long" else candle.low <= signal.take_profit_1

        # Conservative ordering within one candle: if both SL and a TP could
        # have printed in the same bar, assume the worse outcome (SL) hit first.
        if hit_sl:
            return GradedTrade(signal.index, signal.direction, signal.entry, signal.stop_loss, "sl", -1.0, offset)
        if hit_tp2:
            r = (abs(signal.take_profit_2 - signal.entry) / risk) if risk else 0.0
            return GradedTrade(signal.index, signal.direction, signal.entry, signal.stop_loss, "tp2", r, offset)
        if hit_tp1:
            r = (abs(signal.take_profit_1 - signal.entry) / risk) if risk else 0.0
            return GradedTrade(signal.index, signal.direction, signal.entry, signal.stop_loss, "tp1", r, offset)

    return GradedTrade(signal.index, signal.direction, signal.entry, signal.stop_loss, "open", 0.0, 0)


def build_scorecard(graded_trades: list[GradedTrade]) -> Scorecard:
    if not graded_trades:
        return Scorecard()

    resolved = [t for t in graded_trades if t.outcome != "open"]
    wins = [t for t in resolved if t.outcome in ("tp1", "tp2")]
    win_rate = len(wins) / len(resolved) if resolved else 0.0
    avg_r = sum(t.r_multiple for t in resolved) / len(resolved) if resolved else 0.0

    equity, peak, max_dd = 0.0, 0.0, 0.0
    for t in resolved:
        equity += t.r_multiple
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)

    return Scorecard(
        trades=graded_trades,
        win_rate=win_rate,
        avg_r_multiple=avg_r,
        max_drawdown_r=max_dd,
        expectancy_r=avg_r,
    )
