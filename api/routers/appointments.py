"""Appointments — list, reschedule, cancel."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import get_session
from api.models import Appointment, AppointmentStatus
from api.schemas import AppointmentOut

router = APIRouter()


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Appointment]:
    stmt = select(Appointment).order_by(Appointment.starts_at.asc()).limit(200)
    if date_from:
        stmt = stmt.where(Appointment.starts_at >= date_from)
    if date_to:
        stmt = stmt.where(Appointment.starts_at <= date_to)
    return list((await session.scalars(stmt)).all())


@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Appointment:
    appt = await session.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="appointment not found")
    if appt.status == AppointmentStatus.cancelled:
        return appt
    appt.status = AppointmentStatus.cancelled
    # TODO: also delete the linked Google Calendar event if external_event_id set.
    await session.flush()
    return appt


@router.post("/{appointment_id}/no-show", response_model=AppointmentOut)
async def mark_no_show(
    appointment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> Appointment:
    appt = await session.get(Appointment, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="appointment not found")
    appt.status = AppointmentStatus.no_show
    await session.flush()
    return appt