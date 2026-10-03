"""Background jobs — post-call processing, notifications, daily report.

Run via `python -m api.worker` against an arq worker pool backed by Redis.
"""

from __future__ import annotations

from arq.connections import RedisSettings

from api.config import get_settings


async def startup(ctx) -> None:
    """Run once at worker boot."""
    ctx["settings"] = get_settings()


async def shutdown(ctx) -> None:
    pass


async def post_call_summary(ctx, call_id: str) -> dict:
    """Generate a 2-3 line summary, classify intent/outcome, persist."""
    from api.jobs.post_call import run_post_call

    return await run_post_call(call_id)


async def notify_new_message(ctx, message_id: str) -> dict:
    from api.jobs.notifications import notify_new_message as handler

    return await handler(message_id)


async def daily_report(ctx) -> dict:
    from api.jobs.daily_report import run as handler

    return await handler()


class WorkerSettings:
    functions = [post_call_summary, notify_new_message, daily_report]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 4
    job_timeout = 300