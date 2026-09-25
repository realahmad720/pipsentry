"""Historical replay harness (Section 9.1): feed the strategy historical OHLC
for a fixed date range, evaluating each candle close as if live, and refuse
overlapping trades (skip ahead until the open one resolves) so the scorecard
reflects one position at a time, the way a discretionary trader actually
holds one setup per pair.
"""

from app.backtest.scorecard import GradedTrade, Scorecard, build_scorecard, grade_trade
from app.backtest.strategy import generate_signal
from app.marketdata.twelvedata import fetch_candles_range


def run_backtest(symbol: str, timeframe: str, start_date: str, end_date: str) -> Scorecard:
    candles = fetch_candles_range(symbol, timeframe, start_date, end_date)

    graded: list[GradedTrade] = []
    i = 0
    while i < len(candles):
        signal = generate_signal(candles, i)
        if signal is None:
            i += 1
            continue
        trade = grade_trade(signal, candles[i + 1 :])
        graded.append(trade)
        if trade.outcome == "open":
            break  # never resolved before the data ran out — nothing left to replay past it
        i += trade.resolved_offset + 1  # skip past this trade's resolution before looking for the next signal

    return build_scorecard(graded)
