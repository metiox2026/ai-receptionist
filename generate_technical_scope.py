"""
AI Receptionist — Technical Implementation Scope
Generates a dark-themed, A4 PDF matching the styling of the project's
existing scope documents (SYNCD_Implementation_Plan.pdf, etc.).

Usage:
    python generate_technical_scope.py
Output:
    AI_Receptionist_Technical_Implementation_Scope.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Flowable

import os

# ─── Color Palette (matches existing scope docs) ──────────────────────────────
BG_DARK       = colors.HexColor('#0D0D0F')
ACCENT_PURPLE = colors.HexColor('#7C3AED')
ACCENT_PINK   = colors.HexColor('#EC4899')
ACCENT_CYAN   = colors.HexColor('#06B6D4')
GOLD          = colors.HexColor('#F59E0B')
WHITE         = colors.HexColor('#F8F8FF')
LIGHT_GREY    = colors.HexColor('#C4C4D4')
MID_GREY      = colors.HexColor('#6B7280')
DARK_CARD     = colors.HexColor('#1A1A2E')
CARD_BORDER   = colors.HexColor('#2D2D4E')
GREEN         = colors.HexColor('#10B981')
RED_SOFT      = colors.HexColor('#F87171')

PAGE_W, PAGE_H = A4


# ─── Background Canvas ───────────────────────────────────────────────────────
class DarkBackground(Flowable):
    def __init__(self, w, h):
        Flowable.__init__(self)
        self.w, self.h = w, h

    def draw(self):
        pass


def dark_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG_DARK)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Subtle gradient orbs (top-right purple, bottom-left pink)
    canvas.setFillColorRGB(0.48, 0.23, 0.93, alpha=0.06)
    canvas.circle(PAGE_W * 0.85, PAGE_H * 0.9, 140, fill=1, stroke=0)
    canvas.setFillColorRGB(0.93, 0.28, 0.60, alpha=0.05)
    canvas.circle(PAGE_W * 0.1, PAGE_H * 0.15, 110, fill=1, stroke=0)

    # Footer line
    canvas.setStrokeColor(CARD_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 14 * mm, PAGE_W - 20 * mm, 14 * mm)

    # Page number + project tag
    canvas.setFillColor(MID_GREY)
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(
        PAGE_W / 2, 9 * mm,
        f'Page {doc.page}  ·  AI Receptionist — Technical Implementation Scope  ·  Confidential',
    )
    canvas.restoreState()


def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG_DARK)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Large purple orb top-right
    canvas.setFillColorRGB(0.48, 0.23, 0.93, alpha=0.18)
    canvas.circle(PAGE_W, PAGE_H, 260, fill=1, stroke=0)

    # Pink orb bottom-left
    canvas.setFillColorRGB(0.93, 0.28, 0.60, alpha=0.14)
    canvas.circle(0, 0, 200, fill=1, stroke=0)

    # Cyan accent bottom-right
    canvas.setFillColorRGB(0.024, 0.71, 0.831, alpha=0.10)
    canvas.circle(PAGE_W, 0, 150, fill=1, stroke=0)

    # Horizontal accent bar
    canvas.setFillColor(ACCENT_PURPLE)
    canvas.rect(0, PAGE_H * 0.47, PAGE_W, 2, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_PINK)
    canvas.rect(0, PAGE_H * 0.47 - 2, PAGE_W, 2, fill=1, stroke=0)

    # Project name
    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 64)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H * 0.62, 'AI RECEPTIONIST')

    # Tagline
    canvas.setFillColor(LIGHT_GREY)
    canvas.setFont('Helvetica', 14)
    canvas.drawCentredString(
        PAGE_W / 2, PAGE_H * 0.555,
        'Self-Hosted Voice Agent  ·  Pipecat + FastAPI + Next.js Monorepo',
    )

    # Subtitle card
    canvas.setFillColor(DARK_CARD)
    canvas.roundRect(40 * mm, PAGE_H * 0.36, PAGE_W - 80 * mm, 52, 8, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_CYAN)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H * 0.395, 'TECHNICAL IMPLEMENTATION SCOPE')
    canvas.setFillColor(MID_GREY)
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(
        PAGE_W / 2, PAGE_H * 0.375,
        'Version 1.0  ·  ai-receptionist v0.1.0  ·  2026  ·  Confidential & Proprietary',
    )

    # Stat badges
    stats = [
        ('65 files', 'Scaffold'),
        ('4 services', 'Monorepo'),
        ('~2.5K LOC', 'To Implement'),
        ('6 weeks', 'Build ETA'),
    ]
    bw, bh, gap = 36 * mm, 20 * mm, 6 * mm
    total = len(stats) * bw + (len(stats) - 1) * gap
    sx = (PAGE_W - total) / 2
    sy = PAGE_H * 0.22
    for i, (val, lbl) in enumerate(stats):
        bx = sx + i * (bw + gap)
        canvas.setFillColor(DARK_CARD)
        canvas.roundRect(bx, sy, bw, bh, 6, fill=1, stroke=0)
        canvas.setStrokeColor(ACCENT_PURPLE)
        canvas.setLineWidth(0.8)
        canvas.roundRect(bx, sy, bw, bh, 6, fill=0, stroke=1)
        canvas.setFillColor(ACCENT_PINK)
        canvas.setFont('Helvetica-Bold', 13)
        canvas.drawCentredString(bx + bw / 2, sy + 10, val)
        canvas.setFillColor(MID_GREY)
        canvas.setFont('Helvetica', 7.5)
        canvas.drawCentredString(bx + bw / 2, sy + 3, lbl)

    canvas.restoreState()


# ─── Styles ───────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    def ps(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        'h1': ps('H1', fontSize=22, textColor=WHITE, fontName='Helvetica-Bold',
                 spaceAfter=6, spaceBefore=18, leading=28),
        'h2': ps('H2', fontSize=14, textColor=ACCENT_PURPLE, fontName='Helvetica-Bold',
                 spaceAfter=4, spaceBefore=14, leading=18),
        'h3': ps('H3', fontSize=11, textColor=ACCENT_CYAN, fontName='Helvetica-Bold',
                 spaceAfter=3, spaceBefore=10, leading=14),
        'body': ps('Body', fontSize=9.5, textColor=LIGHT_GREY, fontName='Helvetica',
                   spaceAfter=5, leading=14),
        'bullet': ps('Bullet', fontSize=9, textColor=LIGHT_GREY, fontName='Helvetica',
                     spaceAfter=3, leading=13, leftIndent=12, bulletIndent=0),
        'caption': ps('Caption', fontSize=8, textColor=MID_GREY, fontName='Helvetica',
                      spaceAfter=2, leading=11),
        'tag': ps('Tag', fontSize=8, textColor=ACCENT_CYAN, fontName='Helvetica-Bold',
                  spaceAfter=2, leading=11),
        'section_label': ps('SL', fontSize=8, textColor=ACCENT_PURPLE,
                             fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=2,
                             leading=10),
        'phase': ps('Phase', fontSize=11, textColor=GOLD, fontName='Helvetica-Bold',
                    spaceAfter=3, leading=14),
        'white_bold': ps('WB', fontSize=10, textColor=WHITE, fontName='Helvetica-Bold',
                         spaceAfter=3, leading=13),
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────
S = None  # assigned after make_styles()

def sp(n=6): return Spacer(1, n)

def rule(color=CARD_BORDER, t=0.5):
    return HRFlowable(width='100%', thickness=t, color=color, spaceAfter=6, spaceBefore=6)

def p(text, style='body'): return Paragraph(text, S[style])

def bul(items, icon='▸'):
    return [Paragraph(f'<font color="#7C3AED">{icon}</font>  {i}', S['bullet']) for i in items]

def card_table(rows, col_widths, style_extra=None):
    base_style = [
        ('BACKGROUND', (0, 0), (-1, 0), DARK_CARD),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#111124')),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('TEXTCOLOR', (0, 1), (-1, -1), LIGHT_GREY),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#111124'), colors.HexColor('#0F0F1E')]),
        ('GRID', (0, 0), (-1, -1), 0.4, CARD_BORDER),
        ('ROUNDEDCORNERS', [4]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    if style_extra:
        base_style.extend(style_extra)
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle(base_style))
    return t

def section_header(title, subtitle=''):
    elems = []
    elems.append(sp(4))
    elems.append(HRFlowable(width='100%', thickness=1.5, color=ACCENT_PURPLE,
                             spaceAfter=4, spaceBefore=0))
    elems.append(p(title, 'h1'))
    if subtitle:
        elems.append(p(subtitle, 'caption'))
    elems.append(sp(4))
    return elems

def mini_header(title):
    return [p(title, 'h2'), rule(ACCENT_PURPLE, 0.4)]

def code_block(text, lines=None):
    """Render a mono-ish code/inline text block inside a dark card."""
    return Paragraph(
        f'<font face="Courier" size="8" color="#C4C4D4">{text}</font>',
        ParagraphStyle('Code', fontSize=8, textColor=LIGHT_GREY, fontName='Courier',
                       leftIndent=6, rightIndent=6, leading=12),
    )


# ─── Sections ─────────────────────────────────────────────────────────────────

def executive_summary():
    elems = []
    elems += section_header(
        '01  Executive Summary',
        'Engineering build plan for the AI Receptionist scaffold',
    )

    elems.append(p(
        'The AI Receptionist repository is currently in a Scaffold state — topology, services, '
        'configuration, and skeleton code are in place, but most modules are stubs awaiting '
        'real implementation, API keys, and tuning. This document is the companion to the '
        'Full Scope and exists for engineers: it enumerates every TODO, defines the exact '
        'build order, specifies the API contracts, and prescribes the test strategy that '
        'lets us ship the MVP without regressing prompt behaviour.'
    ))
    elems.append(sp(8))

    rows = [
        ['Dimension', 'Detail'],
        ['Repo', 'C:\\Users\\Admin\\Desktop\\PROJECTS\\NEW\\Receptionist (monorepo, 4 services)'],
        ['Current State', 'Scaffold — topology, config, skeleton code in place; modules stubbed'],
        ['Target', 'Phases 0–3 shippable (24/7 inbound, take-message, booking, dashboard v1)'],
        ['Stack (frozen)', 'Pipecat · FastAPI · Postgres+pgvector · Redis+arq · Next.js 14'],
        ['Build Owner', '1 backend + 1 agent + 1 frontend (3 engineers, ~6 weeks)'],
        ['Definition of Done', 'All Phase-0–3 acceptance criteria in §17 met; baseline eval passes'],
    ]
    elems.append(card_table(rows, [55 * mm, 110 * mm]))
    elems.append(sp(12))

    elems += mini_header('How to read this document')
    elems.append(p(
        'Sections 02–03 set the order of operations. Section 04 is the schema-level truth. '
        'Sections 05–09 define contracts the agent and api must satisfy. Sections 10–13 define '
        'what "tested" means. Sections 14–16 are ops. Section 17 is the exit criteria for each '
        'phase of the Full Scope.'
    ))
    return elems


def build_order():
    elems = []
    elems += section_header(
        '02  Build Order & Dependencies',
        'Module-by-module sequence; parallelisable tracks marked',
    )

    elems.append(p(
        'The build follows the dependency graph of the call lifecycle: nothing useful happens '
        'until a call can ring, transcribe, respond, and persist. We layer in this order; '
        'each track is owned by one engineer and tracked independently.'
    ))
    elems.append(sp(6))

    phases = [
        (1, 'Foundation & Wiring', 'Days 1–4', '#7C3AED', [
            ('Env & secrets', [
                'Fill .env from .env.example — required keys only (POSTGRES_PASSWORD, SECRET_KEY, NEXTAUTH_SECRET, provider keys)',
                'docker compose up — verify all containers healthy',
                'make migrate — confirm pgvector extension loaded',
                'make seed — confirm first business + admin user created',
            ]),
            ('Service contracts', [
                'Freeze api/main.py route surface (no new routes without doc update)',
                'Freeze internal router shape — agent ↔ api only ever writes via /internal/*',
                'Lock idempotency-key header convention (Idempotency-Key: <uuid>) for all mutations',
            ]),
        ]),
        (2, 'Telephony & Pipeline Skeleton', 'Days 5–8', '#06B6D4', [
            ('Telnyx inbound', [
                'api/routers/internal.py + webhook signature verification (Ed25519)',
                'agent/providers/telnyx.py serializer — 8 kHz μ-law frames',
                'agent/pipeline.py — assemble empty Pipecat pipeline; call connects & hangs up cleanly',
            ]),
            ('Cost & turns ledger', [
                'agent/cost.py — running per-turn ticker (LLM tokens, STT seconds, TTS chars)',
                'api/routers/internal.py — POST /internal/call-turns (agent → api persistence)',
                'api/routers/internal.py — POST /internal/calls/{id}/finalize (cost rollup)',
            ]),
        ]),
        (3, 'Conversation Core', 'Days 9–14', '#EC4899', [
            ('STT + LLM + TTS', [
                'Wire Deepgram streaming → Claude Haiku 4.5 → Cartesia Sonic-2',
                'agent/fallbacks.py — primary→Gemini fallback on timeout / 5xx',
                'agent/prompts/builder.py — assemble prompt from prompt_versions row + dynamic suffix',
            ]),
            ('P0 tools', [
                'tools/messages.py (take_message) — server-validated, idempotent',
                'tools/transfer.py (transfer_call) — Telnyx call-control REST call',
                'tools/transfer.py (end_call) — graceful hangup',
            ]),
            ('Latency instrumentation', [
                'Per-turn latency_ms capture at 4 stages (endpoint, STT, LLM-ttfb, TTS-ttfb)',
                'Emit histogram metrics to Prometheus',
            ]),
        ]),
        (4, 'Booking + RAG', 'Days 15–20', '#F59E0B', [
            ('Calendar', [
                'tools/calendar.py — Google Calendar FreeBusy + events.insert',
                'Idempotency key on (caller_phone, slot_start)',
                'Re-check availability at booking time (race protection)',
            ]),
            ('Knowledge base', [
                'tools/knowledge.py — pgvector cosine similarity search',
                'tools/knowledge.py — log_unanswered writes to knowledge_gaps',
                'Seed 20+ FAQs from the prompt-validation corpus',
            ]),
            ('SMS confirmations', [
                'tools/sms.py — template-rendered, server-side only (no raw model strings)',
            ]),
        ]),
        (5, 'Post-call & Notifications', 'Days 21–24', '#7C3AED', [
            ('Post-call job', [
                'api/jobs/post_call.py — load transcript, LLM summary, classify intent + outcome + sentiment',
                'api/jobs/post_call.py — compute final cost from call_turns + telephony minutes',
                'api/jobs/post_call.py — enqueue notifications (email/SMS/Telegram/Slack)',
            ]),
            ('Daily report', [
                'api/jobs/daily_report.py — aggregate calls, costs, escalations; send via configured channels',
            ]),
        ]),
        (6, 'Dashboard v1', 'Days 25–32', '#06B6D4', [
            ('Read paths', [
                '/calls list + /calls/[id] synced audio + transcript view',
                '/messages inbox + status transitions',
                '/appointments list + cancel action',
                '/config prompt-version viewer (read-only)',
            ]),
            ('Write paths', [
                'POST /config/prompt-versions (save draft) + publish action',
                'POST /knowledge (add FAQ) + edit + delete',
                'POST /contacts/{id}/block + unblock',
                'POST /calls/{id}/flag',
            ]),
        ]),
        (7, 'Hardening & Launch', 'Days 33–42', '#EC4899', [
            ('Eval harness', [
                'eval/run_eval.py — full scenario runner with assertions',
                'make eval-baseline — capture Phase-2 behaviour as regression baseline',
            ]),
            ('Observability', [
                'Sentry wiring (api + agent)',
                'Langfuse prompt-eval integration',
                'Prometheus scrape config + Grafana dashboard JSON',
            ]),
            ('Launch readiness', [
                'Caddy TLS auto-renew verified',
                'Backups: nightly pg_dump → S3',
                'Soft launch on after-hours only; promote to full-hours after 1 week stable',
            ]),
        ]),
    ]

    for num, name, window, col_hex, tracks in phases:
        # Phase header bar
        rows_header = [[
            Paragraph(f'<font color="{col_hex}">PHASE {num}</font>', S['section_label']),
            Paragraph(
                f'<b>{name}</b>',
                ParagraphStyle('PT', fontSize=11, textColor=WHITE,
                               fontName='Helvetica-Bold', leading=14),
            ),
            Paragraph(
                window,
                ParagraphStyle('PD', fontSize=9, textColor=GOLD,
                               fontName='Helvetica-Bold', leading=12, alignment=TA_RIGHT),
            ),
        ]]
        col = colors.HexColor(col_hex)
        t = Table(rows_header, colWidths=[40 * mm, 95 * mm, 35 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK_CARD),
            ('GRID', (0, 0), (-1, -1), 0, colors.transparent),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 2, col),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elems.append(sp(8))
        elems.append(t)
        for sub_title, items in tracks:
            elems.append(sp(4))
            elems.append(p(f'▸ {sub_title}', 'h3'))
            elems += bul(items)
        elems.append(sp(6))

    return elems


def stub_checklist():
    elems = []
    elems += section_header(
        '03  Stub-Completion Checklist',
        'Every TODO in the scaffold, mapped to the module that closes it',
    )

    elems.append(p(
        'These are the work items already enumerated in the Full Scope §17, '
        're-keyed here by file path with the closure criteria. Treat each as a single '
        'PR — reviewers should be able to verify the closure criterion without reading '
        'the surrounding module.'
    ))
    elems.append(sp(6))

    rows = [
        ['File', 'What is stubbed', 'Closure criterion'],
        ['agent/pipeline.py', 'Caller lookup + turn persistence hooks',
         'Caller fetched from /internal/contacts/lookup; turns POSTed to /internal/call-turns on every frame'],
        ['agent/tools/transfer.py', 'Real Telnyx call-control call',
         'POST https://api.telnyx.com/v2/calls/{id}/actions/transfer with bearer auth; fallback to take_message on 4xx'],
        ['agent/tools/calendar.py', 'Google Calendar FreeBusy + events.insert',
         'OAuth refresh-token flow wired; FreeBusy cached for 30s; idempotency key on (caller_phone, slot_start)'],
        ['api/jobs/post_call.py', 'Transcript load, summary LLM call, notification enqueue',
         'Persists summary + intent/outcome/sentiment; pushes notifications through configured channels; cost_*** rolled up'],
        ['eval/run_eval.py', 'Scenario execution + assertions',
         'Runs each YAML scenario against the agent with stubbed tools; emits pass/fail per assertion; writes results.json'],
        ['api/routers/internal.py', 'Agent → api write endpoints',
         'POST /internal/call-turns (auth: INTERNAL_TOKEN), POST /internal/calls/{id}/finalize'],
        ['api/worker.py', 'arq worker wiring',
         'Boots arq with RedisSettings; registers post_call, notifications, daily_report cron jobs'],
        ['dashboard/app/config/page.tsx', 'Prompt-version create / publish UI',
         'Form + draft save + version diff + publish button (rollback available)'],
        ['dashboard/app/knowledge/page.tsx', 'Knowledge CRUD',
         'Add FAQ form, edit modal, delete confirmation; embedding generated server-side'],
        ['dashboard/app/contacts/page.tsx', 'Block / unblock action',
         'Confirm modal; mutation invalidates /contacts query'],
        ['dashboard/app/appointments/page.tsx', 'Cancel appointment UI',
         'Cancel mutation + optimistic update; cancelled rows distinct from cancelled'],
        ['dashboard/app/calls/[id]/page.tsx', 'Flag + flag_note UI',
         'Flag toggle + reason input; mutation logged to audit_log'],
        ['dashboard/app/settings/page.tsx', 'Settings forms (channels, retention, users)',
         'Forms per section; saves go through PATCH /settings/*'],
        ['dashboard/app/quality/page.tsx', 'Review queue',
         'List flagged calls + LLM-judge regression results; filters by date + reason'],
    ]
    elems.append(card_table(rows, [50 * mm, 55 * mm, 60 * mm]))
    return elems


def data_model_deltas():
    elems = []
    elems += section_header(
        '04  Data Model — Deltas & Indexes',
        'Schema changes required beyond migration 0001_initial',
    )

    elems += mini_header('Schema additions (migration 0002)')
    rows = [
        ['Table', 'Column / Constraint', 'Why'],
        ['calls', 'partial index on flagged WHERE flagged = true',
         'Dashboard review queue + quality page filter; small index, big win'],
        ['calls', 'composite index (business_id, started_at DESC)',
         'Overview + calls list page are ordered + tenant-scoped'],
        ['messages', 'composite index (status, created_at DESC)',
         'Inbox sort by status + recency'],
        ['appointments', 'composite index (business_id, starts_at)',
         'Day-view in dashboard; booking-window validation query'],
        ['call_turns', 'composite index (call_id, seq)',
         'Transcript replay in /calls/[id] is the hot path'],
        ['knowledge_items', 'HNSW index on embedding vector (cosine, m=16, ef_construction=64)',
         'Sub-50ms similarity search at 10K rows; tune m/ef in Phase 4'],
        ['prompt_versions', 'partial unique index WHERE status = live',
         'Enforce exactly one live prompt per business at the DB level'],
        ['audit_log', 'composite index (business_id, created_at DESC)',
         'Settings → audit view is always tenant-scoped + newest-first'],
        ['contacts', 'partial index WHERE blocked = true',
         'Caller lookup short-circuits blocked contacts in O(1)'],
    ]
    elems.append(card_table(rows, [38 * mm, 65 * mm, 62 * mm]))
    elems.append(sp(10))

    elems += mini_header('Field-level notes')
    elems += bul([
        'calls.cost_telephony / cost_stt / cost_llm / cost_tts are Numeric(10,5) — never float; sums computed in DB.',
        'call_turns.tool_args / tool_result are JSONB; validate against tool schema on insert (defense vs prompt injection).',
        'prompt_versions.blob JSONB keys: persona, style, business_facts, policies, actions, rules, escalation — exactly these seven, no more.',
        'knowledge_items.embedding is vector(768) — locked to the OpenAI text-embedding-3-small dimension in Phase 2 (do not swap mid-flight).',
        'appointments.external_event_id carries the Calendar event ID; nullable until Phase 3 sync is on.',
        'users has bcrypt hash + jose-signed HS256 JWT only — no OAuth until 2FA lands in Phase 4.',
    ])

    elems.append(sp(8))
    elems += mini_header('Retention policy implementation')
    rows = [
        ['Table', 'Default', 'Configurable via', 'Job'],
        ['calls, call_turns', 'Indefinite', 'settings.retention_days_calls',
         'cron: DELETE WHERE started_at < now() - retention'],
        ['recordings (object storage)', '30 days', 'settings.retention_days_recordings',
         'cron: list + delete orphan keys in RECORDINGS_BUCKET'],
        ['audit_log', 'Indefinite', '—',
         '— (regulatory: keep all config changes forever)'],
    ]
    elems.append(card_table(rows, [42 * mm, 28 * mm, 42 * mm, 53 * mm]))
    return elems


def api_contracts():
    elems = []
    elems += section_header(
        '05  API Contracts',
        'All HTTP endpoints; auth model; idempotency; pagination; errors',
    )

    elems += mini_header('Authentication')
    elems += bul([
        'Dashboard → api: Bearer HS256 JWT (jose), 15-min access + 7-day refresh cookie (HttpOnly, Secure, SameSite=Lax).',
        'Agent → api (internal): static X-Internal-Token header; token only valid on the docker network — Caddy refuses to forward /internal/* externally.',
        'Telnyx → api/webhooks: Ed25519 signature verified against TELNYX_PUBLIC_KEY over the raw request bytes.',
        'Tool server-side validation: every value the LLM emits is re-validated server-side (zod) before reaching a provider.',
    ])
    elems.append(sp(6))

    elems += mini_header('Dashboard API surface')
    rows = [
        ['Method', 'Path', 'Auth', 'Notes'],
        ['POST', '/auth/login', 'none', 'bcrypt verify → JWT pair; sets refresh cookie'],
        ['POST', '/auth/refresh', 'refresh cookie', 'Rotates access token; refresh cookie unchanged'],
        ['GET',  '/calls', 'JWT', 'Query: from, to, flagged, intent; paginated cursor'],
        ['GET',  '/calls/{id}', 'JWT', 'Includes turn list + recording_url + cost breakdown'],
        ['POST', '/calls/{id}/flag', 'JWT', 'Body: { flag_note } — writes audit_log'],
        ['GET',  '/messages', 'JWT', 'Filter by status; cursor pagination'],
        ['PATCH','/messages/{id}', 'JWT', 'Status: in_progress / done'],
        ['GET',  '/appointments', 'JWT', 'Filter by date range + status'],
        ['PATCH','/appointments/{id}', 'JWT', 'cancel → also cancels Calendar event'],
        ['GET',  '/contacts', 'JWT', 'Filter: blocked, tag'],
        ['POST', '/contacts/{id}/block', 'JWT', 'Idempotent; logs to audit_log'],
        ['GET',  '/config/prompt-versions', 'JWT', 'List all versions + status'],
        ['POST', '/config/prompt-versions', 'JWT', 'Create draft; status=draft'],
        ['POST', '/config/prompt-versions/{id}/publish', 'JWT',
         'Sets to live; archives previous live row (DB partial unique enforces 1)'],
        ['GET',  '/knowledge', 'JWT', 'List FAQ items'],
        ['POST', '/knowledge', 'JWT', 'Body: question, answer → server embeds & stores'],
        ['DELETE','/knowledge/{id}', 'JWT', 'Soft-delete (status=archived)'],
    ]
    elems.append(card_table(rows, [14 * mm, 50 * mm, 18 * mm, 83 * mm]))
    elems.append(sp(10))

    elems += mini_header('Internal router (agent → api)')
    rows = [
        ['Method', 'Path', 'Body', 'Notes'],
        ['POST', '/internal/contacts/lookup',
         '{ phone_e164 }',
         'Returns { contact_id, blocked, last_call_at, tags }; short-circuits if blocked'],
        ['POST', '/internal/calls',
         '{ call_sid, from, to, business_id }',
         'Idempotent on call_sid — UPSERT returns existing id on conflict'],
        ['POST', '/internal/call-turns',
         '{ call_id, role, text?, tool_name?, tool_args?, tool_result?, latency_ms, cost_*, seq }',
         'Append-only; seq gap > 1 returns 409 (drift detection)'],
        ['POST', '/internal/calls/{id}/finalize',
         '{ ended_at, duration_sec }',
         'Triggers post_call job enqueue; returns enqueue receipt id'],
        ['GET',  '/internal/calls/{id}/prompt',
         '—',
         'Returns current live prompt blob + dynamic suffix (caller, time)'],
        ['GET',  '/internal/knowledge/search',
         '?q=&k=',
         'Returns top-k snippets with similarity scores (pgvector cosine)'],
        ['POST', '/internal/knowledge/gaps',
         '{ call_id, question }',
         'Writes knowledge_gaps row'],
        ['POST', '/internal/messages',
         '{ call_id?, caller_phone, name?, reason, callback_window? }',
         'Idempotent on (caller_phone, reason, open_window)'],
    ]
    elems.append(card_table(rows, [14 * mm, 50 * mm, 55 * mm, 46 * mm]))
    elems.append(sp(10))

    elems += mini_header('Error model')
    rows = [
        ['Status', 'When', 'Body shape'],
        ['400', 'zod validation failure on body', '{ error: "validation", issues: [{path, message}] }'],
        ['401', 'Missing or invalid JWT / Telnyx sig / internal token', '{ error: "unauthorized" }'],
        ['403', 'JWT valid but business_id mismatch', '{ error: "forbidden" }'],
        ['404', 'Resource not found within tenant scope', '{ error: "not_found" }'],
        ['409', 'Idempotency conflict (same key, different body)', '{ error: "idempotency_conflict" }'],
        ['422', 'Provider rejected (Calendar slot taken, Telnyx 4xx)', '{ error: "provider", provider: "...", code: "..." }'],
        ['429', 'Per-tenant or per-number rate limit', '{ error: "rate_limited", retry_after_ms }'],
        ['500', 'Unexpected — logged with trace_id', '{ error: "internal", trace_id }'],
    ]
    elems.append(card_table(rows, [16 * mm, 56 * mm, 93 * mm]))
    return elems


def agent_pipeline_spec():
    elems = []
    elems += section_header(
        '06  Agent Pipeline — Frame Flow & Persistence',
        'Pipecat pipeline assembly, frame instrumentation, persistence hooks',
    )

    elems.append(p(
        'The agent pipeline is a serial Pipecat pipeline with three side effects per turn: '
        'latency capture, cost accrual, and persistence. Below is the frame flow for one '
        'caller turn → agent response cycle.'
    ))
    elems.append(sp(6))

    flow_rows = [
        ['Stage', 'Service', 'Frame out', 'Side effect'],
        ['1', 'Telnyx transport', 'AudioFrame (8 kHz μ-law)',
         '—'],
        ['2', 'Silero VAD (Pipecat turn detector)',
         'UserStartedSpeakingFrame / UserStoppedSpeakingFrame',
         'Start endpointing latency timer (T0)'],
        ['3', 'Deepgram STT (streaming)',
         'TranscriptionFrame (partials + final)',
         'On final: stop STT timer → T_stt = T1-T0'],
        ['4', 'Context service',
         'MessagesFrame (system + history + new turn)',
         'Resolve live prompt blob via /internal/calls/{id}/prompt'],
        ['5', 'Claude Haiku 4.5 (with_fallback → Gemini 2.5 Flash-Lite)',
         'LLMTextFrame + ToolUseFrame',
         'Stop LLM-ttfb timer → T_llm = T2-T1; accumulate TUsd tokens'],
        ['6', 'Tool runner (one or more in sequence)',
         'ToolResultFrame',
         'For each tool: 2-3s timeout; POST /internal/* on message/transfer/calendar/etc.'],
        ['7', 'Cartesia Sonic-2 TTS',
         'TTSAudioFrame',
         'Stop TTS-ttfb timer → T_tts = T3-T2; accumulate char count'],
        ['8', 'Telnyx transport (egress)',
         'AudioFrame',
         '—'],
        ['9', 'Turn persistence',
         'POST /internal/call-turns (x1 per role + xN per tool)',
         'Atomic per call; seq monotonic'],
    ]
    elems.append(card_table(flow_rows, [14 * mm, 35 * mm, 50 * mm, 66 * mm]))
    elems.append(sp(10))

    elems += mini_header('Latency budget enforcement')
    elems += bul([
        'Per-turn total budget: 800 ms (T_stt + T_llm + T_tts).',
        'Hard timeout per LLM call: 4 s — past that, with_fallback flips to Gemini.',
        'Tool timeout: 2 s read-only (calendar, knowledge), 3 s write (booking, transfer).',
        'If total exceeds 5 s end-to-end → emit metric voice_agent_turn_overrun_total{stage="total"}.',
        'Dashboard analytics page renders p50 / p95 of T_stt, T_llm, T_tts (Prometheus histograms).',
    ])
    elems.append(sp(6))

    elems += mini_header('Persistence hook placement')
    elems += bul([
        'On call_started → POST /internal/calls (idempotent on call_sid).',
        'On every LLM TextFrame → POST /internal/call-turns (role=agent).',
        'On every STT final → POST /internal/call-turns (role=caller).',
        'On every ToolUseFrame / ToolResultFrame → POST /internal/call-turns (role=tool, tool_args + tool_result JSONB).',
        'On call_ended → POST /internal/calls/{id}/finalize → enqueue post_call job.',
        'Per-turn persistence is async — buffered, flushed every 250 ms or 20 rows, whichever.',
    ])
    return elems


def tool_specs():
    elems = []
    elems += section_header(
        '07  Tool Implementation Specs',
        'Per-tool contract, server-side validation, idempotency, timeouts',
    )

    elems.append(p(
        'Every tool validates its arguments server-side (the model is untrusted). '
        'Idempotency keys are required on every mutation. Timeouts are short. '
        'Below is the canonical shape; each tools/*.py file implements exactly one row.'
    ))
    elems.append(sp(6))

    tools = [
        ('take_message', 'P0', 'read+write', [
            'Args (zod): { name: string max 80, phone: string E.164, reason: string max 500, callback_window?: enum[today, evening, tomorrow, anytime] }',
            'Server-side: phone normalised to E.164; reason length checked; existing open message for same (phone, reason) → 200 with existing id (idempotent).',
            'Side effect: POST /internal/messages; notify configured channels (email default).',
            'Timeout: 2 s; on 5xx → model instructed to retry once then end_call.',
        ]),
        ('transfer_call', 'P0', 'write', [
            'Args (zod): { department: enum[sales, support, billing, manager] }',
            'Server: POST https://api.telnyx.com/v2/calls/{call_control_id}/actions/transfer with target number from settings.transfer_numbers[department].',
            'On Telnyx 4xx (no answer, busy) → fall back to take_message; model told to apologise and capture offer.',
            'Timeout: 3 s; logged to audit_log on success.',
        ]),
        ('end_call', 'P0', 'write', [
            'Args (zod): { reason: enum[completed, transferred, failed, timeout] }',
            'Server: POST https://api.telnyx.com/v2/calls/{id}/actions/hangup.',
            'No body to model — required by end-of-turn logic.',
            'Triggers /internal/calls/{id}/finalize.',
        ]),
        ('check_availability', 'P1', 'read', [
            'Args (zod): { date: ISO date, service?: string, tz?: IANA }',
            'Server: Google Calendar FreeBusy on settings.default_calendar_id; 30s Redis cache.',
            'Returns: array of { starts_at, ends_at } open slots, max 10.',
            'Timeout: 2 s.',
        ]),
        ('book_appointment', 'P1', 'write', [
            'Args (zod): { starts_at: ISO datetime, service: string, name, phone, notes? }',
            'Idempotency key: hash(caller_phone + starts_at + service). Re-running with same key returns existing booking.',
            'Race protection: re-check availability at booking time before events.insert.',
            'Server: events.insert on default calendar → store external_event_id; status=booked.',
            'Timeout: 3 s; on conflict (slot taken) → return 422 with alternative slots.',
        ]),
        ('send_sms', 'P1', 'write', [
            'Args (zod): { template: enum[booking_link, scan_intro, callback_promised], variables: object }',
            'Server: looks up template body from settings.sms_templates[template]; renders variables server-side; POST Telnyx messaging.',
            'Model never produces raw SMS body — defeats prompt injection for outbound messages.',
            'Timeout: 2 s; logs sender + recipient + template_id to audit_log.',
        ]),
        ('search_knowledge', 'P1', 'read', [
            'Args (zod): { question: string max 200, k?: int default 3 }',
            'Server: embed via text-embedding-3-small; pgvector cosine similarity search; return top-k with score.',
            'Threshold: drop results below 0.72 similarity.',
            'Timeout: 1.5 s.',
        ]),
        ('log_unanswered', 'P1', 'write', [
            'Args (zod): { question: string max 200 }',
            'Server: POST /internal/knowledge/gaps — staff resolves later by adding an FAQ.',
            'No model-visible side effect; never blocks the turn.',
        ]),
    ]

    for name, prio, kind_type, items_list in tools:
        title_row = [[
            Paragraph(
                f'<b>{name}</b>',
                ParagraphStyle('T', fontSize=10.5, textColor=WHITE,
                               fontName='Helvetica-Bold', leading=14),
            ),
            Paragraph(
                f'{prio} • {kind_type}',
                ParagraphStyle('P', fontSize=8, textColor=ACCENT_CYAN,
                               fontName='Helvetica-Bold', leading=12, alignment=TA_RIGHT),
            ),
        ]]
        col = GREEN if prio == 'P0' else ACCENT_CYAN
        t = Table(title_row, colWidths=[125 * mm, 40 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK_CARD),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LINEBELOW', (0, 0), (-1, -1), 2, col),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elems.append(sp(6))
        elems.append(t)
        item_table_rows = [[
            Paragraph(
                f'<font color="#7C3AED">◆</font>  {it}',
                ParagraphStyle('I', fontSize=8.5, textColor=LIGHT_GREY,
                               fontName='Helvetica', leading=12),
            ),
        ] for it in items_list]
        it = Table(item_table_rows, colWidths=[165 * mm])
        it.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#0F0F1E')),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#0F0F1E'), colors.HexColor('#111124')]),
        ]))
        elems.append(it)
    return elems


def webhook_verification():
    elems = []
    elems += section_header(
        '08  Webhook Verification',
        'Telnyx Ed25519 signature flow on raw request bytes',
    )

    elems += mini_header('Flow')
    elems += bul([
        'Telnyx POSTs to /webhooks/telnyx with header telnyx-signature-ed25519: <base64>',
        'The signature is over the raw request body — must be captured before any JSON parsing.',
        'Verification: pynacl / nacl.signing.VerifyKey(TELNYX_PUBLIC_KEY).verify(body, signature_b64).',
        'On success → enqueue internal action (open media stream, hangup, etc.).',
        'On failure → HTTP 401 + log with trace_id; emit metric webhook_signature_fail_total.',
        'Replay protection: enforce timestamp window (default 5 min) — reject signatures with timestamp older than now-5min.',
    ])
    elems.append(sp(8))

    elems += mini_header('Implementation notes')
    elems += bul([
        'Use FastAPI dependency get_raw_body(request: Request) that returns await request.body() — this must be the first byte buffer read.',
        'Verify BEFORE pydantic validation — never let invalid bodies advance into the queue.',
        'Caddy must NOT buffer the body for /webhooks/telnyx — set flush_interval -1 or use request_body buffer 0.',
        'In test: provide a fixture that signs with the test private key (TELNYX_PUBLIC_KEY overridden in conftest.py).',
    ])
    return elems


def cost_tracker():
    elems = []
    elems += section_header(
        '09  Cost Tracker — Per-Turn Attribution',
        'agent/cost.py algorithm; rounding rules; persistence shape',
    )

    elems += mini_header('Pricing table (loaded from settings, mutable per business)')
    rows = [
        ['Component', 'Unit', 'Default USD/unit', 'Source'],
        ['Telephony (Telnyx inbound)', 'minute', '0.0085',
         'settings.cost_telephony_per_min'],
        ['STT (Deepgram Nova-3)', 'second', '0.0000717',
         'settings.cost_stt_per_sec — ~$0.0043/min'],
        ['TTS (Cartesia Sonic-2)', 'character', '0.000015',
         'settings.cost_tts_per_char — ~$0.015/min spoken'],
        ['LLM primary (Haiku 4.5)', '1K tokens',
         'input 0.001 / output 0.005',
         'settings.cost_llm_in_per_1k + cost_llm_out_per_1k'],
        ['LLM fallback (Gemini 2.5 Flash-Lite)', '1K tokens',
         'input 0.000075 / output 0.0003',
         'settings.cost_llm_fallback_in_per_1k + cost_llm_fallback_out_per_1k'],
    ]
    elems.append(card_table(rows, [50 * mm, 22 * mm, 40 * mm, 53 * mm]))
    elems.append(sp(10))

    elems += mini_header('Per-turn computation')
    elems.append(p(
        'Each turn records usage at the moment of occurrence. The CostTracker '
        'instance is keyed by call_id and held in the per-call context; on '
        'turn end the running totals are POSTed to /internal/call-turns alongside '
        'the turn row.'
    ))
    elems.append(sp(4))

    pseudo = (
        "class CostTracker:<br/>"
        "▌ def on_stt_final(self, audio_secs): self.cost_stt += audio_secs * STT_PER_SEC<br/>"
        "▌ def on_llm_response(self, in_tok, out_tok, fallback=False): self.cost_llm += in_tok * IN_PER_1K/1000 + out_tok * OUT_PER_1K/1000<br/>"
        "▌ def on_tts_audio(self, chars): self.cost_tts += chars * TTS_PER_CHAR<br/>"
        "▌ def on_call_end(self, duration_sec): self.cost_telephony += (duration_sec/60) * TEL_PER_MIN<br/>"
        "▌ def snapshot(self) -> CallCost: round(Numeric, 5 places) per field<br/>"
        "▌ def flush(self): POST /internal/call-turns x N rows (one per usage event)"
    )
    elems.append(Paragraph(
        f'<font face="Courier" size="8" color="#C4C4D4">{pseudo}</font>',
        ParagraphStyle('Pseudo', fontSize=8, textColor=LIGHT_GREY, fontName='Courier',
                       leftIndent=10, rightIndent=10, leading=13,
                       backColor=colors.HexColor('#0F0F1E'),
                       borderColor=CARD_BORDER, borderWidth=0.5, borderPadding=8),
    ))
    elems.append(sp(8))

    elems += mini_header('On-call finalize')
    elems += bul([
        'On call_ended → POST /internal/calls/{id}/finalize → api computes final cost_telephony from duration_sec, sums cost_*** from call_turns rows.',
        'Numeric(10,5) stored — sum computed in DB (never in Python) to avoid float drift.',
        'Dashboard cost-per-call metric = SUM(cost_*) / COUNT(calls) over date range.',
    ])
    return elems


def post_call_job():
    elems = []
    elems += section_header(
        '10  Post-Call Job Specification',
        'api/jobs/post_call.py — summary, classification, notification dispatch',
    )

    elems += mini_header('Job trigger')
    elems += bul([
        'Trigger: POST /internal/calls/{id}/finalize → api/jobs/post_call.py enqueued via arq.',
        'Retries: 3 attempts with exponential backoff (1s, 4s, 16s); on give-up → alert + dead-letter queue.',
        'Idempotent: re-running with same call_id re-uses existing summary (UPSERT pattern).',
    ])
    elems.append(sp(8))

    elems += mini_header('Job steps')
    rows = [
        ['#', 'Step', 'Source / API', 'Timeout'],
        ['1', 'Load call_turns ordered by seq',
         'DB query (indexed on (call_id, seq))', '500 ms'],
        ['2', 'Render transcript (caller + agent text frames only)',
         'in-memory', '100 ms'],
        ['3', 'LLM summary call — 2-3 sentences',
         'Claude Haiku 4.5, max_tokens=120, temp=0.2', '4 s'],
        ['4', 'Classify intent (enum) + outcome (enum) + sentiment (enum)',
         'Claude Haiku 4.5 structured output (JSON schema)', '4 s'],
        ['5', 'Compute telephony cost from duration_sec',
         'duration_sec * cost_telephony_per_min', '—'],
        ['6', 'Sum STT/LLM/TTS costs from call_turns rows',
         'SQL aggregate (avoid Python sum on floats)', '100 ms'],
        ['7', 'UPSERT calls row (summary, intent, outcome, sentiment, cost_*)',
         'INSERT … ON CONFLICT (id) DO UPDATE', '200 ms'],
        ['8', 'Upload recording (if Telnyc recording enabled)',
         'S3-compatible PUT to RECORDINGS_BUCKET', '5 s'],
        ['9', 'Enqueue notifications',
         'arq job notifications.notify_call_completed', '—'],
    ]
    elems.append(card_table(rows, [10 * mm, 60 * mm, 65 * mm, 30 * mm]))
    elems.append(sp(10))

    elems += mini_header('Notification dispatch (api/jobs/notifications.py)')
    elems += bul([
        'Always: email to business owner (SMTP / Resend / SendGrid — first configured wins).',
        'Optional: Telegram, Slack webhook — fired in parallel; one failure does not block the others.',
        'Payload: call summary, recording URL, transcript link, callback info if take_message triggered.',
        'Rate limit: max 5 notifications per call (deduplicates by template + call_id).',
        'Quiet hours: respect business settings.quiet_hours — defer non-urgent pings (e.g. Telegram) outside the window.',
    ])
    return elems


def prompt_caching():
    elems = []
    elems += section_header(
        '11  Prompt Caching Strategy',
        'Section boundaries, cache hit expectations, iteration workflow',
    )

    elems += mini_header('Static prefix (cacheable across calls — same business_id)')
    rows = [
        ['Position', 'Section', 'Tokens', 'Cache key'],
        ['1', 'persona',
         '~30', 'business_id + version_id'],
        ['2', 'style',
         '~150', 'business_id + version_id'],
        ['3', 'business_facts',
         '300–1000', 'business_id + version_id'],
        ['4', 'policies',
         '~200', 'business_id + version_id'],
        ['5', 'actions',
         '~150', 'business_id + version_id'],
        ['6', 'rules',
         '~150', 'business_id + version_id'],
        ['7', 'escalation',
         '~100', 'business_id + version_id'],
        ['subtotal', 'Static prefix',
         '~1,100–1,800 tokens', 'Anthropic cache (TTL 5 min, refreshed per call)'],
    ]
    elems.append(card_table(rows, [30 * mm, 40 * mm, 35 * mm, 60 * mm]))
    elems.append(sp(10))

    elems += mini_header('Dynamic suffix (per call)')
    elems += bul([
        'now() formatted in business tz',
        'caller_phone (last 4 only — never full)',
        'caller history: tags, last_call_at, total_calls (no transcript text)',
        'open message count, next appointment time',
        'system reminder: "today is {weekday}, business hours {open}–{close}; if outside hours, say so first"',
        'Section ordering is fixed — never insert dynamic content above the rules section (would break cache).',
    ])
    elems.append(sp(8))

    elems += mini_header('Iteration discipline')
    elems += bul([
        'Edit in dashboard → Save as draft → status=draft; live row untouched.',
        'Run make eval against draft (--prompt-version=ID).',
        'When metrics ≥ baseline → Publish; previous live row → archived (partial unique index ensures ≤1 live).',
        'Roll back by re-publishing an archived version.',
        'Never hot-edit the live prompt — always through version → publish flow.',
        'cache_control markers placed exactly at the start of the static prefix and after section 7 — Claude caches from marker to marker.',
    ])
    return elems


def eval_harness():
    elems = []
    elems += section_header(
        '12  Eval Harness Implementation',
        'eval/run_eval.py execution model, assertions, baseline regression',
    )

    elems += mini_header('Execution model')
    elems += bul([
        'eval/run_eval.py runs each YAML scenario against agent service with --suite eval/scenarios.',
        'Tools are stubbed (mock implementations injected via fixture); only LLM is real.',
        'For each caller turn → capture agent response + any tool calls → apply expectations → mark pass/fail.',
        'No audio — text-mode only (keeps eval fast and CI-cheap).',
        'Output: results.json — per scenario { pass, fail, assertions: [{name, passed, expected, actual}] }.',
    ])
    elems.append(sp(8))

    elems += mini_header('Expectation schema')
    pseudo = (
        "turns:<br/>"
        "▌ - role: caller<br/>"
        "▌   text: \"I'd like to book a haircut tomorrow at 2pm.\"<br/>"
        "▌   expect:<br/>"
        "▌     - agent_uses_tool: check_availability<br/>"
        "▌     - agent_eventually_uses_tool: book_appointment<br/>"
        "▌     - agent_response_length_max_words: 25<br/>"
        "▌     - agent_offer_take_message: false<br/>"
        "<br/>"
        "metrics:<br/>"
        "▌ - tool_call_accuracy  # fraction of turns where expected tool fires<br/>"
        "▌ - brevity             # p50 turn word count<br/>"
        "▌ - no_hallucinated_facts  # all facts trace to knowledge_items or business_facts"
    )
    elems.append(Paragraph(
        f'<font face="Courier" size="8" color="#C4C4D4">{pseudo}</font>',
        ParagraphStyle('YAML', fontSize=8, textColor=LIGHT_GREY, fontName='Courier',
                       leftIndent=10, rightIndent=10, leading=13,
                       backColor=colors.HexColor('#0F0F1E'),
                       borderColor=CARD_BORDER, borderWidth=0.5, borderPadding=8),
    ))
    elems.append(sp(10))

    elems += mini_header('Baseline & regression')
    elems += bul([
        'make eval-baseline — runs eval, writes results.json → eval/baselines/<sha>.json.',
        'CI on PR: run eval, compare to baseline; fail if tool_call_accuracy regresses > 5% or brevity p50 > 30 words.',
        'Phase 4: wire to Langfuse — track per-scenario traces + judge model for open-ended assertions.',
        'TODO: prompt-injection scenarios, language-switch scenarios.',
    ])
    return elems


def test_strategy():
    elems = []
    elems += section_header(
        '13  Test Strategy',
        'Unit / integration / e2e / load matrix; what to mock; coverage targets',
    )

    elems += mini_header('Test pyramid')
    rows = [
        ['Layer', 'Tool', 'What it covers', 'Coverage target'],
        ['Unit', 'pytest', 'pure logic: cost math, idempotency, validation, prompt assembly',
         '80% of api + agent modules'],
        ['Integration', 'pytest + testcontainers',
         'api ↔ Postgres (pgvector) ↔ Redis; tool calls against recorded provider responses',
         'all routers, all tools'],
        ['Contract', 'schemathesis (or hand-rolled)',
         'OpenAPI schema validates every endpoint; 4xx/5xx response shapes',
         'every endpoint, every documented error code'],
        ['Eval', 'pytest + YAML scenarios',
         'prompt behaviour regression (see §12)',
         'all 6 baseline scenarios + 2 prompt-injection'],
        ['e2e', 'docker compose up + synthetic Telnyx webhook',
         'call ring → answer → tool → hangup → post_call job → dashboard row',
         '1 happy path + 1 escalation + 1 booking'],
        ['Load', 'k6 (post-Phase-2)',
         '20 concurrent calls sustained for 10 min; p95 turn latency',
         'sized for Phase-2 capacity numbers'],
    ]
    elems.append(card_table(rows, [22 * mm, 38 * mm, 65 * mm, 40 * mm]))
    elems.append(sp(10))

    elems += mini_header('Mocking rules')
    elems += bul([
        'Always mock: Telnyx, Deepgram, Cartesia, Anthropic, Google Calendar, Gmail/SMTP.',
        'Never mock: Postgres, Redis (use testcontainers).',
        'For Pipecat pipeline tests — mock the transport services but run the real frame processor chain.',
        'LLM mock: a deterministic stub that returns canned tool calls + text for fixtures.',
        'Webhook signature tests: sign with a test private key in conftest; do not disable signature verification.',
    ])
    elems.append(sp(8))

    elems += mini_header('Critical tests (must exist before merge)')
    rows = [
        ['Test', 'Why critical'],
        ['test_idempotency_messages.py — same (phone, reason, window) twice → same row',
         'Prevents double-notifying staff'],
        ['test_calendar_race.py — slot freed then re-booked within 200ms',
         'Catches missing re-check at booking time'],
        ['test_webhook_signature.py — unsigned/old/wrong-key all return 401',
         'Security gate'],
        ['test_prompt_caching.py — same prompt_version_id twice → cache_read_tokens > 0',
         'Confirms Anthropic caching actually engaged'],
        ['test_cost_rollup.py — sum across 10 turns matches snapshot by hand',
         'Catches float drift in cost tracker'],
        ['test_call_duration_cap.py — calls > MAX_CALL_DURATION_SEC end gracefully',
         'Cost control — defends against runaway LLM loops'],
    ]
    elems.append(card_table(rows, [55 * mm, 110 * mm]))
    return elems


def observability():
    elems = []
    elems += section_header(
        '14  Observability Wiring',
        'Metric names, structured log keys, trace spans, dashboards',
    )

    elems += mini_header('Prometheus metrics (api + agent)')
    rows = [
        ['Metric', 'Type', 'Labels', 'Used by'],
        ['voice_agent_turn_latency_seconds', 'histogram',
         'stage=endpoint|stt|llm|tts|total', 'p50/p95 latency dashboard'],
        ['voice_agent_turn_overrun_total', 'counter',
         'stage', 'alert: overrun rate > 10% sustained 10 min'],
        ['voice_agent_cost_dollars_total', 'counter',
         'component=telephony|stt|llm|tts, business_id',
         'cost-per-call dashboard'],
        ['voice_agent_tool_calls_total', 'counter',
         'tool, result=success|fail|timeout',
         'tool reliability + per-tool latency'],
        ['api_http_requests_total', 'counter',
         'method, path, status', 'request rate + error rate'],
        ['api_http_request_duration_seconds', 'histogram',
         'method, path', 'api p95 latency'],
        ['api_jobs_processed_total', 'counter',
         'job=post_call|notifications|daily_report, result',
         'job queue health'],
        ['webhook_signature_fail_total', 'counter', '—',
         'security alert: > 0 sustained'],
        ['llm_fallback_engaged_total', 'counter', 'from=primary|fallback',
         'alert: > 5% of turns means primary provider degraded'],
    ]
    elems.append(card_table(rows, [55 * mm, 24 * mm, 50 * mm, 36 * mm]))
    elems.append(sp(10))

    elems += mini_header('Structured log keys (structlog)')
    rows = [
        ['Key', 'Type', 'Example'],
        ['call_id', 'uuid', '8b3e... (every log line within a call shares this)'],
        ['business_id', 'uuid', 'tenant scope'],
        ['caller_phone_hash', 'sha256(last 4)', 'phone_e164 — never full ring'],
        ['turn_seq', 'int', 'monotonic per call'],
        ['latency_ms', 'object',
         '{ endpoint, stt, llm, tts, total }'],
        ['tool_name', 'string|null', 'check_availability / book_appointment / …'],
        ['tool_result', 'enum', 'success | validation_error | timeout | provider_error'],
        ['cost_usd', 'object',
         '{ telephony, stt, llm, tts }'],
        ['prompt_version_id', 'uuid', 'correlation behaviour ↔ prompt change'],
    ]
    elems.append(card_table(rows, [42 * mm, 22 * mm, 101 * mm]))
    elems.append(sp(10))

    elems += mini_header('Trace spans (api → agent → providers)')
    elems += bul([
        'api.receive.webhook  →  agent.call.connect  →  agent.turn.{stt,llm,tool,tts}  →  agent.call.end',
        'api.jobs.post_call — children: api.post_call.summary, api.post_call.classify, api.post_call.notify',
        'Tool spans — one per tool call, includes tool_name, duration, status',
        'Export to Sentry; for Phase 4 wire to OpenTelemetry collector + Langfuse for LLM traces.',
    ])
    return elems


def deploy_pipeline():
    elems = []
    elems += section_header(
        '15  Build & Deploy Pipeline',
        'Image build order, migration runbook, rollback procedure',
    )

    elems += mini_header('Image build')
    rows = [
        ['Service', 'Base image', 'Build context', 'Cache hint'],
        ['api', 'python:3.11-slim',
         'pyproject.toml + api/** + shared/**', 'uv sync --frozen --all-groups as cache key'],
        ['agent', 'python:3.11-slim',
         'pyproject.toml + agent/** + shared/**', 'share uv cache layer with api'],
        ['worker', 'python:3.11-slim',
         'pyproject.toml + api/**', 'same base as api — same Dockerfile, different CMD'],
        ['dashboard', 'node:20-alpine',
         'dashboard/**', 'npm ci with package-lock.json cached'],
    ]
    elems.append(card_table(rows, [25 * mm, 35 * mm, 45 * mm, 60 * mm]))
    elems.append(sp(10))

    elems += mini_header('Migration runbook')
    elems += bul([
        'make migrate — runs Alembic upgrade head inside the api container.',
        'make migrate-new m="..." — generates new revision; review for downgrade.',
        'Backward-compat rules: never drop a column in the same release that removes the reader; two-release deprecation.',
        'Before deploy: docker compose run --rm api alembic current  →  capture for /persist',
        'On failed migration: docker compose run --rm api alembic downgrade -1; investigate; do not force.',
        'Long migrations (>30s on prod data): pre-deploy script that runs against a shadow table first.',
    ])
    elems.append(sp(8))

    elems += mini_header('Rollback procedure')
    elems += bul([
        'git pull && git checkout <last-good-sha>',
        'docker compose build && docker compose up -d',
        'On schema incompatibility: alembic downgrade -1 (only safe for additive migrations).',
        'Call forwarding fallback: Telnyx fallback number auto-routes to a human line if api health probe is down.',
        'Active calls during deploy: agent drains gracefully (signal handler — finishes current turn, then closes).',
        'Roll-forward preferred over roll-back once data has been written by the new code.',
    ])
    return elems


def risks():
    elems = []
    elems += section_header(
        '16  Open Implementation Risks',
        'Provider behaviour, capacity assumptions, race conditions, TBDs',
    )

    rows = [
        ['Risk', 'Likelihood', 'Impact', 'Mitigation'],
        ['Pipecat version churn — API breaks between minor versions',
         'Medium', 'High',
         'Pin Pipecat to a known-good minor; review changelog; integration test before upgrade'],
        ['Telnyx call-control latency spike (> 800 ms)',
         'Low', 'High',
         'Pre-warm connection; fallback to take_message on timeout; alert on p95 > 1.2s'],
        ['Deepgram partials misaligned with turn detector',
         'Medium', 'Medium',
         'Always use Silero VAD — never silence-energy threshold; test with non-English + accented audio'],
        ['Anthropic cache invalidation surprise (template change)',
         'Low', 'Medium',
         'cache_control markers pinned; alert on cache_hit_ratio drop'],
        ['Google Calendar rate limits (FreeBusy = quota)',
         'Medium', 'Medium',
         '30s Redis cache on FreeBusy; exponential backoff; dashboard surfaces 429 explicitly'],
        ['Race: two parallel book_appointment calls hit same slot',
         'High', 'High',
         'Idempotency on (caller_phone, slot) + re-check availability at booking time + SELECT FOR UPDATE on a slot lock row'],
        ['arq worker crashes mid-job → partial state',
         'Low', 'High',
         'Idempotent UPSERTs; retries 3x; on give-up → dead-letter queue + alert'],
        ['Cost drift: float arithmetic rolls up wrong by a fraction',
         'Medium', 'Low',
         'Numeric(10,5) in DB; sum in SQL; test_cost_rollup.py golden test'],
        ['Dashboard XSS via transcript text (caller-controlled)',
         'Low', 'High',
         'React escapes by default; never use dangerouslySetInnerHTML; sanitise on ingest as defence in depth'],
        ['Provider key leaked via agent prompt (prompt injection)',
         'Low', 'Critical',
         'Agent has no secrets in context; every privileged action goes through a tool; tool args validated server-side; SMS templates only'],
        ['Cartesia voice quota exceeded on spike day',
         'Low', 'Medium',
         'Pre-warmed connection; fallback voice id from settings; daily quota alert'],
    ]

    risk_style = [
        ('BACKGROUND', (0, 0), (-1, 0), DARK_CARD),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#111124')),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('TEXTCOLOR', (0, 1), (-1, -1), LIGHT_GREY),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#111124'), colors.HexColor('#0F0F1E')]),
        ('GRID', (0, 0), (-1, -1), 0.4, CARD_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        # Likelihood colors
        ('TEXTCOLOR', (1, 1), (1, 1), GOLD),
        ('TEXTCOLOR', (1, 2), (1, 2), GREEN),
        ('TEXTCOLOR', (1, 3), (1, 3), GOLD),
        ('TEXTCOLOR', (1, 4), (1, 4), GREEN),
        ('TEXTCOLOR', (1, 5), (1, 5), GOLD),
        ('TEXTCOLOR', (1, 6), (1, 6), RED_SOFT),
        ('TEXTCOLOR', (1, 7), (1, 7), GREEN),
        ('TEXTCOLOR', (1, 8), (1, 8), GOLD),
        ('TEXTCOLOR', (1, 9), (1, 9), GREEN),
        ('TEXTCOLOR', (1, 10), (1, 10), GREEN),
        ('TEXTCOLOR', (1, 11), (1, 11), GREEN),
        # Impact colors
        ('TEXTCOLOR', (2, 1), (2, 1), RED_SOFT),
        ('TEXTCOLOR', (2, 2), (2, 2), RED_SOFT),
        ('TEXTCOLOR', (2, 3), (2, 3), GOLD),
        ('TEXTCOLOR', (2, 4), (2, 4), GOLD),
        ('TEXTCOLOR', (2, 5), (2, 5), GOLD),
        ('TEXTCOLOR', (2, 6), (2, 6), RED_SOFT),
        ('TEXTCOLOR', (2, 7), (2, 7), RED_SOFT),
        ('TEXTCOLOR', (2, 8), (2, 8), GREEN),
        ('TEXTCOLOR', (2, 9), (2, 9), RED_SOFT),
        ('TEXTCOLOR', (2, 10), (2, 10), RED_SOFT),
        ('TEXTCOLOR', (2, 11), (2, 11), GOLD),
    ]
    t = Table(rows, colWidths=[55 * mm, 18 * mm, 18 * mm, 74 * mm])
    t.setStyle(TableStyle(risk_style))
    elems.append(t)
    return elems


def acceptance_criteria():
    elems = []
    elems += section_header(
        '17  Acceptance Criteria per Phase',
        'Definition of done — each phase in the Full Scope is "done" when every box here ticks',
    )

    rows = [
        ['Phase', 'Done when…'],
        ['0 — Scope & Content',
         'business hours/prices/FAQs in prompt_versions row; must/must-not list reviewed; voice persona locked; eval scenarios ≥ 20 written'],
        ['1 — Prompt validation',
         'make eval passes on the locked prompt; baseline saved; tool_call_accuracy ≥ 90%; brevity p50 ≤ 25 words'],
        ['2 — Core voice agent (P0)',
         'Telnyx number live; 24/7 inbound answers with AI disclosure; take_message / transfer_call / end_call working; call + turn rows persisted; email notifications firing; max duration + spend caps enforced; grace on API errors'],
        ['3 — Booking + dashboard v1',
         'check_availability / book_appointment live with idempotency; post_call job produces summary + intent + outcome + cost; dashboard read paths render; prompt editor publishes versions; soft launch on after-hours only — 1 week without regression'],
        ['4 — Intelligence + polish',
         'caller recognition + history; reschedule/cancel + SMS confirmations; knowledge base + RAG; gap list; intent/outcome tagging; cost-per-call metric; Telegram/WhatsApp alerts; daily report; latency tuned to < 800 ms p95 on real data; regression eval in CI; full-hours launch'],
        ['5 — Growth',
         'multilingual coverage; CRM integration; outbound reminders; spam filtering + block list; quality review queue; test-call button; multi-tenant (if reselling)'],
    ]
    elems.append(card_table(rows, [42 * mm, 123 * mm]))
    return elems


def conclusion():
    elems = []
    elems += section_header(
        '18  Conclusion & Next Steps',
        'Summary and the first PR',
    )

    elems.append(p(
        'This scope covers every TODO in the scaffold and the contracts that bind the four '
        'services together. The build order in §02 is the critical path; everything else is '
        'parallelisable. The acceptance criteria in §17 are the exit gates; nothing leaves '
        'a phase without all boxes ticked. The risks in §16 are the things we watch during '
        'the first two weeks of real traffic.'
    ))
    elems.append(sp(8))

    elems += mini_header('First PR (Day 1)')
    rows = [
        ['Step', 'Action', 'Owner'],
        ['1', 'cp .env.example .env; fill required keys (POSTGRES_PASSWORD, SECRET_KEY, NEXTAUTH_SECRET, TELNYX_*, DEEPGRAM_API_KEY, CARTESIA_API_KEY, ANTHROPIC_API_KEY)',
         'Backend lead'],
        ['2', 'docker compose up — verify all 7 containers healthy (api, agent, worker, dashboard, caddy, postgres, redis)',
         'Backend lead'],
        ['3', 'make migrate; make seed — confirm first business + admin user',
         'Backend lead'],
        ['4', 'Wire POST /webhooks/telnyx + Ed25519 signature verification per §08 — opens with 401 on unsigned requests',
         'Backend lead'],
        ['5', 'Implement api/routers/internal.py: POST /internal/calls + POST /internal/call-turns + POST /internal/calls/{id}/finalize per §05',
         'Agent lead'],
        ['6', 'Assemble empty Pipecat pipeline in agent/pipeline.py — Telnyx in/out only; hangup cleanly',
         'Agent lead'],
        ['7', 'Add CostTracker stub in agent/cost.py — snapshot returns all zeros but the wiring is exercised on every turn',
         'Agent lead'],
        ['8', 'CI: lint + pytest + make eval — must be green before any feature branch merges',
         'All'],
    ]
    elems.append(card_table(rows, [10 * mm, 90 * mm, 65 * mm]))
    elems.append(sp(12))

    elems.append(rule(ACCENT_PURPLE, 1))
    elems.append(sp(6))
    elems.append(Paragraph(
        '<font color="#7C3AED">AI Receptionist</font> — '
        '<font color="#EC4899">a 24/7 voice receptionist that never sleeps, never misses a call, '
        'and never forgets a customer.</font>',
        ParagraphStyle('Final', fontSize=14, textColor=WHITE, fontName='Helvetica-Bold',
                       alignment=TA_CENTER, leading=18),
    ))
    elems.append(sp(4))
    elems.append(p(
        'This document is confidential and proprietary. Not for distribution. '
        'Companion to the Full Scope — refer to that document for product, cost, and roadmap.',
        'caption',
    ))
    return elems


# ─── Main ─────────────────────────────────────────────────────────────────────
def build():
    global S
    S = make_styles()

    out = os.path.join(os.getcwd(), 'AI_Receptionist_Technical_Implementation_Scope.pdf')
    doc = SimpleDocTemplate(
        out,
        pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=22 * mm,
        title='AI Receptionist — Technical Implementation Scope',
        author='AI Receptionist Engineering',
        subject='Engineering build plan, API contracts, stub-completion, test strategy',
    )

    story = []

    # Cover page (blank content — drawn by canvas function)
    story.append(PageBreak())

    sections = [
        executive_summary,
        build_order,
        stub_checklist,
        data_model_deltas,
        api_contracts,
        agent_pipeline_spec,
        tool_specs,
        webhook_verification,
        cost_tracker,
        post_call_job,
        prompt_caching,
        eval_harness,
        test_strategy,
        observability,
        deploy_pipeline,
        risks,
        acceptance_criteria,
        conclusion,
    ]

    for i, fn in enumerate(sections):
        story.extend(fn())
        if i < len(sections) - 1:
            story.append(PageBreak())

    # Page template: cover for page 1, dark for rest
    def on_page(canvas, doc):
        if doc.page == 1:
            cover_page(canvas, doc)
        else:
            dark_page(canvas, doc)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF written to {out}')


if __name__ == '__main__':
    build()