import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.ingestion.pipeline import run_ingestion
from app.ingestion.storage import delete_uploaded_file, load_uploaded_file, save_uploaded_file
from app.models.ingested_source import IngestedSource
from app.models.user import User
from app.schemas.ingested_source import IngestedSourceCreate, IngestedSourceOut
from app.vectorstore.qdrant_client import delete_source_vectors, ensure_tenant_collection

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

_UPLOADABLE_TYPES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
}


@router.get("/sources", response_model=list[IngestedSourceOut])
def list_sources(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[IngestedSource]:
    return db.query(IngestedSource).filter(IngestedSource.user_id == user.id).all()


@router.post("/sources", response_model=IngestedSourceOut, status_code=status.HTTP_201_CREATED)
def register_youtube_source(
    body: IngestedSourceCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IngestedSource:
    collection_name = ensure_tenant_collection(user.id)
    source = IngestedSource(
        id=uuid.uuid4(),
        user_id=user.id,
        source_type="youtube",
        source_url=body.source_url,
        title=body.title,
        tags=body.tags,
        chunk_count=0,
        vector_collection_name=collection_name,
        status="pending",
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    background_tasks.add_task(run_ingestion, source.id)
    return source


@router.post("/sources/upload", response_model=IngestedSourceOut, status_code=status.HTTP_201_CREATED)
async def upload_source(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    tags: str = Form(""),  # comma-separated
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IngestedSource:
    source_type = _UPLOADABLE_TYPES.get(file.content_type or "")
    if source_type is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Only application/pdf and text/plain uploads are supported",
        )

    raw_bytes = await file.read()
    collection_name = ensure_tenant_collection(user.id)

    source = IngestedSource(
        id=uuid.uuid4(),
        user_id=user.id,
        source_type=source_type,
        source_url=None,
        title=title or file.filename,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
        chunk_count=0,
        vector_collection_name=collection_name,
        status="pending",
    )
    stored_path = save_uploaded_file(user.id, source.id, file.filename or source_type, raw_bytes)
    source.source_url = stored_path

    db.add(source)
    db.commit()
    db.refresh(source)

    background_tasks.add_task(run_ingestion, source.id, raw_bytes)
    return source


@router.post("/sources/{source_id}/reindex", response_model=IngestedSourceOut)
def reindex_source(
    source_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IngestedSource:
    source = (
        db.query(IngestedSource)
        .filter(IngestedSource.id == source_id, IngestedSource.user_id == user.id)
        .one_or_none()
    )
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source not found")

    raw_bytes = load_uploaded_file(source.source_url) if source.source_type in ("pdf", "txt") else None

    source.status = "pending"
    db.commit()
    db.refresh(source)

    background_tasks.add_task(run_ingestion, source.id, raw_bytes)
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    source = (
        db.query(IngestedSource)
        .filter(IngestedSource.id == source_id, IngestedSource.user_id == user.id)
        .one_or_none()
    )
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source not found")

    delete_source_vectors(source.vector_collection_name, source.id)
    if source.source_type in ("pdf", "txt") and source.source_url:
        delete_uploaded_file(source.source_url)

    db.delete(source)
    db.commit()
