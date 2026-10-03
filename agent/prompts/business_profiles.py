"""Business profiles for the demo.

In production, this data comes from the `businesses` table in postgres
(see docs/data-model.md). For the standalone demo we ship a small set of
hardcoded profiles keyed by `business_id`. Add or edit entries here to
change the receptionist's behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BusinessProfile:
    """Everything the prompt builder reads to assemble the system prompt."""
    name: str
    tagline: str
    hours: str
    timezone: str
    services: list[str]
    pricing: list[str]
    service_area: str
    industries: list[str]
    tech_stack: list[str]
    escalation: str          # what the agent does when caller asks for a human
    policies: list[str]
    contact_phone: str
    contact_email: str
    faq: list[tuple[str, str]]   # (question, answer) pairs
    extra_rules: list[str] = field(default_factory=list)


METIOX_SOLUTIONS: BusinessProfile = BusinessProfile(
    name="Metiox Solutions LLC",
    tagline="Custom software, web apps, and AI integrations that move your business forward.",
    hours="Monday to Friday, 9:00 AM to 6:00 PM Gulf Standard Time (Dubai, UTC+4). "
          "Closed on weekends and UAE public holidays.",
    timezone="GST (UTC+4)",
    services=[
        "Discovery / consultation calls (free 30-minute intro)",
        "Project quotes and scoping",
        "Custom web applications (React, Next.js, Python, FastAPI)",
        "Mobile apps (iOS / Android)",
        "AI integrations and conversational assistants",
        "Support and maintenance for existing clients",
    ],
    pricing=[
        "Discovery / consultation calls: free",
        "Project quotes: prepared after the discovery call; minimum engagement $5,000 USD",
        "Hourly work: $150 USD / hour",
        "Retainer support plans: available for existing clients",
    ],
    service_area="Worldwide remote; onsite in the United Arab Emirates (Dubai, Abu Dhabi, Sharjah).",
    industries=[
        "SaaS and B2B platforms",
        "Fintech and payments",
        "E-commerce and marketplaces",
        "Healthtech",
        "Logistics",
        "Internal tools and operations",
    ],
    tech_stack=[
        "React, Next.js, TypeScript",
        "Python, FastAPI, Node.js",
        "PostgreSQL, MongoDB",
        "AWS, Docker, Kubernetes",
        "Anthropic, OpenAI, open-source LLMs",
        "Deepgram (STT), Cartesia (TTS)",
    ],
    escalation=(
        "Take a detailed message with name, phone, and reason — never promise a "
        "specific callback time. Mention that someone from the team will reach "
        "out within one business day."
    ),
    policies=[
        "Never quote exact project prices without a discovery call.",
        "Always ask how the caller heard about Metiox Solutions.",
        "Mention the free 30-minute discovery call to new prospects.",
        "For existing clients with urgent issues, take a detailed message and "
        "flag it as urgent so it gets escalated quickly.",
        "Do not give technical implementation advice over the phone — route "
        "those to a discovery call.",
        "Never make commitments about timelines without consulting the team.",
    ],
    contact_phone="+971-4-XXX-XXXX",       # TODO: replace with real number
    contact_email="hello@metiox.com",    # TODO: replace with real address
    faq=[
        ("What does Metiox Solutions do?",
         "We build custom software — web apps, mobile apps, and AI integrations — "
         "for businesses that need reliable engineering teams."),
        ("How much does a project cost?",
         "It depends on scope. Our minimum engagement is $5,000 USD and most "
         "projects run between $15k and $80k. The best next step is a free "
         "30-minute discovery call."),
        ("Do you work with startups?",
         "Yes. We work with funded startups, established SMBs, and enterprise teams."),
        ("Where are you based?",
         "We're based in Dubai, United Arab Emirates, and work with clients worldwide."),
        ("How quickly can you start?",
         "For new projects we typically onboard within 1–2 weeks after a signed scope."),
        ("Do you do hourly work?",
         "Yes, at $150 USD per hour, billed monthly. Most clients prefer a fixed-scope project."),
        ("Can you maintain an existing codebase?",
         "Yes — we have a support / maintenance offering for existing clients."),
    ],
    extra_rules=[
        "After every tool call, briefly confirm to the caller what you did. "
        "Never end a turn with empty content.",
    ],
)


# Map business_id -> profile. Add more here for multi-tenant demos.
PROFILES: dict[str, BusinessProfile] = {
    "metiox": METIOX_SOLUTIONS,
}


def get_profile(business_id: str) -> BusinessProfile:
    """Look up a profile by id. Falls back to Metiox so the demo always works."""
    return PROFILES.get(business_id) or METIOX_SOLUTIONS