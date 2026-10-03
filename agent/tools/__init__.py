"""Tools the agent can call.

Each tool is a small class that returns a Pipecat-compatible tool spec
(name, description, JSON schema) plus a handler that the LLM service invokes.

Tool design rules from the plan:
  - Validate every argument server-side (never trust model output).
  - Idempotency on mutations (booking, cancellation).
  - Short timeouts (2-3s).
  - Rate limit per call.
"""

from __future__ import annotations

from typing import Any

from agent.tools import calendar, knowledge, messages, sms, transfer


async def all_tools_for_business(business_id: str) -> list[dict[str, Any]]:
    """Return the tool specs the LLM can call for this business.

    Loaded here rather than at module-import time so that per-business config
    (transfer numbers, calendar id, etc.) can be honoured.
    """
    return [
        # P0 — core
        messages.take_message_tool(),
        transfer.transfer_call_tool(),
        transfer.end_call_tool(),
        # P1 — booking + sms
        calendar.check_availability_tool(),
        calendar.book_appointment_tool(),
        sms.send_sms_tool(),
        # Knowledge + caller lookup
        knowledge.search_knowledge_tool(),
        knowledge.log_unanswered_tool(),
    ]