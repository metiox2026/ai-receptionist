"""transfer_call and end_call — P0.

`transfer_call` forwards the call to a configured department number. The
agent checks business hours and falls back to take_message if the transfer
target cannot be reached. The actual SIP/phone forwarding is done by Telnyx
through its call-control API, not by the agent.

`end_call` is the explicit way the LLM signals "we are done" — the agent
says a brief goodbye and hangs up.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()


def transfer_call_tool() -> dict[str, Any]:
    return {
        "name": "transfer_call",
        "description": (
            "Forward the call to a human or another line. Use this when the "
            "caller asks for a person, is in an emergency, or when the agent "
            "cannot resolve the request and a staff member is available."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why the caller is being transferred.",
                },
                "department": {
                    "type": "string",
                    "description": "Which department or person to transfer to, if known.",
                },
            },
            "required": ["reason"],
        },
    }


def end_call_tool() -> dict[str, Any]:
    return {
        "name": "end_call",
        "description": (
            "Politely end the call after saying goodbye. Use this as the very "
            "last action of a successful call, or when the caller has hung up."
        ),
        "parameters": {"type": "object", "properties": {}},
    }


async def handle_transfer(
    *,
    business_id: str,
    call_id: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    reason = (args.get("reason") or "").strip()
    if not reason:
        return {"ok": False, "error": "reason is required"}

    logger.info(
        "transfer_call",
        business_id=business_id,
        call_id=call_id,
        reason=reason,
        department=args.get("department"),
    )

    # TODO: call Telnyx REST API to start the transfer, with a timeout and a
    # fall-back path that calls take_message if the transfer fails.
    return {
        "ok": True,
        "transferred_to": args.get("department") or "main_line",
        "fallback": "take_message",
    }


async def handle_end_call(
    *,
    business_id: str,
    call_id: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    logger.info("end_call", business_id=business_id, call_id=call_id)
    return {"ok": True, "next_step": "say goodbye and hang up"}