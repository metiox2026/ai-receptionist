"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-02

Creates the full receptionist schema in one go so the dev environment is bootable
from scratch. In production, prefer splitting this into per-table migrations.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector extension for the knowledge_items.embedding column.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "businesses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
        sa.Column("phone_number", sa.String(32)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.Text, unique=True, nullable=False),
        sa.Column(
            "role",
            sa.Enum("owner", "manager", "staff", "read_only", name="user_role"),
            nullable=False,
            server_default="staff",
        ),
        sa.Column("password_hash", sa.Text, nullable=False),
    )

    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("name", sa.Text),
        sa.Column("email", sa.Text),
        sa.Column("tags", postgresql.ARRAY(sa.Text), server_default="{}"),
        sa.Column("notes", sa.Text),
        sa.Column("is_blocked", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("business_id", "phone", name="uq_contacts_business_phone"),
    )

    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "contact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("contacts.id", ondelete="SET NULL"),
        ),
        sa.Column("provider_call_id", sa.Text),
        sa.Column(
            "direction",
            sa.Enum("inbound", "outbound", name="call_direction"),
            nullable=False,
            server_default="inbound",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("duration_sec", sa.Integer),
        sa.Column("language", sa.String(16)),
        sa.Column("intent", sa.Text),
        sa.Column("outcome", sa.Text),
        sa.Column("sentiment", sa.Float),
        sa.Column("summary", sa.Text),
        sa.Column("recording_url", sa.Text),
        sa.Column("prompt_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("cost_telephony", sa.Numeric(10, 5), server_default="0"),
        sa.Column("cost_stt", sa.Numeric(10, 5), server_default="0"),
        sa.Column("cost_llm", sa.Numeric(10, 5), server_default="0"),
        sa.Column("cost_tts", sa.Numeric(10, 5), server_default="0"),
        sa.Column("flagged", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("flag_note", sa.Text),
    )

    op.create_table(
        "call_turns",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "call_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("calls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("turn_index", sa.Integer, nullable=False),
        sa.Column(
            "role",
            sa.Enum("caller", "agent", "tool", name="turn_role"),
            nullable=False,
        ),
        sa.Column("text", sa.Text),
        sa.Column("tool_name", sa.Text),
        sa.Column("tool_args", postgresql.JSONB),
        sa.Column("tool_result", postgresql.JSONB),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_call_turns_call_id", "call_turns", ["call_id"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("call_id", postgresql.UUID(as_uuid=True)),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True)),
        sa.Column("caller_name", sa.Text),
        sa.Column("caller_phone", sa.String(32)),
        sa.Column("reason", sa.Text),
        sa.Column(
            "status",
            sa.Enum("new", "in_progress", "done", name="message_status"),
            nullable=False,
            server_default="new",
        ),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True)),
        sa.Column("call_id", postgresql.UUID(as_uuid=True)),
        sa.Column("service", sa.Text, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("booked", "cancelled", "completed", "no_show", name="appointment_status"),
            nullable=False,
            server_default="booked",
        ),
        sa.Column("external_event_id", sa.Text),
        sa.Column(
            "created_by",
            sa.Enum("ai", "staff", name="appointment_creator"),
            nullable=False,
            server_default="ai",
        ),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", postgresql.JSONB, nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "live", "archived", name="prompt_status"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.Text),
    )

    op.create_table(
        "knowledge_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", postgresql.JSONB),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "knowledge_gaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("call_id", postgresql.UUID(as_uuid=True)),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("resolved_item_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("entity", sa.Text, nullable=False),
        sa.Column("entity_id", sa.Text),
        sa.Column("diff", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table in (
        "audit_log",
        "knowledge_gaps",
        "knowledge_items",
        "prompt_versions",
        "appointments",
        "messages",
        "call_turns",
        "calls",
        "contacts",
        "users",
        "businesses",
    ):
        op.drop_table(table)
    for enum in (
        "user_role",
        "call_direction",
        "turn_role",
        "message_status",
        "appointment_status",
        "appointment_creator",
        "prompt_status",
    ):
        op.execute(f"DROP TYPE IF EXISTS {enum}")
    op.execute("DROP EXTENSION IF EXISTS vector")