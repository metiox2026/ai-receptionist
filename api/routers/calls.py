"""Calls — list, detail, flag."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.models import Call, CallTurn
from api.schemas import CallDetailOut, CallListQuery, CallOut, CallTurnOut

router = APIRouter()


@router.get("", response_model=list[CallOut])
async def list_calls(
    query: CallListQuery = Depends(),  # type: ignore[assignment]
    session: AsyncSession = Depends(get_session),
) -> list[Call]:
    stmt = select(Call).order_by(Call.started_at.desc().nullslast()).limit(query.limit)
    if query.offset:
        stmt = stmt.offset(query.offset)
    if query.date_from:
        stmt = stmt.where(Call.started_at >= query.date_from)
    if query.date_to:
        stmt = stmt.where(Call.started_at <= query.date_to)
    if query.outcome:
        stmt = stmt.where(Call.outcome == query.outcome)
    if query.intent:
        stmt = stmt.where(Call.intent == query.intent)
    if query.flagged is not None:
        stmt = stmt.where(Call.flagged == query.flagged)
    return list((await session.scalars(stmt)).all())


@router.get("/{call_id}", response_model=CallDetailOut)
async def get_call(call_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:
    call = await session.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="call not found")
    turns = list(
        (
            await session.scalars(
                select(CallTurn).where(CallTurn.call_id == call_id).order_by(CallTurn.turn_index)
            )
        ).all()
    )
    cost_total = float(
        (call.cost_telephony or 0)
        + (call.cost_stt or 0)
        + (call.cost_llm or 0)
        + (call.cost_tts or 0)
    )
    return {
        **CallDetailOut.model_validate(call).model_dump(),
        "turns": [CallTurnOut.model_validate(t).model_dump() for t in turns],
        "cost_total_usd": cost_total,
    }


@router.post("/{call_id}/flag")
async def flag_call(
    call_id: uuid.UUID,
    note: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    call = await session.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="call not found")
    call.flagged = True
    call.flag_note = note
    await session.flush()
    return {"ok": True}