"""Post-call job.

Triggered by the agent when a call ends. Responsibilities:
  1. Read the full transcript from `call_turns`.
  2. Ask the LLM for a 2-3 line summary, intent, outcome, sentiment.
  3. Update the `calls` row.
  4. Enqueue staff notifications for messages taken during the call.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from api.config import get_settings


async def run_post_call(call_id: str) -> dict:
    settings = get_settings()
    # TODO: load the call + turns via async session.
    # TODO: call Claude Haiku with the transcript and the structured
    #       response schema.
    # TODO: persist summary/intent/outcome/sentiment back to the calls row.
    # TODO: enqueue notify_new_message for each take_message tool call.

    return {
        "call_id": call_id,
        "completed_at": datetime.now(tz=timezone.utc).isoformat(),
        "note": "stub — implementation pending",
    }