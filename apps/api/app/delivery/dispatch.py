"""Fan-out a finished advisory to every enabled delivery channel (Section 3
"NOTIFICATIONS: Telegram Bot per user" + the dashboard feed itself)."""

import logging
import uuid

from sqlalchemy.orm import Session

from app.core.crypto import decrypt
from app.delivery.telegram import TelegramNotConfigured, format_advisory_message, send_message
from app.models.alert_delivery import AlertDelivery
from app.models.user import User

logger = logging.getLogger(__name__)


def deliver_advisory(db: Session, user: User, advisory_id: uuid.UUID, payload: dict) -> None:
    db.add(AlertDelivery(id=uuid.uuid4(), advisory_id=advisory_id, channel="dashboard"))

    if user.telegram_chat_id_encrypted:
        try:
            chat_id = decrypt(user.telegram_chat_id_encrypted)
            send_message(chat_id, format_advisory_message(payload))
            db.add(AlertDelivery(id=uuid.uuid4(), advisory_id=advisory_id, channel="telegram"))
        except TelegramNotConfigured:
            logger.warning("Telegram delivery skipped for user %s: bot token not configured", user.id)
        except Exception:
            logger.exception("Telegram delivery failed for user %s", user.id)

    db.commit()
