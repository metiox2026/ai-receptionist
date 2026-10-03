"""send_sms — P1.

Templates, not free text. The LLM picks a template type and the tool fills
in the variables. This is the defence against a prompt-injected caller
getting the model to send arbitrary messages.

The destination phone is the caller's number from caller ID, unless the
caller explicitly asked for a different one and the agent has confirmed it.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()

TEMPLATES = {
    "address": "Hi from {business_name}! Our address is {address}. Reply STOP to opt out.",
    "booking_link": "Your appointment with {business_name} is confirmed: {link}. Reply STOP to opt out.",
    "price_list": "Here is the {business_name} price list: {link}. Reply STOP to opt out.",
    "callback": "{business_name} will call you back at {time}. Reply STOP to opt out.",
}


def send_sms_tool() -> dict[str, Any]:
    return {
        "name": "send_sms",
        "description": (
            "Send an SMS to the caller using a fixed template. Choose the "
            "right template type and fill in the variables. Never invent "
            "the message body."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "template": {
                    "type": "string",
                    "enum": list(TEMPLATES.keys()),
                },
                "variables": {
                    "type": "object",
                    "description": "Values to fill into the template.",
                },
            },
            "required": ["template", "variables"],
        },
    }


async def handle(
    *,
    business_id: str,
    caller_phone: str,
    args: dict[str, Any],
) -> dict[str, Any]:
    template = args.get("template")
    if template not in TEMPLATES:
        return {"ok": False, "error": f"unknown template {template!r}"}

    variables = args.get("variables") or {}
    try:
        body = TEMPLATES[template].format(**variables)
    except KeyError as exc:
        return {"ok": False, "error": f"missing template variable {exc.args[0]}"}

    logger.info(
        "send_sms",
        business_id=business_id,
        to=caller_phone,
        template=template,
    )
    # TODO: POST to Telnyx messaging API. Verify caller_phone is E.164.
    return {"ok": True, "to": caller_phone, "body": body}