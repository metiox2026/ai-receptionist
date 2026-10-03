"""Messages inbox."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.models import Message, MessageStatus
from api.schemas import MessageOut, MessageUpdate

router = APIRouter()


@router.get("", response_model=list[MessageOut])
async def list_messages(
    status: MessageStatus | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Message]:
    stmt = select(Message).order_by(Message.created_at.desc()).limit(200)
    if status:
        stmt = stmt.where(Message.status == status)
    return list((await session.scalars(stmt)).all())


@router.get("/{message_id}", response_model=MessageOut)
async def get_message(message_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Message:
    msg = await session.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="message not found")
    return msg


@router.patch("/{message_id}", response_model=MessageOut)
async def update_message(
    message_id: uuid.UUID,
    payload: MessageUpdate,
    session: AsyncSession = Depends(get_session),
) -> Message:
    msg = await session.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="message not found")
    if payload.status is not None:
        msg.status = payload.status
    if payload.assigned_to is not None:
        msg.assigned_to = payload.assigned_to
    if payload.notes is not None:
        msg.notes = payload.notes
    await session.flush()
    return msg