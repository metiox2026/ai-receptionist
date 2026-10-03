# Prompts

The agent prompt is split into named sections, each editable in the
dashboard. Sections live in `prompt_versions.content` (JSONB) and are
assembled by `agent/prompts/builder.py` before each call.

## Sections

| Key | What it controls | Typical length |
|---|---|---|
| `persona` | Who the agent is | 1 line |
| `style` | Tone, length, formatting rules | ~150 tokens |
| `business_facts` | Hours, address, services, prices | 300–1000 tokens |
| `policies` | Cancellation, payment, "we don't do that" | ~200 tokens |
| `actions` | When to use which tool | ~150 tokens |
| `rules` | Hard guardrails (no secrets, no inventions) | ~150 tokens |
| `escalation` | When to transfer or take a message | ~100 tokens |

A `prompt_version` snapshot is the whole JSONB blob. Publishing a draft
archives the previous live version. The dashboard shows the full diff.

## Static vs dynamic

Static sections (everything except the per-call block) are placed **first**
in the assembled system prompt. The dynamic block goes **last**:

```text
[ static, cacheable prefix — LLM provider caches this ]
- persona
- style
- business_facts
- policies
- actions
- rules
- escalation

[ dynamic, per-call suffix — never cached ]
- now: 2026-10-02 10:04 UTC (America/Los_Angeles)
- status: OPEN
- announcements: - (none)
- caller: returning customer Sara, last interaction: haircut on 3 Sept
```

This ordering keeps the prompt cache hit when only the dynamic block
changes between calls.

## Iteration workflow

1. Edit a section in the dashboard.
2. Click **Save draft** — a new `prompt_versions` row is created with
   `status = draft`.
3. Run `make eval` against the draft (the eval runner takes a prompt
   override).
4. Click **Publish** when happy. The agent starts using it on the next call.
5. If something breaks, click **Roll back** to make the previous live
   version live again.

## Versioning

`prompt_versions.id` is stored on every `calls` row so we can correlate
behaviour changes to prompt changes.

## What never goes in the prompt

- API keys
- Internal URLs (the agent calls them through the internal router)
- Tool implementation details
- Customer PII beyond what the caller just told us

The agent has no secrets, only public instructions + tool results.