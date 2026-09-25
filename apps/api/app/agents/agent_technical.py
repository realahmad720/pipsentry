"""Agent 2: Technical & Price Action (Section 7). Pulls candles via the
TwelveData bridge, computes ATR/RSI/SMA/swing levels in plain Python
(marketdata/indicators.py), and has DeepSeek-R1 turn those numbers into a
directional read and a candidate entry/SL/TP zone.

This does not implement real order-block / fair-value-gap detection — that's
a dedicated price-action pattern-recognition algorithm, out of scope for this
pass. The model reasons over swing highs/lows, ATR, RSI and moving averages
instead, which is a coarser read than the ICT-style analysis in the spec's
example payload (Section 10). Swapping in real SMC pattern detection later is
a change inside this function, not to its callers.
"""

from app.agents.llm import call_deepseek
from app.agents.state import AgentState
from app.marketdata import indicators
from app.marketdata.twelvedata import fetch_candles

SYSTEM_PROMPT = (
    "You are the Technical & Price Action agent inside Pipsentry's forex advisory "
    "pipeline. Given recent price, ATR, RSI, moving averages, and swing high/low "
    "levels, judge the pair's technical bias and propose a plausible entry zone, "
    "stop loss, and two take-profit targets consistent with the current "
    "volatility (ATR) and the nearest swing levels. Respond as JSON: "
    '{"bias": "BULLISH"|"BEARISH"|"NEUTRAL", "entry_range": [low, high], '
    '"suggested_entry": number, "stop_loss": number, "take_profit_1": number, '
    '"take_profit_2": number, "rationale": string}.'
)


def run_agent_technical(state: AgentState) -> AgentState:
    symbol, timeframe = state["symbol"], state["timeframe"]
    candles = fetch_candles(symbol, timeframe, outputsize=200)
    closes = [c.close for c in candles]

    atr = indicators.atr(candles) or 0.0
    rsi = indicators.rsi(closes)
    sma20 = indicators.sma(closes, 20)
    sma50 = indicators.sma(closes, 50)
    swing_high, swing_low = indicators.swing_levels(candles)
    last_close = closes[-1] if closes else None

    user_prompt = (
        f"Pair: {symbol} ({timeframe})\nLast close: {last_close}\nATR(14): {atr}\n"
        f"RSI(14): {rsi}\nSMA20: {sma20}\nSMA50: {sma50}\n"
        f"Recent swing high: {swing_high}\nRecent swing low: {swing_low}"
    )

    tokens = 0
    try:
        result, tokens = call_deepseek(SYSTEM_PROMPT, user_prompt)
    except Exception as exc:
        # Deterministic fallback: trend from SMA cross, SL/TP from ATR multiples.
        bullish = bool(sma20 and sma50 and sma20 > sma50)
        bias = "BULLISH" if bullish else "BEARISH" if sma20 and sma50 else "NEUTRAL"
        entry = last_close or 0.0
        direction = 1 if bias == "BULLISH" else -1
        result = {
            "bias": bias,
            "entry_range": [entry - direction * atr * 0.1, entry + direction * atr * 0.1],
            "suggested_entry": entry,
            "stop_loss": entry - direction * atr * 1.5,
            "take_profit_1": entry + direction * atr * 3,
            "take_profit_2": entry + direction * atr * 4.5,
            "rationale": f"SMA20/SMA50 cross fallback (LLM unavailable: {exc}).",
        }

    return {
        **state,
        "technical": {
            **result,
            "atr": atr,
            "rsi": rsi,
            "sma20": sma20,
            "sma50": sma50,
            "last_close": last_close,
        },
        "tokens_used": state.get("tokens_used", 0) + tokens,
    }
