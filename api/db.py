"""Database session management.

The API and worker share this. The agent connects through a separate asyncpg
URL when it needs to read/write directly.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from api.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for SQLAlchemy 2.0 models."""


_settings = get_settings()
engine = create_async_engine(_settings.database_url, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a session and rolls back on exception."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def healthcheck() -> dict[str, Any]:
    """Return DB and Redis reachability. Used by /healthz."""
    from redis.asyncio import Redis

    out: dict[str, Any] = {"db": False, "redis": False}
    try:
        async with engine.connect() as conn:
            await conn.exec_driver_sql("SELECT 1")
        out["db"] = True
    except Exception as exc:  # pragma: no cover
        out["db_error"] = repr(exc)
    try:
        r = Redis.from_url(_settings.redis_url, decode_responses=True)
        out["redis"] = await r.ping()
        await r.close()
    except Exception as exc:  # pragma: no cover
        out["redis_error"] = repr(exc)
    return out