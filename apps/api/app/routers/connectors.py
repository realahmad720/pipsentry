import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.connectors.mcp_bridge import ConnectorUnreachable, discover_tools
from app.core.crypto import encrypt
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.connector import Connector
from app.models.user import User
from app.schemas.connector import ConnectorCreate, ConnectorOut

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _run_health_check(connector: Connector) -> None:
    try:
        connector.discovered_tools = discover_tools(connector.endpoint_url, connector.credentials_encrypted)
        connector.status = "healthy"
    except ConnectorUnreachable:
        connector.status = "unreachable"
    except Exception:
        connector.status = "unauthorized"
    connector.last_health_check_at = datetime.now(timezone.utc)


@router.get("", response_model=list[ConnectorOut])
def list_connectors(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[Connector]:
    return db.query(Connector).filter(Connector.user_id == user.id).all()


@router.post("", response_model=ConnectorOut, status_code=status.HTTP_201_CREATED)
def create_connector(
    body: ConnectorCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Connector:
    connector = Connector(
        id=uuid.uuid4(),
        user_id=user.id,
        name=body.name,
        endpoint_url=body.endpoint_url,
        credentials_encrypted=encrypt(body.credentials) if body.credentials else None,
        category=body.category,
    )
    _run_health_check(connector)  # tool-discovery call happens on registration (Section 20)
    db.add(connector)
    db.commit()
    db.refresh(connector)
    return connector


@router.post("/{connector_id}/health-check", response_model=ConnectorOut)
def health_check_connector(
    connector_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Connector:
    connector = (
        db.query(Connector).filter(Connector.id == connector_id, Connector.user_id == user.id).one_or_none()
    )
    if connector is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connector not found")
    _run_health_check(connector)
    db.commit()
    db.refresh(connector)
    return connector


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connector(
    connector_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    connector = (
        db.query(Connector).filter(Connector.id == connector_id, Connector.user_id == user.id).one_or_none()
    )
    if connector is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connector not found")
    db.delete(connector)
    db.commit()
