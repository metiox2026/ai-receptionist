"""SQLAlchemy models for the receptionist domain. Matches the schema in
docs/data-model.md.

We use SQLAlchemy 2.0 typed declarative style. The pgvector `embedding`
column on `knowledge_items` is declared using the `pgvector.sqlalchemy.Vector`
type — added in a follow-up migration once pgvector is available.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.db import Base


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------
class CallDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class TurnRole(str, enum.Enum):
    caller = "caller"
    agent = "agent"
    tool = "tool"


class MessageStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    done = "done"


class AppointmentStatus(str, enum.Enum):
    booked = "booked"
    cancelled = "cancelled"
    completed = "completed"
    no_show = "no_show"


class AppointmentCreator(str, enum.Enum):
    ai = "ai"
    staff = "staff"


class PromptStatus(str, enum.Enum):
    draft = "draft"
    live = "live"
    archived = "archived"


class UserRole(str, enum.Enum):
    owner = "owner"
    manager = "manager"
    staff = "staff"
    read_only = "read_only"


# -----------------------------------------------------------------------------
# Tables
# -----------------------------------------------------------------------------
class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    phone_number: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.staff)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("business_id", "phone", name="uq_contacts_business_phone"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    notes: Mapped[str | None] = mapped_column(Text)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Call(Base):
    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL")
    )
    provider_call_id: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[CallDirection] = mapped_column(
        Enum(CallDirection), nullable=False, default=CallDirection.inbound
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_sec: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str | None] = mapped_column(String(16))

    intent: Mapped[str | None] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(Text)
    sentiment: Mapped[float | None] = mapped_column(Float)

    summary: Mapped[str | None] = mapped_column(Text)
    recording_url: Mapped[str | None] = mapped_column(Text)

    prompt_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    cost_telephony: Mapped[float] = mapped_column(Numeric(10, 5), default=0)
    cost_stt: Mapped[float] = mapped_column(Numeric(10, 5), default=0)
    cost_llm: Mapped[float] = mapped_column(Numeric(10, 5), default=0)
    cost_tts: Mapped[float] = mapped_column(Numeric(10, 5), default=0)

    flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    flag_note: Mapped[str | None] = mapped_column(Text)

    turns: Mapped[list["CallTurn"]] = relationship(
        back_populates="call", cascade="all, delete-orphan", lazy="noload"
    )


class CallTurn(Base):
    __tablename__ = "call_turns"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    call_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[TurnRole] = mapped_column(Enum(TurnRole), nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    tool_name: Mapped[str | None] = mapped_column(Text)
    tool_args: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    tool_result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    call: Mapped[Call] = relationship(back_populates="turns")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    call_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    caller_name: Mapped[str | None] = mapped_column(Text)
    caller_phone: Mapped[str | None] = mapped_column(String(32))
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus), nullable=False, default=MessageStatus.new
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    call_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    service: Mapped[str] = mapped_column(Text, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), nullable=False, default=AppointmentStatus.booked
    )
    external_event_id: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[AppointmentCreator] = mapped_column(
        Enum(AppointmentCreator), nullable=False, default=AppointmentCreator.ai
    )


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[PromptStatus] = mapped_column(
        Enum(PromptStatus), nullable=False, default=PromptStatus.draft
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text)


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # pgvector column. Defined as raw SQL in the initial migration; here we use
    # a permissive JSONB fallback for non-pgvector dev environments.
    embedding: Mapped[Any] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    call_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    resolved_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str | None] = mapped_column(Text)
    diff: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )