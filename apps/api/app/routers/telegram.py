from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.crypto import encrypt
from app.core.security import get_current_user
from app.db.session import get_db
from app.delivery.linking import generate_linking_code, resolve_linking_code
from app.models.user import User

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.get("/link-code")
def get_link_code(user: User = Depends(get_current_user)) -> dict:
    """Dashboard calls this (Section 19 page 19, Alerts settings) to show the
    user a code to send their bot as `/start <code>`."""
    return {"code": generate_linking_code(user.id), "expires_in_seconds": 600}


@router.post("/webhook")
def telegram_webhook(update: dict, db: Session = Depends(get_db)) -> dict:
    """Telegram calls this for every update sent to the bot. We only handle
    `/start <code>` messages; everything else is acknowledged and ignored."""
    message = update.get("message") or {}
    text: str = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not text.startswith("/start ") or chat_id is None:
        return {"ok": True}

    code = text.removeprefix("/start ").strip()
    user_id = resolve_linking_code(code)
    if user_id is None:
        return {"ok": True}

    user = db.get(User, user_id)
    if user is not None:
        user.telegram_chat_id_encrypted = encrypt(str(chat_id))
        db.commit()

    return {"ok": True}
