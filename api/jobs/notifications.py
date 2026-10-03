"""Notifications — Telegram, email, Slack."""

from __future__ import annotations

import httpx

from api.config import get_settings


async def notify_new_message(message_id: str) -> dict:
    """Alert staff that a new message has arrived."""
    settings = get_settings()
    # TODO: load the message and the business's notification preferences.
    # TODO: respect do-not-disturb hours from the business config.
    body = "New receptionist message. Open the dashboard for details."
    return await _send(body)


async def _send(body: str) -> dict:
    settings = get_settings()
    if settings.telegram_bot_token and settings.telegram_default_chat_id:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                    json={"chat_id": settings.telegram_default_chat_id, "text": body},
                    timeout=5.0,
                )
                resp.raise_for_status()
                return {"channel": "telegram", "ok": True}
        except httpx.HTTPError:
            return {"channel": "telegram", "ok": False}

    # TODO: SMTP / Resend / SendGrid fall-through.
    return {"channel": "none", "ok": False}