import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings

_client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

# Must match the embedding model's output dimension (text-embedding-3-small = 1536).
EMBEDDING_DIM = 1536


def collection_name_for(user_id: uuid.UUID) -> str:
    return f"kb_{user_id}"


def ensure_tenant_collection(user_id: uuid.UUID) -> str:
    """Create the user's namespaced Qdrant collection if it doesn't exist yet.

    Called on first ingestion for a user so every tenant's vectors live in their
    own collection and a query can never cross into another user's knowledge base.
    """
    name = collection_name_for(user_id)
    if not _client.collection_exists(name):
        _client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(size=EMBEDDING_DIM, distance=qmodels.Distance.COSINE),
        )
    return name


def get_client() -> QdrantClient:
    return _client


def delete_source_vectors(collection_name: str, source_id: uuid.UUID) -> None:
    """Remove every vector belonging to one ingested source (purge before
    reindexing it, or when the source itself is deleted)."""
    if not _client.collection_exists(collection_name):
        return
    _client.delete(
        collection_name=collection_name,
        points_selector=qmodels.FilterSelector(
            filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key="source_id", match=qmodels.MatchValue(value=str(source_id)))]
            )
        ),
    )
