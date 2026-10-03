# Data model

Postgres + pgvector. Each table maps to a SQLAlchemy class in `api/models.py`
and a Pydantic schema in `api/schemas.py`. Migrations live in
`api/migrations/versions/`.

## Tables

```
businesses          ──┐
                      │
users ────────────────┤
                      │
contacts ─────────────┤
                      ├── foreign keys (CASCADE on delete)
calls ────────────────┤
   │                  │
   ├── call_turns     │
   │                  │
messages ─────────────┤
                      │
appointments ─────────┤
                      │
prompt_versions ──────┤
                      │
knowledge_items ──────┤  (pgvector embedding)
knowledge_gaps ──────┤
```

All ids are `uuid` except `call_turns.id` (BIGSERIAL, write-heavy) and
`audit_log.id` (BIGSERIAL).

## `calls`

The central table. One row per inbound (or outbound) call.

| Column | Notes |
|---|---|
| `started_at`, `ended_at`, `duration_sec` | Set by the agent on stream open / close |
| `intent`, `outcome` | Set by the post-call job |
| `summary` | Set by the post-call job (2–3 lines) |
| `recording_url` | Set when the recording is uploaded to S3 / R2 |
| `cost_*` | Set by the post-call job from per-turn usage |
| `flagged`, `flag_note` | Staff can flag a call from the dashboard |

## `call_turns`

Every transcript line plus every tool invocation. Drives the dashboard's
synced audio + transcript view.

## `messages`

Messages the agent took on a call (`take_message` tool). Status workflow:
`new → in_progress → done`.

## `appointments`

Bookings (and service appointments) created by the AI or by staff. Linked
to `external_event_id` for the Google Calendar event when applicable.

## `prompt_versions`

Each version is a JSONB blob of the prompt sections. Status:
`draft → live → archived`. Only one row per business is `live` at a time.

## `knowledge_items`

FAQ snippets retrieved by `search_knowledge`. `embedding` is a 768-dim
vector for cosine similarity search.

## `knowledge_gaps`

Questions the agent could not answer. Staff can resolve by adding an FAQ,
which sets `resolved_item_id`.

## Indexes

The initial migration adds an index on `call_turns.call_id`. Add more in
follow-up revisions as query patterns become clear:

```sql
CREATE INDEX ix_calls_business_started ON calls (business_id, started_at DESC);
CREATE INDEX ix_calls_flagged ON calls (flagged) WHERE flagged;
CREATE INDEX ix_messages_status_created ON messages (status, created_at DESC);
CREATE INDEX ix_appointments_business_starts ON appointments (business_id, starts_at);
```

## Retention

| Table | Default | Configurable |
|---|---|---|
| `calls`, `call_turns` | Indefinite | Yes |
| `recordings` (object storage) | 30 days | Yes |

The Settings page in the dashboard exposes these knobs.