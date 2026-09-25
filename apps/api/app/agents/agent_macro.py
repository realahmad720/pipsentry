"""Agent 1: Macro & News (Section 7). Economic calendar scan + a deterministic
sentiment score (marketdata/sentiment.py), with DeepSeek-R1 turning the raw
numbers into a directional bias and rationale.
"""

from datetime import timedelta

from app.agents.llm import call_deepseek
from app.agents.state import AgentState
from app.marketdata import forexfactory, sentiment

SYSTEM_PROMPT = (
    "You are the Macro & News agent inside Pipsentry's forex advisory pipeline. "
    "Given a computed macro sentiment score and a list of upcoming high-impact "
    "economic calendar events, classify the pair's macro bias and explain why in "
    "one or two sentences, the way a trading terminal narrates a fact, not a "
    "hype-driven headline. Respond as JSON: "
    '{"bias": "BULLISH"|"BEARISH"|"NEUTRAL", "rationale": string}.'
)


def run_agent_macro(state: AgentState) -> AgentState:
    symbol = state["symbol"]
    events = forexfactory.fetch_calendar()
    score = sentiment.pair_sentiment_score(symbol, events)

    base, quote = symbol[:3], symbol[3:]
    blocking_events = forexfactory.is_no_trade_zone(events, base) + forexfactory.is_no_trade_zone(events, quote)
    upcoming = forexfactory.upcoming_high_impact(events, None, timedelta(hours=24))
    relevant_upcoming = [e for e in upcoming if e.country in (base, quote)]

    user_prompt = (
        f"Pair: {symbol}\nComputed sentiment score ({base} minus {quote} surprise average): {score:.2f}\n"
        f"Upcoming high-impact events (next 24h): "
        + (", ".join(f"{e.country} {e.title} at {e.event_time.isoformat()}" for e in relevant_upcoming) or "none")
    )

    tokens = 0
    try:
        result, tokens = call_deepseek(SYSTEM_PROMPT, user_prompt)
        bias = result.get("bias", "NEUTRAL")
        rationale = result.get("rationale", "")
    except Exception as exc:  # LLM unavailable/misconfigured — fall back to the deterministic score alone
        bias = "BULLISH" if score > 0.1 else "BEARISH" if score < -0.1 else "NEUTRAL"
        rationale = f"Macro sentiment score {score:.2f} from recent economic surprises (LLM unavailable: {exc})."

    return {
        **state,
        "macro": {
            "bias": bias,
            "sentiment_score": score,
            "rationale": rationale,
            "blocking_events": [
                {"title": e.title, "country": e.country, "event_time": e.event_time.isoformat()}
                for e in blocking_events
            ],
        },
        "tokens_used": state.get("tokens_used", 0) + tokens,
    }
