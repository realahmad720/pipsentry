"""Embedding generation per spec Section 6.

Uses OpenAI's text-embedding-3-small (1536 dimensions, matching
app.vectorstore.qdrant_client.EMBEDDING_DIM). The spec also allows
BAAI/bge-large-en as a self-hosted alternative; that would mean running a
local model server instead of an API call, which is a swap behind this same
function, not a change to callers.
"""

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = _get_client().embeddings.create(model=settings.embedding_model, input=texts)
    return [item.embedding for item in response.data]
