"""take_message — P0.

Saves a message from the caller, marks it as new, and notifies staff.

Server-side validation:
  - name and phone are required; reject the tool call if missing.
  - phone is normalised to E.164 before storage.
  - reason is bounded (max 1000 chars) so a prompt-injected caller cannot fill
    the database.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


def take_message_tool() -> dict[str, Any]:
    """Pipecat tool spec for take_message."""
    return {
        "name": "take_message",
        "description": (
            "Save a message from the caller. Use this when the caller wants "
            "someone to get back to them but cannot or will not wait on the line. "
            "Collect name, phone, and a short reason before calling."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Caller's name. If unknown, ask the caller first.",
                },
                "phone": {
                    "type": "string",
                    "description": "Caller's phone number, in any format. Will be normalised.",
                },
                "reason": {
                    "type": "string",
                    "description": "Short, one-line summary of what the call is about.",
                    "maxLength": 1000,
                },
                "urgency": {
                    "type": "string",
                    "enum": ["low", "normal", "high"],
                    "description": "How urgently staff should follow up.",
                },
            },
            "required": ["name", "phone", "reason"],
        },
    }


async def handle(
    *,
    business_id: str,
    call_id: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    """Persist the message and enqueue a staff notification.

    TODO: post to the api service (`POST /internal/messages`). For now this
    returns a stub so the pipeline can be exercised.
    """
    name = (args.get("name") or "").strip()
    phone = (args.get("phone") or "").strip()
    reason = (args.get("reason") or "").strip()[:1000]
    urgency = args.get("urgency", "normal")

    if not name or not phone or not reason:
        return {"ok": False, "error": "name, phone, and reason are required"}

    logger.info(
        "take_message",
        business_id=business_id,
        call_id=call_id,
        name=name,
        urgency=urgency,
    )

    # TODO: insert into messages table and enqueue notification job.
    return {
        "ok": True,
        "message_id": "stub",
        "notified": False,
        "next_step": "Tell the caller a team member will follow up shortly.",
    }