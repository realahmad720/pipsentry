"""Orchestrates one source through extraction -> chunking -> embedding ->
per-tenant Qdrant upsert -> status update (spec Section 6).

Runs as a FastAPI BackgroundTask right after the source is registered, so it
needs its own DB session rather than the request-scoped one (which closes
once the response is sent). This is the simplest thing that actually works
end to end for an MVP; Section 12's Celery/Redis or Render Cron recommendation
is the move once ingestion volume outgrows a single API process.
"""

import logging
import uuid

from qdrant_client.http import models as qmodels

from app.db.session import SessionLocal
from app.ingestion.chunking import chunk_text
from app.ingestion.embeddings import embed_texts
from app.ingestion.extractors import ExtractionError, extract_pdf_text, extract_txt_text
from app.ingestion.youtube import YouTubeExtractionError, fetch_youtube_source
from app.models.ingested_source import IngestedSource
from app.vectorstore.qdrant_client import delete_source_vectors, ensure_tenant_collection, get_client

logger = logging.getLogger(__name__)


def run_ingestion(source_id: uuid.UUID, raw_bytes: bytes | None = None) -> None:
    db = SessionLocal()
    try:
        source = db.get(IngestedSource, source_id)
        if source is None:
            logger.warning("Ingestion triggered for missing source %s", source_id)
            return

        try:
            if source.source_type == "youtube":
                extracted = fetch_youtube_source(source.source_url or "")
                text = extracted.transcript
                if not source.title:
                    source.title = extracted.title
            elif source.source_type == "pdf":
                if raw_bytes is None:
                    raise ExtractionError("No file content available to (re)index this PDF")
                text = extract_pdf_text(raw_bytes)
            elif source.source_type == "txt":
                if raw_bytes is None:
                    raise ExtractionError("No file content available to (re)index this text file")
                text = extract_txt_text(raw_bytes)
            else:
                raise ExtractionError(f"Unknown source_type: {source.source_type}")
        except (ExtractionError, YouTubeExtractionError) as exc:
            source.status = "failed"
            source.chunk_count = 0
            db.commit()
            logger.info("Ingestion failed for source %s: %s", source_id, exc)
            return

        chunks = chunk_text(text)
        collection_name = ensure_tenant_collection(source.user_id)
        delete_source_vectors(collection_name, source_id)

        if chunks:
            vectors = embed_texts(chunks)
            get_client().upsert(
                collection_name=collection_name,
                points=[
                    qmodels.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "source_id": str(source_id),
                            "chunk_index": i,
                            "text": chunk,
                            "tags": source.tags,
                            "title": source.title,
                        },
                    )
                    for i, (chunk, vector) in enumerate(zip(chunks, vectors))
                ],
            )

        source.chunk_count = len(chunks)
        source.status = "indexed"
        db.commit()
    finally:
        db.close()
