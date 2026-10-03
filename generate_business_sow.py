"""
AI Receptionist — Business Statement of Work (SOW)
Generates a dark-themed, A4 PDF matching the styling of the project's
other scope documents. Non-technical; pitched at business stakeholders.

Usage:
    python generate_business_sow.py
Output:
    AI_Receptionist_Business_SOW.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable,
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

    canvas.setFillColorRGB(0.48, 0.23, 0.93, alpha=0.06)
    canvas.circle(PAGE_W * 0.85, PAGE_H * 0.9, 140, fill=1, stroke=0)
    canvas.setFillColorRGB(0.93, 0.28, 0.60, alpha=0.05)
    canvas.circle(PAGE_W * 0.1, PAGE_H * 0.15, 110, fill=1, stroke=0)

    canvas.setStrokeColor(CARD_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, 14 * mm, PAGE_W - 20 * mm, 14 * mm)

    canvas.setFillColor(MID_GREY)
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(
        PAGE_W / 2, 9 * mm,
        f'Page {doc.page}  ·  AI Receptionist — Business Statement of Work  ·  Confidential',
    )
    canvas.restoreState()


def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(BG_DARK)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    canvas.setFillColorRGB(0.48, 0.23, 0.93, alpha=0.18)
    canvas.circle(PAGE_W, PAGE_H, 260, fill=1, stroke=0)
    canvas.setFillColorRGB(0.93, 0.28, 0.60, alpha=0.14)
    canvas.circle(0, 0, 200, fill=1, stroke=0)
    canvas.setFillColorRGB(0.024, 0.71, 0.831, alpha=0.10)
    canvas.circle(PAGE_W, 0, 150, fill=1, stroke=0)

    canvas.setFillColor(ACCENT_PURPLE)
    canvas.rect(0, PAGE_H * 0.47, PAGE_W, 2, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_PINK)
    canvas.rect(0, PAGE_H * 0.47 - 2, PAGE_W, 2, fill=1, stroke=0)

    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 60)
    canvas.drawCentredString(PAGE_W / 2, PAGE_H * 0.62, 'AI RECEPTIONIST')

    canvas.setFillColor(LIGHT_GREY)
    canvas.setFont('Helvetica', 14)
    canvas.drawCentredString(
        PAGE_W / 2, PAGE_H * 0.555,
        'A 24/7 AI Phone Receptionist for Small & Mid-Sized Businesses',
    )

    canvas.setFillColor(DARK_CARD)
    canvas.roundRect(40 * mm, PAGE_H * 0.36, PAGE_W - 80 * mm, 52, 8, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_CYAN)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawCentredString(PAGE_W / 0.6 / 1, PAGE_H * 0.395, 'BUSINESS STATEMENT OF WORK')
    canvas.setFillColor(MID_GREY)
    canvas.setFont('Helvetica', 9)
    canvas.drawCentredString(
        PAGE_W / 2, PAGE_H * 0.375,
        'Version 1.0  ·  ai-receptionist v0.1.0  ·  2026  ·  Confidential',
    )

    stats = [
        ('24/7', 'Coverage'),
        ('< $0.05', 'Per Call'),
        ('< 1 sec', 'Response'),
        ('~ 6 wks', 'To Launch'),
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
        'body': ps('Body', fontSize=10, textColor=LIGHT_GREY, fontName='Helvetica',
                   spaceAfter=5, leading=14),
        'bullet': ps('Bullet', fontSize=9.5, textColor=LIGHT_GREY, fontName='Helvetica',
                     spaceAfter=3, leading=14, leftIndent=12, bulletIndent=0),
        'caption': ps('Caption', fontSize=8, textColor=MID_GREY, fontName='Helvetica',
                      spaceAfter=2, leading=11),
        'section_label': ps('SL', fontSize=8, textColor=ACCENT_PURPLE,
                             fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=2,
                             leading=10),
        'white_bold': ps('WB', fontSize=10.5, textColor=WHITE, fontName='Helvetica-Bold',
                         spaceAfter=3, leading=14),
        'lead': ps('Lead', fontSize=11.5, textColor=WHITE, fontName='Helvetica',
                   spaceAfter=8, leading=18),
    }


S = None

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
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#111124'), colors.HexColor('#0F0F1E')]),
        ('GRID', (0, 0), (-1, -1), 0.4, CARD_BORDER),
        ('ROUNDEDCORNERS', [4]),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
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

def feature_block(title, priority, items_list):
    elems = []
    title_row = [[
        Paragraph(
            f'<b>{title}</b>',
            ParagraphStyle('F', fontSize=11, textColor=WHITE,
                           fontName='Helvetica-Bold', leading=14),
        ),
        Paragraph(
            priority,
            ParagraphStyle('FP', fontSize=8.5, textColor=GOLD if priority.startswith('Phase') else GREEN,
                           fontName='Helvetica-Bold', leading=12, alignment=TA_RIGHT),
        ),
    ]]
    t = Table(title_row, colWidths=[130 * mm, 35 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK_CARD),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LINEBELOW', (0, 0), (-1, -1), 2, ACCENT_PURPLE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elems.append(sp(6))
    elems.append(t)
    item_rows = [[
        Paragraph(
            f'<font color="#7C3AED">◆</font>  {it}',
            ParagraphStyle('FI', fontSize=9, textColor=LIGHT_GREY,
                           fontName='Helvetica', leading=13),
        ),
    ] for it in items_list]
    it = Table(item_rows, colWidths=[165 * mm])
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


# ─── Sections ─────────────────────────────────────────────────────────────────

def executive_summary():
    elems = []
    elems += section_header(
        '01  Executive Summary',
        'A 24/7 AI phone receptionist for businesses that cannot afford to miss a call',
    )

    elems.append(p(
        'The AI Receptionist is a self-hosted voice agent that answers every inbound call '
        'to a business, day or night, in a human-sounding voice. It greets callers, takes '
        'messages, books appointments, transfers urgent calls to staff, and answers common '
        'questions — all while the business owner sleeps, focuses on customers in front of '
        'them, or runs the business after hours. Every call is recorded, transcribed, '
        'summarised, and surfaced in a simple dashboard where staff can review activity, '
        'update what the agent says, and follow up on leads.'
    ))
    elems.append(sp(6))
    elems.append(p(
        'This Statement of Work (SOW) explains what the product does, what problem it solves, '
        'what is included, the timeline to launch, and what success looks like. It is written '
        'for non-technical readers — owners, managers, and decision-makers evaluating whether '
        'to adopt the system.'
    ))
    elems.append(sp(10))

    rows = [
        ['Dimension', 'Detail'],
        ['Product', 'AI Receptionist — voice agent + management dashboard'],
        ['Version', 'v0.1.0 (Scaffold complete; ready for content + tuning)'],
        ['Target Customer', 'Service businesses: clinics, salons, legal, trades, real estate'],
        ['Coverage', '24/7/365 — no missed calls, no after-hours voicemail'],
        ['Total Cost to Run', '~$45–$90/month for ~50 calls/day'],
        ['Time to Launch', '~6 weeks from kickoff'],
        ['Compliance', 'AI disclosure on every call; PCI-safe (no card data); GDPR-ready'],
    ]
    elems.append(card_table(rows, [55 * mm, 110 * mm]))
    return elems


def problem_statement():
    elems = []
    elems += section_header(
        '02  Problem Statement',
        'Why this product exists — the missed-call problem and its cost',
    )

    elems.append(p(
        'Small and mid-sized businesses lose revenue and erode customer trust every time a '
        'phone call goes unanswered. The drivers are familiar and persistent across the '
        'service economy:'
    ))
    elems.append(sp(4))
    elems += bul([
        '<b>After-hours and lunchtime gaps.</b> Most SMBs cannot afford 24/7 staff; calls outside business hours go to voicemail — and 80% of callers will not leave a message.',
        '<b>Front-desk overload.</b> When staff are tied up with a customer in front of them, the phone rings out. The caller moves on to a competitor.',
        '<b>Slow callbacks.</b> Owners juggle callbacks between meetings and miss the 5-minute window when a lead is still warm.',
        '<b>Inconsistent answers.</b> Front-desk staff improvise on pricing, hours, and policies — leading to mistakes that cost trust.',
        '<b>No record of what was said.</b> Verbal commitments made on the phone vanish; disputes and follow-ups lose context.',
        '<b>Voicemail fatigue.</b> Callers hate voicemail and increasingly abandon the call before the beep.',
    ])
    elems.append(sp(8))

    elems += mini_header('The cost of a missed call')
    rows = [
        ['Business type', 'Avg. value of a missed call', 'Why'],
        ['Dental clinic', '$300 – $800',
         'New patient consults, hygiene appointments'],
        ['Salon / spa', '$80 – $250',
         'Service bookings, retail add-ons'],
        ['Law firm', '$500 – $5,000',
         'Case intake; one missed call can mean a lost client'],
        ['Trades (plumber, HVAC, electrician)', '$200 – $1,500',
         'Emergency service calls; high urgency, high value'],
        ['Real estate agent', '$1,000 – $10,000+',
         'Listing inquiries; lifetime commission value'],
    ]
    elems.append(card_table(rows, [50 * mm, 35 * mm, 80 * mm]))

    elems.append(sp(10))
    elems.append(p(
        'For a typical service business, just <b>three missed calls per week</b> translates '
        'to thousands of dollars in lost revenue every month. The cost of doing nothing is '
        'rarely zero.'
    ))
    return elems


def proposed_solution():
    elems = []
    elems += section_header(
        '03  Proposed Solution',
        'Always-on, on-brand, polite — and never tired',
    )

    elems.append(p(
        'The AI Receptionist is an AI voice agent that sits on the business phone line. '
        'It answers immediately, identifies itself as an AI assistant (as required by law '
        'in the US and EU), and handles the call end-to-end using a configurable script '
        'tailored to the business. It uses a natural-sounding voice, understands '
        'free-flowing conversation, and recognises when a caller needs a human — at which '
        'point it transfers the call or captures the details for a callback.'
    ))
    elems.append(sp(8))

    rows = [
        ['Without AI Receptionist', 'With AI Receptionist'],
        ['60% of after-hours calls go to voicemail',
         '100% of calls answered in under a second'],
        ['Front desk juggles in-person and phone — caller hears ringing',
         'Every caller greeted warmly within ~600 ms of the line opening'],
        ['Owners return calls hours later, leads have moved on',
         'Leads contacted within the configured SLA — email or SMS'],
        ['Staff improvise on pricing, hours, and policies',
         'Consistent, on-brand answers drawn from a single source of truth'],
        ['No record of who called and what was said',
         'Every call transcribed, summarised, and searchable in the dashboard'],
        ['Booking only when staff are free',
         'Bookings placed 24/7, with confirmations sent automatically'],
    ]
    elems.append(card_table(rows, [82 * mm, 83 * mm], [
        ('TEXTCOLOR', (0, 1), (0, -1), RED_SOFT),
        ('TEXTCOLOR', (1, 1), (1, -1), GREEN),
    ]))
    return elems


def scope_included():
    elems = []
    elems += section_header(
        '04  Scope of Work — What Is Included',
        'Everything delivered under this SOW',
    )

    elems.append(p(
        'The following deliverables are included in this engagement. Anything not listed '
        'here is considered out of scope and will require a separate change request.'
    ))
    elems.append(sp(6))

    rows = [
        ['#', 'Deliverable', 'Description'],
        ['1', 'Voice agent',
         'Custom-trained AI voice agent that answers inbound calls, handles common questions, takes messages, books appointments, and transfers urgent calls. Configurable voice persona; on-brand script.'],
        ['2', 'Phone number & telephony',
         'Telnyx inbound number provisioned for the business; caller ID; routing configured; recording disabled by default (toggleable).'],
        ['3', 'Calendar integration',
         'Google Calendar integration for availability checks and 2× booking. Real-time conflict detection; automatic confirmations.'],
        ['4', 'Knowledge base',
         'Up to 50 FAQ entries (hours, prices, services, policies, directions) — seeded during onboarding; editable by staff.'],
        ['5', 'Management dashboard',
         'Web dashboard for staff to review calls, messages, and appointments; edit what the agent says; manage contacts and blocked numbers; view usage and costs.'],
        ['6', 'Notifications',
         'Email, SMS, Telegram, and Slack notifications for new messages, bookings, and urgent escalations. Multi-channel configurable.'],
        ['7', 'Call recording & transcription',
         'Calls transcribed automatically; AI-generated 2–3 sentence summary; searchable history; export to PNG (MP3).'],
        ['8', 'Daily summary report',
         'Once-daily email summarising calls, messages, bookings, and notable escalations.'],
        ['9', 'Self-hosting & deployment',
         'Docker Compose deployment on the customer server (or managed hosting). TLS via Let’s Encrypt; nightly backups; 24/7 health monitoring.'],
        ['10', 'Training & handover',
         'Two 1-hour live sessions for staff: one on the dashboard, one on tuning the agent’s responses. Written playbook (SOP).'],
    ]
    elems.append(card_table(rows, [10 * mm, 40 * mm, 115 * mm]))
    return elems


def features():
    elems = []
    elems += section_header(
        '05  Features',
        'Full feature inventory, grouped by phase',
    )

    elems.append(p(
        'Features are grouped into three release waves. Wave 1 ships with launch. '
        'Waves 2 and 3 are scheduled upgrades after launch and are included in this SOW.'
    ))
    elems.append(sp(6))

    # Wave 1 — launch
    elems += feature_block(
        'Wave 1 — Launch (Phases 0–3)',
        'Ships in ~6 weeks',
        [
            '<b>24/7 inbound answering</b> — every call answered in under 1 second, with a warm, on-brand greeting',
            '<b>AI disclosure</b> — the agent identifies itself as an AI assistant on every call (US/EU requirement)',
            '<b>Take messages</b> — captures name, phone, and reason; sends to staff by email / SMS / Telegram / Slack',
            '<b>Book appointments</b> — checks real-time calendar availability and books the slot; sends caller an SMS confirmation',
            '<b>Transfer to staff</b> — for urgent calls (medical, emergency, angry customer), routes to a human phone; falls back to take-message if no answer',
            '<b>Answer FAQs</b> — answers from the knowledge base: hours, prices, directions, services, policies',
            '<b>Call recording & transcript</b> — every call recorded (if enabled) and transcribed; searchable in the dashboard',
            '<b>AI summary</b> — each call gets a 2–3 sentence summary plus tags (intent, outcome, sentiment)',
            '<b>Dashboard</b> — review calls, messages, bookings, contacts; edit what the agent says; view costs',
            '<b>Notifications</b> — email + SMS + Telegram + Slack; configurable per business',
            '<b>Daily report</b> — end-of-day summary delivered to the business owner',
            '<b>Block list</b> — staff can block spam numbers; blocked callers hear a brief message and are routed away',
            '<b>Spend caps</b> — per-call and per-day spend caps enforced automatically',
        ],
    )

    elems.append(sp(10))

    # Wave 2 — first 60 days
    elems += feature_block(
        'Wave 2 — Intelligence Layer (30–60 days post-launch)',
        'Updates within 60 days',
        [
            '<b>Caller recognition</b> — returning callers are greeted by name and routed based on history',
            '<b>Reschedule & cancel</b> — callers can reschedule or cancel existing bookings by voice',
            '<b>SMS confirmations</b> — automatic SMS reminders 24 hours and 1 hour before appointments',
            '<b>Knowledge base growth</b> — staff see a list of questions the agent could not answer; one-click to add as FAQ',
            '<b>Quality review queue</b> — flagged calls surfaced for staff review with one-click notes',
            '<b>Cost reporting</b> — per-call and per-day cost dashboards; spend trends',
        ],
    )

    elems.append(sp(10))

    # Wave 3 — growth
    elems += feature_block(
        'Wave 3 — Polish & Scale (60–120 days post-launch)',
        'Updates within 120 days',
        [
            '<b>Outbound reminders</b> — the agent can place reminder calls for appointments and follow-ups',
            '<b>Spam filtering</b> — AI-driven detection of robocalls and spam; silent hangup',
            '<b>Multi-language</b> — switch between languages mid-conversation',
            '<b>CRM integration</b> — push contacts and call notes to HubSpot, Salesforce, or Zoho',
            '<b>Test call button</b> — staff can place a test call from the dashboard to validate behaviour',
            '<b>Multilingual voice</b> — pick voice and accent per business',
        ],
    )
    return elems


def how_it_works():
    elems = []
    elems += section_header(
        '06  How It Works',
        'From caller dial to dashboard — what happens on a typical call',
    )

    elems.append(p(
        'A typical call follows this flow. Most calls take less than two minutes.'
    ))
    elems.append(sp(6))

    flow_rows = [
        ['Step', 'What happens', 'Time'],
        ['1', 'Caller dials the business number — it rings once.',
         '< 1 s'],
        ['2', 'The agent answers and greets the caller by name (if recognised) and identifies itself as an AI assistant.',
         '~ 1 s'],
        ['3', 'The caller explains what they need — for example, "I’d like to book a haircut for tomorrow afternoon."',
         'varies'],
        ['4', 'The agent checks the calendar, proposes available slots, and confirms the booking.',
         '~ 5–10 s'],
        ['5', 'The caller receives an SMS confirmation with the appointment details.',
         '~ 2 s'],
        ['6', 'The call ends. Staff see a new row in the dashboard with the recording, transcript, and a 2-line summary.',
         '~ 5 s after hangup'],
    ]
    elems.append(card_table(flow_rows, [12 * mm, 115 * mm, 38 * mm]))

    elems.append(sp(10))
    elems += mini_header('What the caller experiences')
    elems.append(p(
        'A warm, natural voice. No menu trees. No hold queue. No voicemail. '
        'Conversational — callers speak normally and are understood. '
        'Polite and on-brand — the agent uses the business name, the right tone, '
        'and the right words every time.'
    ))

    elems.append(sp(8))
    elems += mini_header('What the business owner experiences')
    elems.append(p(
        'A web dashboard where every call appears within seconds of hanging up. '
        'Each call has a one-paragraph summary, the caller’s details, the recording, '
        'the transcript, and the outcome (booked / messaged / transferred). '
        'Owners tune what the agent says through a simple editor — no code required.'
    ))

    elems.append(sp(8))
    elems += mini_header('What staff experience')
    elems += bul([
        'A shared inbox of messages (with status: new → done), filtering by urgency',
        'A calendar view of bookings, with one-click cancel and reschedule',
        'A quality-review queue for flagged calls',
        'A contacts list with history, tags, and block-list toggle',
        'A settings page for users, notification channels, and retention',
    ])
    return elems


def tech_overview():
    elems = []
    elems += section_header(
        '07  Technology Overview',
        'A simple, modern stack — explained without jargon',
    )

    elems.append(p(
        'The system uses a small number of proven, best-in-class vendors. The business '
        'owns its own data; nothing is locked in. All components have been selected '
        'for reliability, low latency, low cost, and ease of replacement.'
    ))
    elems.append(sp(6))

    rows = [
        ['Layer', 'Vendor', 'What it does for the business'],
        ['Phone service', 'Telnyx',
         'Carries the inbound calls to the AI agent. Low-cost, reliable, supports call transfers.'],
        ['Speech-to-text', 'Deepgram',
         'Transcribes the caller’s voice in real time so the agent can understand. Industry-leading accuracy, ~$0.004/min.'],
        ['AI brain', 'Claude (Anthropic)',
         'The agent’s reasoning — understands the caller, decides what to say, picks the right tool. Fast and low-cost.'],
        ['Voice (text-to-speech)', 'Cartesia',
         'Speaks the agent’s responses in a natural human voice. Sub-second first response.'],
        ['Backend & API', 'Self-hosted (FastAPI)',
         'Stores calls, messages, bookings, and contacts. Handles webhooks and the dashboard API.'],
        ['Database', 'PostgreSQL + pgvector',
         'All business data + AI-powered FAQ search.'],
        ['Dashboard', 'Next.js (web)',
         'The web interface staff use to review calls and manage the agent.'],
        ['Notifications', 'Email + SMS + Telegram + Slack',
         'Staff are notified the way they already work.'],
        ['Hosting', 'Self-hosted Docker or managed VPS',
         'Runs anywhere: the customer’s server, a small VPS, or our managed hosting.'],
    ]
    elems.append(card_table(rows, [32 * mm, 38 * mm, 95 * mm]))

    elems.append(sp(10))
    elems += mini_header('Why these choices')
    elems += bul([
        '<b>Self-hosted by default</b> — the business owns its data and its phone number. No per-minute SaaS markup; no vendor lock-in.',
        '<b>Best-of-breed</b> — each vendor is the strongest in its category; swapping one is a contained change.',
        '<b>Low cost</b> — ~$0.03–$0.06 per minute of call. A typical 2.5-minute call costs under $0.15.',
        '<b>Low latency</b> — typical response time is under 1 second; natural conversational feel.',
        '<b>Compliant</b> — AI disclosure, GDPR-ready, encryption in transit and at rest. PCI-safe (no card data ever spoken).',
    ])
    return elems


def call_cost():
    elems = []
    elems += section_header(
        '08  Cost to Run — What Each Call Costs',
        'Transparent, predictable cost per call',
    )

    elems.append(p(
        'A typical 2.5-minute call (the median for a service business) costs '
        'roughly <b>$0.08 to $0.15</b> across all providers. The breakdown:'
    ))
    elems.append(sp(6))

    rows = [
        ['Component', 'Cost per minute', 'Notes'],
        ['Phone service (Telnyx)', '~$0.008',
         'Inbound minutes only; outbound not used in Wave 1'],
        ['Speech-to-text (Deepgram)', '~$0.004',
         'Streaming partials — billed per second of audio'],
        ['Voice (Cartesia)', '~$0.015',
         'Billed per character of generated speech'],
        ['AI brain (Claude Haiku)', '~$0.001 – $0.010',
         'Varies with conversation length; cheaper on shorter calls'],
        ['Total per minute', '~$0.03 – $0.05',
         'Most calls cluster around $0.035/min'],
    ]
    elems.append(card_table(rows, [50 * mm, 28 * mm, 87 * mm]))

    elems.append(sp(10))
    elems += mini_header('Monthly cost examples')
    rows = [
        ['Call volume', 'Avg. length', 'Estimated monthly cost'],
        ['~10 calls / day', '2.5 min',
         '~$25 – $40 / month'],
        ['~20 calls / day', '2.5 min',
         '~$45 – $80 / month'],
        ['~50 calls / day', '2.5 min',
         '~$110 – $200 / month'],
    ]
    elems.append(card_table(rows, [40 * mm, 30 * mm, 95 * mm]))

    elems.append(sp(10))
    elems.append(p(
        'A simple cost-control setting caps total spend per day (default $50) — '
        'beyond which the agent politely takes a message instead of continuing. '
        'The owner is never surprised by an invoice.'
    ))
    return elems


def timeline():
    elems = []
    elems += section_header(
        '09  Timeline & Delivery Plan',
        'From kickoff to live in ~6 weeks',
    )

    elems.append(p(
        'The project runs across five phases. Each phase ends with a live demo and a '
        'go/no-go gate before the next begins.'
    ))
    elems.append(sp(6))

    phases = [
        ('Phase 0', 'Content & Configuration',
         'Week 1',
         [
             'Discovery call — capture business hours, services, prices, policies, FAQs',
             'Draft the agent’s persona, tone, and standard responses',
             'Provision phone number, calendar access, and notification channels',
             'Kickoff session with the business owner to confirm scope',
         ]),
        ('Phase 1', 'Prompt Validation',
         'Week 2',
         [
             'Test the agent’s responses against realistic caller scenarios (≥ 20)',
             'Refine the prompt until responses are consistent and on-brand',
             'Owner review and approval of the agent’s voice and behaviour',
             'Capture the first baseline of agent behaviour for regression testing',
         ]),
        ('Phase 2', 'Voice Agent Goes Live (After-Hours Only)',
         'Week 3',
         [
             'Phone number live; calls route to the AI agent outside business hours',
             'Live test calls covering messages, bookings, and transfers',
             'Email + SMS notifications working end-to-end',
             'Daily review of transcripts; fine-tune where needed',
         ]),
        ('Phase 3', 'Dashboard & Prompt Editor',
         'Week 4',
         [
             'Dashboard live for staff — calls, messages, bookings, contacts',
             'Prompt editor live — staff can update what the agent says',
             'Quality-review workflow operational',
         ]),
        ('Phase 4', 'Full-Hours Launch',
         'Weeks 5–6',
         [
             'After 1 stable week on after-hours, the agent is enabled 24/7',
             'Caller recognition + history enabled',
             'Knowledge base growth tooling live (FAQ from real questions)',
             'Daily summary report delivered to the owner',
             'Two staff training sessions (dashboard + prompt tuning)',
             'Written playbook handed off',
         ]),
    ]

    for name, title, when, items_list in phases:
        rows = [[
            Paragraph(
                f'<font color="#7C3AED"><b>{name}</b></font>',
                S['section_label'],
            ),
            Paragraph(
                f'<b>{title}</b>',
                ParagraphStyle('PT', fontSize=11, textColor=WHITE,
                               fontName='Helvetica-Bold', leading=14),
            ),
            Paragraph(
                when,
                ParagraphStyle('PD', fontSize=9, textColor=GOLD,
                               fontName='Helvetica-Bold', leading=12, alignment=TA_RIGHT),
            ),
        ]]
        t = Table(rows, colWidths=[28 * mm, 95 * mm, 42 * mm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), DARK_CARD),
            ('GRID', (0, 0), (-1, -1), 0, colors.transparent),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 2, ACCENT_PURPLE),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elems.append(sp(8))
        elems.append(t)
        elems.append(sp(4))
        elems += bul(items_list)
        elems.append(sp(4))

    return elems


def sla():
    elems = []
    elems += section_header(
        '10  Service Levels & Support',
        'What we commit to after launch',
    )

    rows = [
        ['Commitment', 'Target'],
        ['Agent availability (uptime)', '99.5% per month, excluding scheduled maintenance'],
        ['Answer time on inbound calls', 'Under 1 second (95th percentile)'],
        ['Notification delivery', 'Within 30 seconds of call end'],
        ['Dashboard load time', 'Under 2 seconds (95th percentile)'],
        ['Daily summary report', 'Delivered by 8:00 AM local time'],
        ['Backup retention', '30 days rolling (calls, transcripts, recordings)'],
        ['Security patching', 'Critical patches within 48 hours'],
        ['Bug reports — P1', 'Acknowledged within 4 business hours; fix or workaround within 24 hours'],
        ['Bug reports — P2', 'Acknowledged within 1 business day; fix scheduled within the next release'],
        ['Feature requests', 'Reviewed monthly; roadmap update quarterly'],
        ['Maintenance windows', 'Sunday 02:00 – 04:00 local; 7-day notice for non-emergency'],
    ]
    elems.append(card_table(rows, [70 * mm, 95 * mm]))
    return elems


def success_metrics():
    elems = []
    elems += section_header(
        '11  Success Metrics',
        'How we measure whether the system is working',
    )

    rows = [
        ['Metric', 'Target (90 days post-launch)'],
        ['Calls answered by agent', '≥ 95% of inbound (excluding blocked)'],
        ['Calls requiring human transfer', '≤ 8% (down from baseline)'],
        ['Bookings placed by agent', '≥ 40% of appointment calls'],
        ['Messages captured and delivered to staff', '100% (within 30 seconds of call end)'],
        ['Caller satisfaction (post-call survey)', '≥ 4.2 / 5 stars'],
        ['Average call cost', '≤ $0.06 per minute'],
        ['Missed-call rate', '≤ 1% (down from ~60% outside hours)'],
        ['Dashboard weekly active staff', '≥ 2 of the business owner + 1 staff member'],
        ['Staff prompt-edit frequency', 'Initial edits in week 1; revisions every 2 weeks'],
    ]
    elems.append(card_table(rows, [80 * mm, 85 * mm]))

    elems.append(sp(10))
    elems += mini_header('Quarterly business review')
    elems.append(p(
        'Every 90 days, we present a one-page summary to the owner: calls answered, '
        'calls transferred, bookings, spend, and the top three calls the agent could not '
        'handle — with one-click actions to update the agent’s responses.'
    ))
    return elems


def out_of_scope():
    elems = []
    elems += section_header(
        '12  Out of Scope',
        'What this SOW does not include',
    )

    elems += bul([
        '<b>Outbound sales or marketing calls.</b> The agent handles inbound only in Wave 1. Outbound reminders arrive in Wave 3.',
        '<b>Handling payment card numbers by phone.</b> By design — the agent never accepts card numbers verbally. Payment links are sent by SMS.',
        '<b>HIPAA / protected health information.</b> Not supported in v0.1.0. Can be enabled with a separate compliance package.',
        '<b>Custom CRM integrations beyond the supported list.</b> HubSpot, Salesforce, and Zoho are supported in Wave 3. Other CRMs require a change-request.',
        '<b>Voice cloning of a specific person.</b> We use a curated set of natural-sounding voices. Voice cloning is a separate engagement.',
        '<b>Real-time translation between languages.</b> Multilingual support means the agent understands and responds in multiple languages, not simultaneous translation.',
        '<b>Hardware / phones / on-premise PBX.</b> We deliver a cloud-hosted or self-hosted service; we do not sell or install physical hardware.',
        '<b>Mobile apps for staff.</b> The dashboard is web-based and mobile-responsive in Wave 1; native mobile apps are not in scope.',
        '<b>24/7 live human support.</b> Email + business-hours live support in Wave 1. 24/7 live support is an add-on.',
    ])
    return elems


def assumptions():
    elems = []
    elems += section_header(
        '13  Assumptions & Dependencies',
        'What we are assuming to be true at kickoff',
    )

    elems += mini_header('Customer-side assumptions')
    elems += bul([
        'Business hours, services, prices, and policies are provided in writing within 5 business days of kickoff',
        'A Google Calendar is available (or willingness to create one) for booking integration',
        'Staff are available for two 1-hour training sessions in weeks 5 and 6',
        'Notification destination addresses (email, Telegram chat ID, Slack webhook) are configured before go-live',
        'Domain name and DNS access are available if hosted on the customer’s infrastructure',
        'A 2 vCPU / 4 GB server is available for self-hosted deployments (or willingness to use managed hosting)',
    ])

    elems.append(sp(8))
    elems += mini_header('Vendor-side dependencies')
    elems += bul([
        'Telnyx account is provisioned with a US/CA/UK number in the business’s region',
        'Deepgram, Cartesia, and Anthropic accounts are active with valid payment',
        'Google Workspace (or personal Google account) for Calendar integration',
        'Email delivery (SMTP or SendGrid/Resend) for outbound notifications',
        'SMS delivery via Telnyx messaging for confirmations',
    ])

    elems.append(sp(8))
    elems += mini_header('Compliance dependencies')
    elems += bul([
        'Recording consent: by default, calls are <b>not</b> recorded. Recording is opt-in per jurisdiction.',
        'Data residency: default is US-East. EU residency is available as a configuration change in Phase 4.',
        'GDPR data-subject requests supported within 30 days (deletion + export).',
    ])
    return elems


def acceptance():
    elems = []
    elems += section_header(
        '14  Acceptance Criteria',
        'What "done" means at each gate',
    )

    rows = [
        ['Gate', 'Done when…'],
        ['Phase 0 — Content',
         'Hours, services, prices, and FAQs documented; agent persona approved; phone number and calendar connected'],
        ['Phase 1 — Prompt Validation',
         '20+ realistic caller scenarios pass; tone and behaviour approved by the owner'],
        ['Phase 2 — After-Hours Live',
         'Calls answered live outside business hours for 7 consecutive days without critical bugs; notifications delivered on every call'],
        ['Phase 3 — Dashboard Live',
         'Staff can review every call, message, and booking; staff can edit what the agent says without engineering help'],
        ['Phase 4 — 24/7 Launch',
         'Agent live 24/7; staff trained; playbook delivered; first 30 days of metrics tracked and reviewed'],
    ]
    elems.append(card_table(rows, [42 * mm, 123 * mm]))

    elems.append(sp(10))
    elems += mini_header('Final acceptance')
    elems.append(p(
        'The project is complete when Phase 4 acceptance is signed off by the business '
        'owner and the system has run cleanly for 30 days in 24/7 mode with all SLA '
        'commitments met.'
    ))
    return elems


def conclusion():
    elems = []
    elems += section_header(
        '15  Next Steps & Sign-off',
        'What happens after this SOW is approved',
    )

    elems += mini_header('Immediate next steps (Week 1)')
    rows = [
        ['Step', 'Owner', 'Outcome'],
        ['1', 'Sign SOW; provision accounts',
         'Both sides', 'Telnyx, Deepgram, Cartesia, Anthropic accounts active'],
        ['2', 'Discovery call (1 hour)',
         'Vendor + Owner', 'Business hours, services, prices, FAQs captured'],
        ['3', 'Phone number & calendar setup',
         'Vendor', 'Inbound number live; calendar connected'],
        ['4', 'Draft agent persona & prompt',
         'Vendor', 'Ready for Phase 1 scenario testing'],
    ]
    elems.append(card_table(rows, [10 * mm, 50 * mm, 105 * mm]))

    elems.append(sp(10))
    elems += mini_header('Sign-off')
    rows = [
        ['Party', 'Name', 'Signature', 'Date'],
        ['Customer', '_________________________', '_________________________', '____________'],
        ['Vendor', '_________________________', '_________________________', '____________'],
    ]
    elems.append(card_table(rows, [30 * mm, 55 * mm, 55 * mm, 25 * mm]))

    elems.append(sp(12))
    elems.append(rule(ACCENT_PURPLE, 1))
    elems.append(sp(6))
    elems.append(Paragraph(
        '<font color="#7C3AED">AI Receptionist</font> — '
        '<font color="#EC4899">never miss a call, never miss a customer.</font>',
        ParagraphStyle('Final', fontSize=14, textColor=WHITE, fontName='Helvetica-Bold',
                       alignment=TA_CENTER, leading=18),
    ))
    elems.append(sp(4))
    elems.append(p(
        'This document is confidential and proprietary. Not for distribution. '
        'Companion to the Full Scope and the Technical Implementation Scope.',
        'caption',
    ))
    return elems


# ─── Main ─────────────────────────────────────────────────────────────────────
def build():
    global S
    S = make_styles()

    out = os.path.join(os.getcwd(), 'AI_Receptionist_Business_SOW.pdf')
    doc = SimpleDocTemplate(
        out,
        pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=18 * mm, bottomMargin=22 * mm,
        title='AI Receptionist — Business Statement of Work',
        author='AI Receptionist',
        subject='Non-technical Statement of Work covering problem, solution, scope, features, tech overview, timeline, SLAs, and acceptance criteria',
    )

    story = []
    story.append(PageBreak())

    sections = [
        executive_summary,
        problem_statement,
        proposed_solution,
        scope_included,
        features,
        how_it_works,
        tech_overview,
        call_cost,
        timeline,
        sla,
        success_metrics,
        out_of_scope,
        assumptions,
        acceptance,
        conclusion,
    ]

    for i, fn in enumerate(sections):
        story.extend(fn())
        if i < len(sections) - 1:
            story.append(PageBreak())

    def on_page(canvas, doc):
        if doc.page == 1:
            cover_page(canvas, doc)
        else:
            dark_page(canvas, doc)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f'PDF written to {out}')


if __name__ == '__main__':
    build()