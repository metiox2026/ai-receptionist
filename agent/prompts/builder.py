"""Assembles the full system prompt from sections loaded from the database
plus the dynamic block computed per call.

Section ordering matters for caching: static content goes first, dynamic last.
The LLM provider's prompt cache keys on the prefix, so as long as the static
section is unchanged the cache hits.

In production the business profile comes from postgres. For the standalone
demo it comes from `agent.prompts.business_profiles` — a small dict of
hardcoded profiles keyed by `business_id`.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog

from agent.prompts import templates
from agent.prompts.business_profiles import BusinessProfile, get_profile

logger = structlog.get_logger()


async def build_system_prompt(
    *,
    business_id: str,
    caller: dict,
) -> str:
    """Return the full system prompt for this call.

    The static part (identity, facts, policies, actions, rules) is stable per
    business — the LLM provider's prompt cache can reuse it. The dynamic
    block (current time, announcements, caller context) is per-call.
    """
    profile = get_profile(business_id)

    static_part = _build_static(profile)
    dynamic = templates.dynamic_block(
        business_name=profile.name,
        timezone=profile.timezone,
        now=datetime.now(tz=timezone.utc),
        open_now=_is_open_now(profile),
        announcements=[],
        caller_context=_format_caller(caller),
    )

    return f"{static_part}\n\n{dynamic}"


def _build_static(profile: BusinessProfile) -> str:
    """Assemble the cacheable section of the system prompt."""
    facts = _render_facts(profile)
    policies = _render_policies(profile)
    return (
        f"You are the receptionist for {profile.name}, speaking on the phone.\n"
        f"{profile.tagline}\n\n"
        f"{templates.style()}\n\n"
        f"BUSINESS FACTS\n{facts}\n\n"
        f"POLICIES\n{policies}\n\n"
        f"{templates.actions()}\n\n"
        f"{templates.rules(profile.name)}\n\n"
        f"{templates.confirm_after_tool()}"
    )


def _render_facts(p: BusinessProfile) -> str:
    """Pretty-print the BusinessProfile as a labelled key/value block."""
    lines: list[str] = []
    lines.append(f"- Name: {p.name}")
    lines.append(f"- Hours: {p.hours}")
    lines.append(f"- Timezone: {p.timezone}")
    if p.services:
        lines.append("- Services:")
        for s in p.services:
            lines.append(f"  - {s}")
    if p.pricing:
        lines.append("- Pricing:")
        for s in p.pricing:
            lines.append(f"  - {s}")
    if p.service_area:
        lines.append(f"- Service area: {p.service_area}")
    if p.industries:
        lines.append("- Industries served: " + ", ".join(p.industries))
    if p.tech_stack:
        lines.append("- Tech stack: " + ", ".join(p.tech_stack))
    if p.contact_phone:
        lines.append(f"- Business phone: {p.contact_phone}")
    if p.contact_email:
        lines.append(f"- Business email: {p.contact_email}")
    if p.faq:
        lines.append("- FAQ:")
        for q, a in p.faq:
            lines.append(f"  Q: {q}")
            lines.append(f"  A: {a}")
    return "\n".join(lines)


def _render_policies(p: BusinessProfile) -> str:
    """Format the policy list (escalation + per-business rules + extra_rules)."""
    parts: list[str] = []
    if p.escalation:
        parts.append(f"- Escalation: {p.escalation}")
    for line in p.policies:
        parts.append(f"- {line}")
    for line in p.extra_rules:
        parts.append(f"- {line}")
    return "\n".join(parts)


def _is_open_now(p: BusinessProfile) -> bool:
    """Best-effort open/closed check based on weekday + business hours string.

    The full system parses the hours string out of the business record; this
    is a coarse default for the demo. Returns True on weekends so callers
    can still leave a message.
    """
    now = datetime.now(tz=timezone.utc)
    weekday = now.weekday()  # 0 = Monday
    # If hours string mentions weekends closed, treat Sat/Sun as closed.
    closed_str = "weekend" in p.hours.lower() or "saturday" in p.hours.lower()
    if closed_str and weekday >= 5:
        return False
    # Mon-Fri 9am-6pm in the business timezone (assume UTC for the demo).
    return 9 <= now.hour < 18


def _format_caller(caller: dict) -> str:
    """One-line caller description for the dynamic block."""
    if not caller:
        return "Unknown caller"
    name = caller.get("name", "unknown name")
    history = caller.get("last_interaction_summary")
    if history:
        return f"Returning customer: {name}, last interaction: {history}"
    return f"Known caller: {name}"