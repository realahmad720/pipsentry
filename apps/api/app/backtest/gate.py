"""Section 9.3: "a strategy/symbol only moves to the live 3-week forward
paper test after clearing a minimum backtest threshold (positive expectancy
over the historical window)"."""

from app.backtest.scorecard import Scorecard

MIN_RESOLVED_TRADES = 10  # too few trades to trust any expectancy figure


def passes_expectancy_gate(scorecard: Scorecard) -> tuple[bool, str]:
    resolved = [t for t in scorecard.trades if t.outcome != "open"]
    if len(resolved) < MIN_RESOLVED_TRADES:
        return False, f"Only {len(resolved)} resolved trade(s); need at least {MIN_RESOLVED_TRADES} to judge expectancy."
    if scorecard.expectancy_r <= 0:
        return False, f"Expectancy is {scorecard.expectancy_r:.2f}R — not positive over this window."
    return True, f"Positive expectancy ({scorecard.expectancy_r:.2f}R avg over {len(resolved)} trades) — cleared to forward-test."
