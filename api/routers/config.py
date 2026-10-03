"""Agent configuration endpoints — prompt versions, business settings, voice."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.models import PromptStatus, PromptVersion
from api.schemas import PromptVersionIn, PromptVersionOut

router = APIRouter()


@router.get("/prompt-versions", response_model=list[PromptVersionOut])
async def list_versions(session: AsyncSession = Depends(get_session)) -> list[PromptVersion]:
    stmt = (
        select(PromptVersion)
        .order_by(PromptVersion.created_at.desc())
        .limit(100)
    )
    return list((await session.scalars(stmt)).all())


@router.post("/prompt-versions", response_model=PromptVersionOut, status_code=201)
async def create_version(
    payload: PromptVersionIn,
    session: AsyncSession = Depends(get_session),
) -> PromptVersion:
    version = PromptVersion(
        business_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # TODO: from auth
        content=payload.content,
        notes=payload.notes,
        status=PromptStatus.draft,
    )
    session.add(version)
    await session.flush()
    return version


@router.post("/prompt-versions/{version_id}/publish", response_model=PromptVersionOut)
async def publish_version(
    version_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PromptVersion:
    """Mark a draft as live. The previously live version becomes archived."""
    new_live = await session.get(PromptVersion, version_id)
    if not new_live:
        raise HTTPException(status_code=404, detail="version not found")
    stmt = select(PromptVersion).where(PromptVersion.status == PromptStatus.live)
    for old_live in (await session.scalars(stmt)).all():
        old_live.status = PromptStatus.archived
    new_live.status = PromptStatus.live
    await session.flush()
    return new_live