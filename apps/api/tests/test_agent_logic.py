"""Pure-logic tests that need no DB, network, or LLM key — the parts of the
pipeline whose correctness matters most (Section 7's conflict rule, Section
7's risk:reward gate) and that a model can never talk its way around."""

from datetime import datetime, timedelta, timezone

from app.agents.conflict import resolve_conflict
from app.agents.agent_risk_auditor import _risk_reward
from app.backtest.gate import MIN_RESOLVED_TRADES, passes_expectancy_gate
from app.backtest.scorecard import GradedTrade, build_scorecard
from app.backtest.strategy import WARMUP_CANDLES, generate_signal
from app.marketdata.twelvedata import Candle


def test_conflict_rule_flags_bullish_technical_against_bearish_macro() -> None:
    is_conflicted, size = resolve_conflict("BULLISH", -0.5)
    assert is_conflicted is True
    assert size == 0.5


def test_conflict_rule_flags_bearish_technical_against_bullish_macro() -> None:
    is_conflicted, size = resolve_conflict("BEARISH", 0.5)
    assert is_conflicted is True
    assert size == 0.5


def test_conflict_rule_clears_when_aligned() -> None:
    assert resolve_conflict("BULLISH", 0.5) == (False, 1.0)
    assert resolve_conflict("BEARISH", -0.5) == (False, 1.0)


def test_conflict_rule_clears_below_threshold() -> None:
    assert resolve_conflict("BULLISH", -0.39) == (False, 1.0)


def test_risk_reward_matches_manual_calculation() -> None:
    rr = _risk_reward(entry=1.0850, stop_loss=1.0882, take_profit_1=1.0790)
    assert round(rr, 3) == round(0.0060 / 0.0032, 3)


def _flat_candles(n: int) -> list[Candle]:
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [Candle(time=base + timedelta(hours=i), open=1.0, high=1.0, low=1.0, close=1.0) for i in range(n)]


def test_generate_signal_returns_none_before_warmup() -> None:
    candles = _flat_candles(WARMUP_CANDLES - 1)
    assert generate_signal(candles, len(candles) - 1) is None


def test_generate_signal_returns_none_on_flat_market() -> None:
    # SMA20 == SMA50 on a perfectly flat series — no crossover, no signal.
    candles = _flat_candles(WARMUP_CANDLES + 5)
    assert generate_signal(candles, len(candles) - 1) is None


def test_expectancy_gate_requires_minimum_sample_size() -> None:
    trades = [GradedTrade(i, "long", 1.0, 0.9, "tp1", 2.0) for i in range(MIN_RESOLVED_TRADES - 1)]
    ok, message = passes_expectancy_gate(build_scorecard(trades))
    assert ok is False
    assert "Only" in message


def test_expectancy_gate_passes_on_positive_expectancy() -> None:
    trades = [GradedTrade(i, "long", 1.0, 0.9, "tp1", 2.0) for i in range(MIN_RESOLVED_TRADES)]
    ok, _ = passes_expectancy_gate(build_scorecard(trades))
    assert ok is True


def test_expectancy_gate_fails_on_negative_expectancy() -> None:
    trades = [GradedTrade(i, "long", 1.0, 0.9, "sl", -1.0) for i in range(MIN_RESOLVED_TRADES)]
    ok, _ = passes_expectancy_gate(build_scorecard(trades))
    assert ok is False
