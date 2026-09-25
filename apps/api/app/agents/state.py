"""Shared state passed between the four LangGraph nodes (Section 7)."""

import uuid
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_id: uuid.UUID
    symbol: str
    timeframe: str

    macro: dict[str, Any]  # Agent 1 output
    technical: dict[str, Any]  # Agent 2 output
    strategy: dict[str, Any]  # Agent 3 output

    budget_ok: bool
    tokens_used: int

    advisory: dict[str, Any]  # Agent 4 output — the final payload (Section 10)
