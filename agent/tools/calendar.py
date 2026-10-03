"""Calendar tools — P1.

check_availability: query the business's Google Calendar for open times.
book_appointment: create an event with idempotency on the (caller_phone, slot).
reschedule_appointment / cancel_appointment live here for now.

Server-side validation:
  - Re-check availability at booking time (the slot might have been taken
    between check_availability and book_appointment).
  - Phone normalised to E.164.
  - Booking window capped (e.g., not more than 60 days in the future).
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


def check_availability_tool() -> dict[str, Any]:
    return {
        "name": "check_availability",
        "description": (
            "Look up available appointment times. Offer the caller at most 2 "
            "options from the result. Always call this before book_appointment."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Service the caller wants to book.",
                },
                "date": {
                    "type": "string",
                    "description": "Date the caller prefers, in YYYY-MM-DD or natural language.",
                },
                "time_window": {
                    "type": "string",
                    "description": "Optional preferred window (morning, afternoon, evening, or HH:MM-HH:MM).",
                },
            },
            "required": ["service", "date"],
        },
    }


def book_appointment_tool() -> dict[str, Any]:
    return {
        "name": "book_appointment",
        "description": (
            "Book the appointment at the agreed slot. After booking, repeat "
            "the details to the caller and send an SMS if possible."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "start_time": {
                    "type": "string",
                    "description": "ISO 8601 start time, e.g. 2026-10-05T14:00:00-07:00.",
                },
                "name": {"type": "string"},
                "phone": {"type": "string"},
            },
            "required": ["service", "start_time", "name", "phone"],
        },
    }


async def handle_check_availability(
    *,
    business_id: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    """Return up to 3 slots for the requested date.

    TODO: hit Google Calendar FreeBusy API for the configured calendar id.
    """
    service = (args.get("service") or "").strip()
    date = (args.get("date") or "").strip()
    if not service or not date:
        return {"ok": False, "error": "service and date are required"}

    logger.info("check_availability", business_id=business_id, service=service, date=date)
    return {
        "ok": True,
        "slots": [],  # TODO
    }


async def handle_book_appointment(
    *,
    business_id: str,
    call_id: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    """Create the event. Idempotent: a duplicate call must not double-book."""
    required = ("service", "start_time", "name", "phone")
    missing = [k for k in required if not args.get(k)]
    if missing:
        return {"ok": False, "error": f"missing: {', '.join(missing)}"}

    logger.info(
        "book_appointment",
        business_id=business_id,
        call_id=call_id,
        service=args["service"],
        start_time=args["start_time"],
    )
    # TODO: re-check availability, then Google Calendar events.insert, then
    # insert an appointments row, then enqueue an SMS confirmation.
    return {
        "ok": True,
        "appointment_id": "stub",
        "confirmation_sent": False,
    }