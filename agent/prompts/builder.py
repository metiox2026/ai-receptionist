"""Assembles the full system prompt from sections loaded from the database
plus the dynamic block computed per call.

Section ordering matters for caching: static content goes first, dynamic last.
The LLM provider's prompt cache keys on the prefix, so as long as the static
section is unchanged the cache hits.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog

from agent.prompts import templates

logger = structlog.get_logger()


async def build_system_prompt(
    *,
    business_id: str,
    caller: dict,
) -> str:
    """Return the full system prompt for this call.

    TODO: fetch the business's prompt sections from the api service or local DB
    and pass them in here. For now this returns a working scaffold.
    """
    # --- Static (cacheable) sections ---
    business_name = "The Business"  # TODO: load from db
    business_facts = "(hours, services, prices, FAQ not yet loaded)"  # TODO
    policies = "(policies not yet loaded)"  # TODO

    static_part = (
        f"You are the receptionist for {business_name}, speaking on the phone.\n\n"
        f"{templates.style()}\n\n"
        f"BUSINESS FACTS\n{business_facts}\n\n"
        f"POLICIES\n{policies}\n\n"
        f"{templates.actions()}\n\n"
        f"{templates.rules(business_name)}"
    )

    # --- Dynamic block (per-call, not cached) ---
    caller_context = _format_caller(caller)
    dynamic = templates.dynamic_block(
        business_name=business_name,
        timezone="UTC",  # TODO: load per business
        now=datetime.now(tz=timezone.utc),
        open_now=True,  # TODO: compute
        announcements=[],  # TODO: load active announcements
        caller_context=caller_context,
    )

    return f"{static_part}\n\n{dynamic}"


def _format_caller(caller: dict) -> str:
    """One-line caller description for the dynamic block."""
    if not caller:
        return "Unknown caller"
    name = caller.get("name", "unknown name")
    history = caller.get("last_interaction_summary")
    if history:
        return f"Returning customer: {name}, last interaction: {history}"
    return f"Known caller: {name}"