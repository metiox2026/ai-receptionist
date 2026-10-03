"""FastAPI entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.db import healthcheck
from api.routers import (
    appointments,
    auth,
    calls,
    config as config_router,
    contacts,
    internal,
    messages,
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper(), logging.INFO)
        ),
    )
    logger.info("api_starting", environment=settings.environment)
    yield
    logger.info("api_stopping")


app = FastAPI(
    title="Receptionist API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — locked down in production. The dashboard reads from the same origin
# via Caddy, so the defaults are conservative.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.public_base_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    """Liveness + dependency probe."""
    deps = await healthcheck()
    ok = all(deps.get(k) for k in ("db", "redis"))
    return {"ok": ok, "dependencies": deps}


# -----------------------------------------------------------------------------
# Routers
# -----------------------------------------------------------------------------
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(calls.router, prefix="/calls", tags=["calls"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
app.include_router(config_router.router, prefix="/config", tags=["config"])
app.include_router(internal.router, prefix="/internal", tags=["internal"])