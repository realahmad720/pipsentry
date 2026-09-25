"""Conflict resolution rule (Section 7): if Agent 1 (macro) and Agent 2
(technical) disagree in direction — e.g. technical is bullish but macro
sentiment is below -0.4 — Agent 4 downgrades to CONFLICTED/REDUCED SIZE and
caps position sizing at 50%, rather than picking a side. Pure function, no
LLM call, so it's independently unit-testable and the rule can never be
talked out of by a model.
"""

MACRO_CONFLICT_THRESHOLD = 0.4
CONFLICTED_SIZE_CAP = 0.5


def resolve_conflict(technical_bias: str, macro_sentiment: float) -> tuple[bool, float]:
    """Returns (is_conflicted, size_multiplier)."""
    if technical_bias == "BULLISH" and macro_sentiment <= -MACRO_CONFLICT_THRESHOLD:
        return True, CONFLICTED_SIZE_CAP
    if technical_bias == "BEARISH" and macro_sentiment >= MACRO_CONFLICT_THRESHOLD:
        return True, CONFLICTED_SIZE_CAP
    return False, 1.0
