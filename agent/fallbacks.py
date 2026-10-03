"""Provider fallback logic.

When the primary provider fails N times in a single call, swap to the
fallback. The wrapper preserves the Pipecat LLM service interface so the
pipeline does not need to know.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog

logger = structlog.get_logger()


class FallbackLLM:
    """Wrap a primary and fallback LLM service. Use the primary; if it fails
    `failure_threshold` times within the call, swap permanently to the
    fallback for the rest of the call.
    """

    def __init__(
        self,
        *,
        primary: Any,
        fallback: Any | None,
        failure_threshold: int,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.failure_threshold = failure_threshold
        self.failures = 0
        self._active = primary
        self._swapped_at: float | None = None

    @property
    def active(self) -> Any:
        return self._active

    @property
    def swapped(self) -> bool:
        return self._swapped_at is not None

    def record_failure(self) -> None:
        self.failures += 1
        if (
            not self.swapped
            and self.failures >= self.failure_threshold
            and self.fallback is not None
        ):
            logger.warning(
                "llm_fallback_swap",
                failures=self.failures,
                threshold=self.failure_threshold,
            )
            self._active = self.fallback
            self._swapped_at = time.time()


def with_fallback(*, primary: Any, failure_threshold: int) -> FallbackLLM:
    """Construct a FallbackLLM. The fallback service is created lazily so a
    missing key does not crash startup — we just log a warning instead.
    """
    from agent.config import get_settings

    settings = get_settings()
    fallback: Any | None = None
    if settings.google_api_key:
        # Lazy import so we don't pull google-generativeai at startup if it's
        # not configured.
        try:
            from pipecat.services.google import GoogleLLMService

            fallback = GoogleLLMService(
                api_key=settings.google_api_key,
                model=settings.google_model,
                max_tokens=128,
                temperature=0.3,
            )
        except Exception:
            logger.exception("fallback_llm_init_failed")

    return FallbackLLM(
        primary=primary,
        fallback=fallback,
        failure_threshold=failure_threshold,
    )