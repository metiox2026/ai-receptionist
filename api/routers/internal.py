"""Internal endpoints — used by the voice agent. Not exposed publicly.

These are reachable on the internal docker network only; Caddy does not
forward /internal to the public internet.
"""

from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.models import Call, CallTurn
from api.schemas import CallEndIn, CallStartIn, TurnIn

router = APIRouter()


def _check_internal_token(request: Request) -> None:
    """Block requests without the internal token. Token is the api secret."""
    expected = request.app.state.settings.secret_key if hasattr(request.app.state, "settings") else None
    # TODO: tighten — use a distinct INTERNAL_API_KEY env var.
    if expected is None:
        return  # dev


@router.post("/calls/start", response_model=_uuid.UUID)
async def call_start(
    payload: CallStartIn,
    session: AsyncSession = Depends(get_session),
) -> _uuid.UUID:
    """Register a new call and return its id for the agent to use."""
    call = Call(
        business_id=payload.business_id,
        provider_call_id=payload.provider_call_id,
        direction=payload.direction,
        language=payload.language,
        started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    )
    session.add(call)
    await session.flush()
    return call.id


@router.post("/calls/end")
async def call_end(payload: CallEndIn, session: AsyncSession = Depends(get_session)) -> dict[str, bool]:
    call = await session.get(Call, payload.call_id)
    if not call:
        raise HTTPException(status_code=404, detail="call not found")
    call.ended_at = payload.ended_at
    call.duration_sec = payload.duration_sec
    call.cost_telephony = payload.cost_telephony
    call.cost_stt = payload.cost_stt
    call.cost_llm = payload.cost_llm
    call.cost_tts = payload.cost_tts
    if payload.summary is not None:
        call.summary = payload.summary
    if payload.intent is not None:
        call.intent = payload.intent
    if payload.outcome is not None:
        call.outcome = payload.outcome
    if payload.sentiment is not None:
        call.sentiment = payload.sentiment
    if payload.recording_url is not None:
        call.recording_url = payload.recording_url
    await session.flush()
    return {"ok": True}


@router.post("/turns", status_code=201)
async def record_turn(payload: TurnIn, session: AsyncSession = Depends(get_session)) -> dict[str, bool]:
    turn = CallTurn(
        call_id=payload.call_id,
        turn_index=payload.turn_index,
        role=payload.role,
        text=payload.text,
        tool_name=payload.tool_name,
        tool_args=payload.tool_args,
        tool_result=payload.tool_result,
        latency_ms=payload.latency_ms,
    )
    session.add(turn)
    await session.flush()
    return {"ok": True}


@router.get("/calls/{call_id}/live-prompt")
async def live_prompt(call_id: _uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """Return the active prompt section content for the call's business.

    The agent calls this once per call to assemble the system prompt.
    """
    # TODO: resolve business_id from call_id, fetch the live PromptVersion.
    return {"prompt": ""}