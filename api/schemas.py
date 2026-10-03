"""Pydantic schemas — request/response shapes for the HTTP API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from api.models import (
    AppointmentCreator,
    AppointmentStatus,
    CallDirection,
    MessageStatus,
    PromptStatus,
    UserRole,
)


# -----------------------------------------------------------------------------
# Auth / user
# -----------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.staff


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: UserRole


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# -----------------------------------------------------------------------------
# Business
# -----------------------------------------------------------------------------
class BusinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    timezone: str
    phone_number: str | None


# -----------------------------------------------------------------------------
# Contact
# -----------------------------------------------------------------------------
class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone: str
    name: str | None
    tags: list[str]
    is_blocked: bool


# -----------------------------------------------------------------------------
# Call
# -----------------------------------------------------------------------------
class CallTurnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    turn_index: int
    role: str
    text: str | None
    tool_name: str | None
    latency_ms: int | None


class CallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider_call_id: str | None
    direction: CallDirection
    started_at: datetime | None
    ended_at: datetime | None
    duration_sec: int | None
    language: str | None
    intent: str | None
    outcome: str | None
    summary: str | None
    flagged: bool


class CallDetailOut(CallOut):
    """Call with turns and computed totals."""

    turns: list[CallTurnOut] = []
    cost_total_usd: float = 0.0


class CallListQuery(BaseModel):
    date_from: datetime | None = None
    date_to: datetime | None = None
    outcome: str | None = None
    intent: str | None = None
    flagged: bool | None = None
    limit: int = 50
    offset: int = 0


# -----------------------------------------------------------------------------
# Message
# -----------------------------------------------------------------------------
class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    caller_name: str | None
    caller_phone: str | None
    reason: str | None
    status: MessageStatus
    created_at: datetime


class MessageUpdate(BaseModel):
    status: MessageStatus | None = None
    assigned_to: uuid.UUID | None = None
    notes: str | None = None


# -----------------------------------------------------------------------------
# Appointment
# -----------------------------------------------------------------------------
class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service: str
    starts_at: datetime
    ends_at: datetime
    status: AppointmentStatus
    created_by: AppointmentCreator


# -----------------------------------------------------------------------------
# Prompt
# -----------------------------------------------------------------------------
class PromptVersionIn(BaseModel):
    content: dict
    notes: str | None = None


class PromptVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: PromptStatus
    notes: str | None
    created_at: datetime


# -----------------------------------------------------------------------------
# Knowledge
# -----------------------------------------------------------------------------
class KnowledgeItemIn(BaseModel):
    title: str
    content: str


class KnowledgeItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    updated_at: datetime


class KnowledgeGapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    status: str
    created_at: datetime


# -----------------------------------------------------------------------------
# Internal (agent -> api)
# -----------------------------------------------------------------------------
class TurnIn(BaseModel):
    call_id: uuid.UUID
    turn_index: int
    role: str
    text: str | None = None
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result: dict | None = None
    latency_ms: int | None = None


class CallStartIn(BaseModel):
    provider_call_id: str
    business_id: uuid.UUID
    direction: CallDirection = CallDirection.inbound
    caller_phone: str | None = None
    language: str | None = None


class CallEndIn(BaseModel):
    call_id: uuid.UUID
    ended_at: datetime
    duration_sec: int
    cost_telephony: float = 0
    cost_stt: float = 0
    cost_llm: float = 0
    cost_tts: float = 0
    summary: str | None = None
    intent: str | None = None
    outcome: str | None = None
    sentiment: float | None = None
    recording_url: str | None = None