# Architecture

## One-paragraph overview

A caller dials the business phone number → the telephony provider (Telnyx)
opens a media stream → the **voice agent** (Pipecat) runs the loop
STT → LLM → TTS → tools, all streaming → the **FastAPI backend** persists
calls, messages, appointments and serves the dashboard → the **Next.js
dashboard** is where staff review calls, edit the agent prompt, and manage
bookings.

```
                         ┌──────────────────────────────────────────┐
                         │             YOUR SERVER                  │
Caller ──► Telephony ───►│  Voice Agent (Pipecat)                   │
        (Telnyx/Twilio)  │   ├─ VAD + Turn detection                │
                         │   ├─ STT (Deepgram, streaming)           │
                         │   ├─ LLM (Claude Haiku + Gemini fallback) │
                         │   │    └─ Tools ──► Calendar / DB / SMS  │
                         │   └─ TTS (Cartesia)                      │
                         │                                          │
                         │  API Server (FastAPI)                    │
                         │   ├─ Webhooks (call start/end)           │
                         │   ├─ Dashboard API                       │
                         │   └─ Background jobs (summaries, SMS)    │
                         │                                          │
                         │  PostgreSQL ── Redis ── Object storage   │
                         └───────────────┬──────────────────────────┘
                                         │
                              Dashboard (Next.js) ◄── Staff / Owner
```

## Call lifecycle

1. Caller dials the business number.
2. Telephony provider hits your webhook (`/webhooks/telnyx`) and opens a
   media stream (`/media/telnyx` WebSocket) to the voice agent.
3. Agent looks up the caller by phone number.
4. Agent plays an instant greeting, then runs the loop:
   **listen → transcribe → think → call tools if needed → speak.**
5. Call ends (caller hangs up, `end_call` tool, or max duration).
6. Post-call job: store transcript, generate summary, classify intent and
   outcome, compute cost, send notifications.

## Service boundaries

| Service | Owns | Talks to |
|---|---|---|
| `agent` | Conversation state, the live media stream | Telnyx, Deepgram, Cartesia, Anthropic, Google, `api` (writes turns) |
| `api` | HTTP API, webhooks, business rules, migrations | Postgres, Redis, Telnyx REST, Google Calendar |
| `worker` | Post-call summary, daily report, async jobs | Postgres, Redis, Telegram, SMTP, object storage |
| `dashboard` | UI, session/auth | `api` via `/api/proxy/*` (Caddy rewrite) |
| `caddy` | TLS, reverse proxy, request routing | All of the above |

## Latency budget

Target **< 800 ms** from end of caller speech to first audio out.

| Stage | Budget | Where it's optimised |
|---|---|---|
| Endpointing (silence → end-of-turn) | 300–500 ms | Pipecat turn detection tuning |
| STT finalisation | 100–200 ms | Streaming partials, no full re-encode |
| LLM first token | 200–400 ms | Thinking off, short prompt, prompt caching |
| TTS first byte | 50–100 ms | Cartesia Sonic, pre-warm connection |
| Network | ~10 ms | Co-locate, persistent HTTP/2 |

Each turn records the time at every stage. The dashboard shows p50 / p95.

## Cost model

Per minute, all components:

| Component | USD/min |
|---|---|
| Telephony (Telnyx inbound) | $0.005–$0.015 |
| STT (Deepgram) | $0.004–$0.01 |
| TTS (Cartesia) | $0.01–$0.03 |
| LLM (Haiku) | ~$0.001–$0.01 |
| **Total** | **~$0.03–$0.06** |

20 calls/day × 2.5 min each ≈ 1,500 min/month → $45–$90 / month for the
voice parts. Server and storage add another $5–$30/month.