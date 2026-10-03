"""Daily summary — runs once a day, sends a Telegram message and an email."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


async def run() -> dict:
    """Compute yesterday's stats and send the digest."""
    today = datetime.now(tz=timezone.utc).date()
    yesterday = today - timedelta(days=1)
    # TODO: aggregate calls/messages/bookings/cost and send.
    return {"date": yesterday.isoformat(), "sent": False}