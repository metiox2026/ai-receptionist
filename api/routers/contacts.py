"""Contacts and the block list."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.models import Contact
from api.schemas import ContactOut

router = APIRouter()


@router.get("", response_model=list[ContactOut])
async def list_contacts(
    query: str | None = None,
    is_blocked: bool | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Contact]:
    stmt = select(Contact).order_by(Contact.created_at.desc()).limit(200)
    if query:
        like = f"%{query}%"
        stmt = stmt.where((Contact.name.ilike(like)) | (Contact.phone.ilike(like)))
    if is_blocked is not None:
        stmt = stmt.where(Contact.is_blocked == is_blocked)
    return list((await session.scalars(stmt)).all())


@router.get("/{contact_id}", response_model=ContactOut)
async def get_contact(contact_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Contact:
    contact = await session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="contact not found")
    return contact


@router.post("/{contact_id}/block", response_model=ContactOut)
async def block_contact(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Contact:
    contact = await session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="contact not found")
    contact.is_blocked = True
    await session.flush()
    return contact


@router.post("/{contact_id}/unblock", response_model=ContactOut)
async def unblock_contact(
    contact_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Contact:
    contact = await session.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="contact not found")
    contact.is_blocked = False
    await session.flush()
    return contact