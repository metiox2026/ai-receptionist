# AI Phone Receptionist

Self-hosted, low-cost, low-latency voice receptionist with a custom management dashboard.

This repository contains the scaffold for an AI receptionist that answers inbound calls,
takes messages, books appointments, and transfers to humans. The full plan is in
`docs/architecture.md`.

## Status

**Scaffold.** The repository layout, services, configuration, and skeleton code are in
place. Each module needs real implementation, API keys, and tuning before launch. See the
[Phased Roadmap](docs/deployment.md#phased-roadmap) in the docs.

## Architecture (one-paragraph version)

A caller dials the business phone number → telephony provider (Telnyx) opens a media
stream → the **voice agent** (Pipecat) runs the loop STT → LLM → TTS → tools, all
streaming → the **FastAPI backend** persists calls, messages, appointments and serves
the dashboard → the **Next.js dashboard** is where staff review calls, edit the agent
prompt, and manage bookings.

## Tech stack

| Layer | Choice |
|---|---|
| Voice orchestration | Pipecat (Python) |
| Telephony | Telnyx |
| STT | Deepgram (streaming) |
| LLM | Claude Haiku 4.5 (primary), Gemini Flash-Lite (fallback) |
| TTS | Cartesia |
| Backend API | FastAPI |
| Database | PostgreSQL with pgvector |
| Cache / queue | Redis |
| Dashboard | Next.js 14 (App Router) + Tailwind + shadcn/ui |
| Reverse proxy | Caddy |
| Containers | Docker Compose |

## Repository layout

```
.
├── agent/          # Pipecat voice agent (webhook + media stream + tools)
├── api/            # FastAPI backend (webhooks, dashboard API, background jobs)
├── dashboard/      # Next.js custom dashboard
├── eval/           # Scenario-based regression tests
├── infra/          # Caddyfile, Prometheus, Grafana dashboards
├── docs/           # Architecture, data model, prompts, deployment, security
├── docker-compose.yml
├── .env.example
└── Makefile
```

## Quickstart

> **Note:** this is the end-state quickstart. Until Phase 2 is built, several of these
> commands will not do anything useful.

1. **Copy environment template**

   ```bash
   cp .env.example .env
   ```

   Fill in the API keys you have. The app will refuse to start if a required key is
   missing. Optional services stay disabled.

2. **Start the stack**

   ```bash
   make up
   ```

   This brings up Postgres, Redis, the agent, the API, and the dashboard. Optional
   services (Metabase, Langfuse, Prometheus) are behind `--profile` flags.

3. **Run migrations and create the first owner user**

   ```bash
   make migrate
   make seed
   ```

4. **Open the dashboard**

   Dashboard: <http://localhost:3000>
   API docs: <http://localhost:8000/docs>

5. **Wire up the phone number**

   In your Telnyx portal, set the call-control webhook to
   `https://<your-domain>/webhooks/telnyx` and the media-streaming URL to
   `wss://<your-domain>/media/telnyx`. The Caddyfile routes both.

## Common commands

```bash
make up           # docker compose up -d
make down         # docker compose down
make logs         # tail logs for all services
make logs-agent   # tail logs for the agent only
make migrate      # run Alembic migrations
make seed         # seed the first business + admin user
make test         # run pytest (api + agent unit tests)
make eval         # run the scenario eval suite (text mode)
make shell-api    # open a shell in the api container
make shell-agent  # open a shell in the agent container
```

## Before you start spending money

You do **not** need real API keys to develop locally. To work on the prompt or the
dashboard without making a phone call, run the eval suite (`make eval`) — it replays
text scenarios against the LLM with stubbed tools.

When you are ready to make real calls, sign up for the providers in the order they
appear in `.env.example`. Start with the cheapest LLM that passes your eval set.

## Phased roadmap

See `docs/deployment.md` for the full roadmap. Short version:

- **Phase 0–1:** scope, content, prompt validation (text mode)
- **Phase 2:** core voice agent, P0 tools (take message, transfer, end call)
- **Phase 3:** booking, dashboard v1, soft launch
- **Phase 4:** intelligence, polish, full launch
- **Phase 5:** growth features (multilingual, CRM, outbound)

## License

Proprietary unless a LICENSE file is added.