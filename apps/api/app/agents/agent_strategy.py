"""Agent 3: Strategy & RAG Retriever (Section 7). Queries the user's own
Qdrant namespace (never another tenant's — Section 5) for ingested strategy
rules relevant to the current technical/macro read, and has DeepSeek-R1 check
the setup against whatever it finds.
"""

from app.agents.llm import call_deepseek
from app.agents.state import AgentState
from app.ingestion.embeddings import embed_texts
from app.vectorstore.qdrant_client import collection_name_for, get_client

TOP_K = 5
SCORE_THRESHOLD = 0.3

SYSTEM_PROMPT = (
    "You are the Strategy & RAG Retriever agent inside Pipsentry's forex advisory "
    "pipeline. You are given the current technical/macro read and excerpts "
    "retrieved from the user's own ingested trading knowledge base. Judge whether "
    "the retrieved rules support, conflict with, or say nothing about this setup. "
    'Respond as JSON: {"rule_check": "confirms"|"conflicts"|"no_data", '
    '"strategy_match": string describing which strategy/source this matches, if any}.'
)


def run_agent_strategy(state: AgentState) -> AgentState:
    macro, technical = state.get("macro", {}), state.get("technical", {})
    query_text = (
        f"{state['symbol']} {state['timeframe']} bias {technical.get('bias')} "
        f"macro {macro.get('bias')}: {technical.get('rationale', '')} {macro.get('rationale', '')}"
    )

    collection = collection_name_for(state["user_id"])
    client = get_client()
    chunks: list[dict] = []
    if client.collection_exists(collection):
        [query_vector] = embed_texts([query_text])
        results = client.query_points(
            collection_name=collection, query=query_vector, limit=TOP_K, score_threshold=SCORE_THRESHOLD
        )
        chunks = [
            {"source_id": p.payload.get("source_id"), "title": p.payload.get("title"), "text": p.payload.get("text"), "score": p.score}
            for p in results.points
        ]

    if not chunks:
        return {
            **state,
            "strategy": {
                "rule_check": "no_data",
                "strategy_match": "No matching ingested knowledge for this setup yet.",
                "matched_source_ids": [],
            },
        }

    excerpts = "\n---\n".join(f"[{c['title']}] {c['text'][:500]}" for c in chunks)
    user_prompt = f"Current setup:\n{query_text}\n\nRetrieved knowledge excerpts:\n{excerpts}"

    tokens = 0
    try:
        result, tokens = call_deepseek(SYSTEM_PROMPT, user_prompt)
    except Exception as exc:
        result = {
            "rule_check": "no_data",
            "strategy_match": f"Retrieved {len(chunks)} excerpt(s) but could not evaluate them (LLM unavailable: {exc}).",
        }

    return {
        **state,
        "strategy": {
            **result,
            "matched_source_ids": list({c["source_id"] for c in chunks if c["source_id"]}),
        },
        "tokens_used": state.get("tokens_used", 0) + tokens,
    }
