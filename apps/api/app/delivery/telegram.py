"""Telegram Bot API client (Section 6/12 notification channel). One platform
bot (TELEGRAM_BOT_TOKEN); each user links their own chat by sending
`/start <linking_code>` to it, which telegram_router.py resolves back to a
user id and stores the resulting chat id encrypted (Section 11).
"""

import httpx

from app.config import settings

BASE_URL = "https://api.telegram.org"


class TelegramNotConfigured(RuntimeError):
    pass


def _require_token() -> str:
    if not settings.telegram_bot_token:
        raise TelegramNotConfigured("TELEGRAM_BOT_TOKEN is not configured")
    return settings.telegram_bot_token


def send_message(chat_id: str, text: str) -> None:
    token = _require_token()
    response = httpx.post(
        f"{BASE_URL}/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10.0,
    )
    response.raise_for_status()


def format_advisory_message(advisory: dict) -> str:
    zones = advisory.get("execution_zones") or {}
    lines = [
        f"{advisory['symbol']} ({advisory['timeframe']}) — {advisory['action']}",
        f"Bias: {advisory['bias']} · Confidence: {advisory['confidence_score']:.0%}",
    ]
    if zones:
        lines.append(
            f"Entry {zones.get('suggested_entry')} · SL {zones.get('stop_loss')} · "
            f"TP1 {zones.get('take_profit_1')} · TP2 {zones.get('take_profit_2')} "
            f"({zones.get('risk_reward_ratio')})"
        )
    for warning in advisory.get("warnings", []):
        lines.append(f"⚠ {warning}")
    lines.append(advisory["disclaimer"])
    return "\n".join(lines)
