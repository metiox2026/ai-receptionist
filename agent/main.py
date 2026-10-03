"""Agent entry point.

Exposes:
  GET  /healthz             — liveness probe
  POST /webhooks/telnyx     — Telnyx call-control webhook (call started, ringing, etc.)
  WS   /media/telnyx        — bidirectional audio media stream

The actual conversation loop lives in `pipeline.py`. This file is the thin HTTP
shell that validates webhooks and hands the stream off to a new pipeline.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request, WebSocket, status
from fastapi.responses import JSONResponse

from agent.config import get_settings
from agent.pipeline import run_call

logger = structlog.get_logger()
settings = get_settings()


# -----------------------------------------------------------------------------
# Lifespan — startup checks
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
    )
    logger.info("agent_starting", environment=settings.environment)
    yield
    logger.info("agent_stopping")


app = FastAPI(title="Receptionist Voice Agent", lifespan=lifespan)


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    """Liveness probe. Return 200 if process is up and provider keys present."""
    missing = []
    if not settings.telnyx_api_key:
        missing.append("TELNYX_API_KEY")
    if not settings.deepgram_api_key:
        missing.append("DEEPGRAM_API_KEY")
    if not settings.cartesia_api_key:
        missing.append("CARTESIA_API_KEY")
    if not (settings.anthropic_api_key or settings.google_api_key):
        missing.append("ANTHROPIC_API_KEY or GOOGLE_API_KEY")
    if missing:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ok": False, "missing": missing},
        )
    return {"ok": True}


# -----------------------------------------------------------------------------
# Telnyx webhook — call lifecycle events
# -----------------------------------------------------------------------------
@app.post("/webhooks/telnyx")
async def telnyx_webhook(request: Request) -> JSONResponse:
    """Handle call-control events from Telnyx.

    Validates the signature, then enqueues or returns the right response.
    The heavy lifting (media stream, conversation) happens on /media/telnyx.
    """
    # TODO: verify Telnyx signature using settings.telnyx_public_key + the raw body
    #       (Ed25519). Reject with HTTPException(401) if invalid.
    body = await request.json()
    event_type = body.get("data", {}).get("event_type")
    logger.info("telnyx_event", event_type=event_type)
    return JSONResponse({"status": "received"})


# -----------------------------------------------------------------------------
# Telephony media stream — bidirectional audio
# -----------------------------------------------------------------------------
@app.websocket("/media/telnyx")
async def media_telnyx(websocket: WebSocket) -> None:
    """Bidirectional audio stream from Telnyx.

    Pipecat expects raw 16-bit PCM frames at 8 kHz (Telnyx default) on the
    inbound side and writes TTS audio on the outbound side. The Pipecat
    transport layer wraps the WebSocket; we just hand off to run_call.
    """
    await websocket.accept()
    try:
        await run_call(websocket)
    except Exception:
        logger.exception("media_stream_error")
        try:
            await websocket.close()
        except Exception:
            pass


# -----------------------------------------------------------------------------
# Local dev entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "agent.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8765")),
        reload=True,
    )