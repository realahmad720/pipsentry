"""LangGraph wiring for the four agents (Section 7 diagram):

    START -> {agent_macro, agent_technical} (parallel fan-out)
          -> agent_strategy
          -> budget_gate
          -> agent_risk_auditor | budget_exceeded
          -> END

Agents 1 and 2 have no data dependency on each other, so they run in
parallel; both must finish before Agent 3 (which needs both reads to build
its retrieval query). Agent 4 only runs if the budget gate passes
(Section 8).
"""

from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph

from app.agents.agent_macro import run_agent_macro
from app.agents.agent_risk_auditor import DISCLAIMER, run_agent_risk_auditor
from app.agents.agent_strategy import run_agent_strategy
from app.agents.agent_technical import run_agent_technical
from app.agents.budget import has_budget_remaining
from app.agents.state import AgentState
from app.db.session import SessionLocal


def _budget_gate(state: AgentState) -> AgentState:
    db = SessionLocal()
    try:
        budget_ok = has_budget_remaining(db, state["user_id"])
    finally:
        db.close()
    return {**state, "budget_ok": budget_ok}


def _budget_exceeded(state: AgentState) -> AgentState:
    advisory = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": str(state["user_id"]),
        "symbol": state["symbol"],
        "timeframe": state["timeframe"],
        "action": "STATUS_BUDGET_EXCEEDED",
        "bias": "NEUTRAL",
        "confidence_score": 0.0,
        "conflict_status": "NONE",
        "position_size_multiplier": 0.0,
        "execution_zones": None,
        "rationale": {
            "technical": "Not evaluated — monthly token budget exhausted before Agent 4 could run.",
            "macro_fundamental": "",
            "strategy_match": "",
        },
        "warnings": ["STATUS: BUDGET_EXCEEDED — upgrade plan or wait for next billing cycle."],
        "disclaimer": DISCLAIMER,
    }
    return {**state, "advisory": advisory}


def _route_after_budget(state: AgentState) -> str:
    return "agent_risk_auditor" if state.get("budget_ok") else "budget_exceeded"


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent_macro", run_agent_macro)
    graph.add_node("agent_technical", run_agent_technical)
    graph.add_node("agent_strategy", run_agent_strategy)
    graph.add_node("budget_gate", _budget_gate)
    graph.add_node("agent_risk_auditor", run_agent_risk_auditor)
    graph.add_node("budget_exceeded", _budget_exceeded)

    graph.add_edge(START, "agent_macro")
    graph.add_edge(START, "agent_technical")
    graph.add_edge("agent_macro", "agent_strategy")
    graph.add_edge("agent_technical", "agent_strategy")
    graph.add_edge("agent_strategy", "budget_gate")
    graph.add_conditional_edges(
        "budget_gate", _route_after_budget, {"agent_risk_auditor": "agent_risk_auditor", "budget_exceeded": "budget_exceeded"}
    )
    graph.add_edge("agent_risk_auditor", END)
    graph.add_edge("budget_exceeded", END)
    return graph.compile()


_compiled_graph = None


def get_compiled_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


def run_advisory_pipeline(user_id, symbol: str, timeframe: str) -> AgentState:
    graph = get_compiled_graph()
    initial_state: AgentState = {"user_id": user_id, "symbol": symbol.upper(), "timeframe": timeframe}
    return graph.invoke(initial_state)
