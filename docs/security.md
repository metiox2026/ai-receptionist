# Security and privacy

## Disclosures

- **AI disclosure**: the greeting says "this is an AI assistant." Required
  in many jurisdictions.
- **Recording notice**: if recording is on, the greeting also says so. Off
  by default for jurisdictions with strict consent rules.

## Authentication

- Dashboard: bcrypt + HS256 JWT.
- API-to-API: shared `SECRET_KEY` for internal endpoints, plus a future
  per-service token. The internal router (`/internal/*`) is reachable on the
  docker network only — Caddy does not forward it publicly.

## Webhook verification

Telnyx webhooks are signed with Ed25519. Verify the signature against
`TELNYX_PUBLIC_KEY` and the raw request bytes before processing. Reject
unsigned requests with HTTP 401.

## Data protection

- All traffic is TLS via Caddy.
- DB password and JWT secrets live in `.env` (never in code).
- PII redaction: card numbers spoken by callers are stripped from
  transcripts before they hit the database. The agent never accepts card
  numbers by voice — it sends a payment link by SMS instead.
- Encryption at rest: rely on the managed Postgres disk encryption; encrypt
  recording files in S3-compatible storage with SSE-S3 or SSE-KMS.

## Prompt injection defence

- The agent has **no secrets** in context. Every privileged action goes
  through a tool that validates inputs server-side.
- All tool arguments are validated against the JSON schema, and types
  like phone numbers are normalised.
- SMS messages use **templates only** — the model picks the template and
  fills in variables, but the body is rendered server-side.
- Knowledge-base snippets are wrapped in system prompts that instruct the
  agent to ignore any instructions they contain.

## Cost controls

- Per-call: `MAX_CALL_DURATION_SEC`, `MAX_TOOL_CALLS_PER_CALL`.
- Daily: `MAX_DAILY_SPEND_USD` (enforced by provider-side caps; mirrored
  in the agent's running sum).
- Concurrent: `MAX_CONCURRENT_CALLS` (rejected when exceeded).

## Backups

Nightly `pg_dump` to S3-compatible storage. Object storage versioned and
lifecycle-managed. Test restores monthly.

## Threat model (strict)

| Threat | Mitigation |
|---|---|
| Spam / robocall | Block list + per-number rate limit + short-call detection |
| Prompt injection via caller | Server-side tool validation, template SMS, no secrets in prompt |
| Webhook spoofing | Ed25519 signature verification |
| Account takeover | bcrypt, 2FA (TBD), JWT expiry, audit log |
| Data exfiltration via LLM | Egress allow redaction; agent has no DB credentials |
| Insider abuse | Role-based access, audit log, retention policy |

## Regulatory checklist

| Concern | Action |
|---|---|
| AI disclosure (US, EU) | Greeting announces it |
| Recording consent (varies) | Default off in two-party jurisdictions |
| GDPR (EU) | Data minimization, retention policy, deletion on request |
| HIPAA (US, healthcare) | NOT YET — do not handle PHI without BAA |
| PCI DSS (cards) | Never accept card numbers by voice; payment links by SMS |
| Telecom rules (varies) | Check carrier requirements for business numbers, SMS sender IDs |

## Auditing

Every config change is logged to `audit_log`. The Settings page exposes
the table.