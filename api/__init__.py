"""FastAPI backend for the AI receptionist.

This service owns:
  - The HTTP API the staff dashboard talks to.
  - The webhook endpoints the agent calls to log turns, save messages, etc.
  - Background jobs (post-call summaries, notifications, daily report).
  - Migrations and the schema definition.

It does NOT own the conversation loop. That lives in /agent.