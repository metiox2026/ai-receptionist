# Deployment

## Server sizing

| Concurrent calls | Suggested server |
|---|---|
| 1–5 | 2 vCPU, 4 GB RAM |
| 5–20 | 4–8 vCPU, 8–16 GB RAM |
| 20+ | Multiple agent instances behind a load balancer |

Voice agents are mostly I/O-bound. Heavy compute happens at the providers.

## First-time deploy

1. Provision a server; firewall SSH on 22 only.
2. Install Docker + Docker Compose.
3. Point a domain at the server's public IP.
4. Clone this repo and `cp .env.example .env`. Fill in the required keys.
5. `make up` brings up the stack.
6. `make migrate` runs Alembic migrations.
7. `make seed` creates the first owner user (interactive).
8. Configure the Telnyx phone number's webhook to your domain.
9. Place a test call. The dashboard's Overview tile should report
   `agent_healthy: OK`.

## Configuration

| Variable | Required | Notes |
|---|---|---|
| `POSTGRES_PASSWORD` | yes | Set a strong password |
| `SECRET_KEY` | yes | Used for JWT |
| `NEXTAUTH_SECRET` | yes | Used for dashboard sessions |
| `TELNYX_API_KEY` | yes (when going live) | |
| `DEEPGRAM_API_KEY` | yes (when going live) | |
| `CARTESIA_API_KEY` | yes (when going live) | |
| `ANTHROPIC_API_KEY` | yes | LLM |
| `GOOGLE_API_KEY` | optional | Fallback LLM |
| `TELEGRAM_BOT_TOKEN` | optional | Staff alerts |

Optional services (Metabase, Langfuse, Prometheus, Grafana) are behind
docker compose profiles. Start them with `--profile analytics` or
`--profile observability`.

## Backups

Nightly `pg_dump` to S3-compatible storage. Test a restore monthly.

```bash
docker compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB \
  | gzip > backups/receptionist-$(date +%F).sql.gz
```

## Reliability

- **Auto-restart** containers. Health checks the agent and api.
- **Fallback URL** in Telnyx: if your server is unreachable, forward to the
  fallback number. Configure this in the Telnyx portal.
- **Spend caps** at each provider. Telnyx: portal. Deepgram: portal.
  Cartesia: portal. Anthropic: console.
- **Max call duration** enforced in the agent (`MAX_CALL_DURATION_SEC`).
- **Tool call rate limit** per call (`MAX_TOOL_CALLS_PER_CALL`).

## Updating

```bash
git pull
docker compose build
docker compose up -d
```

The agent drains active calls before restarting if you give it a graceful
shutdown signal. Set `traefik` or Caddy to drain in front of the api.

## Phased roadmap

### Phase 0 — Scope and content (1–2 days)
- [ ] List services, hours, prices, FAQs, policies
- [ ] Define what the AI must / must not do
- [ ] Decide languages and voice persona
- [ ] Write the first prompt

### Phase 1 — Prompt validation (1–2 days)
- [ ] Run 20+ scenarios in the eval suite
- [ ] Save baseline: `make eval-baseline`

### Phase 2 — Core voice agent, P0 features (week 1)
- [ ] Telephony number and webhook
- [ ] Pipecat pipeline: STT → LLM → TTS streaming
- [ ] Greeting, AI disclosure, interruption handling
- [ ] Tools: `take_message`, `transfer_call`, `end_call`
- [ ] DB: call and turn logging
- [ ] Email notification for messages
- [ ] Max duration, spending caps, basic guardrails

### Phase 3 — Booking + dashboard v1 (week 2)
- [ ] Calendar integration: `check_availability`, `book_appointment`
- [ ] Post-call summary job
- [ ] Dashboard v1 (Option C)
- [ ] Prompt editor with versioning
- [ ] Soft launch on after-hours calls only

### Phase 4 — Intelligence + polish (weeks 3–4)
- [ ] Caller recognition and history
- [ ] Reschedule / cancel, SMS confirmations
- [ ] Knowledge base + RAG + knowledge-gap list
- [ ] Intent and outcome tagging, cost-per-call tracking
- [ ] Telegram/WhatsApp staff alerts, daily summary report
- [ ] Latency tuning from real call data
- [ ] Regression eval runner in CI
- [ ] Full-hours launch

### Phase 5 — Growth features (month 2+)
- [ ] Multilingual support
- [ ] CRM integration
- [ ] Outbound reminder calls
- [ ] Spam filtering and block list
- [ ] Quality review queue
- [ ] Test-call button
- [ ] Multi-tenant support (if reselling)