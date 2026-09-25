"""Agent 4: Risk & Synthesis Auditor (Section 7) — the only agent on Claude
Sonnet (Section 21). Compiles the final structured advisory (Section 10
payload shape), but the numbers that gate trust — conflict status, no-trade
zone, risk:reward, the disclaimer — are computed in Python and handed to the
model as *facts to narrate*, not left for it to compute. An LLM should never
be the sole authority on whether a risk rule was satisfied.
"""

from datetime import datetime, timezone

from app.agents.conflict import resolve_conflict
from app.agents.llm import call_claude
from app.agents.state import AgentState

MIN_RISK_REWARD = 2.0
DISCLAIMER = (
    "This is an automated advisory for informational purposes only and does not "
    "constitute financial advice. You are solely responsible for your own trading decisions."
)

SYSTEM_PROMPT = (
    "You are the Risk & Synthesis Auditor inside Pipsentry's forex advisory pipeline — "
    "the final, highest-stakes step. You are given the macro read, technical read, "
    "strategy/RAG check, and precomputed risk facts (conflict status, no-trade-zone "
    "status, risk:reward ratio, action). Write the rationale fields and any warnings "
    "the trader should know before acting, in a direct, calm, no-hype voice. Do not "
    "change the action, bias, or numbers you were given — narrate them. Respond as JSON: "
    '{"confidence_score": number between 0 and 1, "warnings": [string, ...], '
    '"technical_rationale": string, "macro_fundamental_rationale": string}.'
)


def _risk_reward(entry: float, stop_loss: float, take_profit_1: float) -> float:
    risk = abs(entry - stop_loss)
    reward = abs(take_profit_1 - entry)
    return reward / risk if risk > 0 else 0.0


def run_agent_risk_auditor(state: AgentState) -> AgentState:
    macro, technical, strategy = state["macro"], state["technical"], state["strategy"]
    symbol, timeframe = state["symbol"], state["timeframe"]

    is_conflicted, size_multiplier = resolve_conflict(technical["bias"], macro["sentiment_score"])
    blocked_by_news = bool(macro.get("blocking_events"))

    entry = technical["suggested_entry"]
    stop_loss = technical["stop_loss"]
    take_profit_1 = technical["take_profit_1"]
    take_profit_2 = technical["take_profit_2"]
    rr = _risk_reward(entry, stop_loss, take_profit_1)

    if blocked_by_news:
        action = "NO_TRADE"
    elif rr < MIN_RISK_REWARD:
        action = "NO_TRADE"
    elif technical["bias"] == "BULLISH":
        action = "BUY_LIMIT"
    elif technical["bias"] == "BEARISH":
        action = "SELL_LIMIT"
    else:
        action = "NO_TRADE"

    user_prompt = (
        f"Pair: {symbol} ({timeframe})\n"
        f"Macro bias: {macro['bias']} (score {macro['sentiment_score']:.2f}) — {macro['rationale']}\n"
        f"Technical bias: {technical['bias']} — {technical.get('rationale', '')}\n"
        f"Strategy/RAG check: {strategy['rule_check']} — {strategy['strategy_match']}\n"
        f"Precomputed: action={action}, conflicted={is_conflicted}, "
        f"position_size_multiplier={size_multiplier}, risk_reward={rr:.2f}, "
        f"blocked_by_high_impact_news={blocked_by_news}"
    )

    tokens = 0
    try:
        result, tokens = call_claude(SYSTEM_PROMPT, user_prompt)
        confidence = float(result.get("confidence_score", 0.5))
        warnings = list(result.get("warnings", []))
        technical_rationale = result.get("technical_rationale", technical.get("rationale", ""))
        macro_rationale = result.get("macro_fundamental_rationale", macro.get("rationale", ""))
    except Exception as exc:
        confidence = 0.5 if action != "NO_TRADE" else 0.0
        warnings = [f"LLM synthesis unavailable ({exc}); rationale is the raw agent output."]
        technical_rationale = technical.get("rationale", "")
        macro_rationale = macro.get("rationale", "")

    if blocked_by_news:
        warnings.append("Blocked: high-impact news within 45 minutes.")
    if is_conflicted:
        warnings.append("Macro and technical bias disagree; size capped at 50% of normal risk unit.")

    advisory = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": str(state["user_id"]),
        "symbol": symbol,
        "timeframe": timeframe,
        "action": action,
        "bias": technical["bias"],
        "confidence_score": round(confidence, 2),
        "conflict_status": "CONFLICTED_REDUCED_SIZE" if is_conflicted else "NONE",
        "position_size_multiplier": size_multiplier,
        "execution_zones": {
            "entry_range": technical["entry_range"],
            "suggested_entry": entry,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "risk_reward_ratio": f"1:{rr:.2f}",
        },
        "rationale": {
            "technical": technical_rationale,
            "macro_fundamental": macro_rationale,
            "strategy_match": strategy["strategy_match"],
        },
        "warnings": warnings,
        "disclaimer": DISCLAIMER,
    }

    return {**state, "advisory": advisory, "tokens_used": state.get("tokens_used", 0) + tokens}
