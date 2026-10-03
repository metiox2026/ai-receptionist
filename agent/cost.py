"""Per-call cost tracking.

Each turn records the LLM token counts and the duration. At end of call we
multiply by per-provider unit prices and persist the totals onto the
`calls` row so the dashboard can show cost-per-call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# Approximate prices (USD). Re-check each provider's pricing page monthly.
LLM_PRICE = {
    # input per token, output per token
    "claude-haiku-4-5": (0.0000008, 0.000004),
    "gemini-2.5-flash-lite": (0.000000075, 0.0000003),
}
STT_PRICE_PER_MIN = 0.0043     # Deepgram Nova-3 (check current pricing)
TTS_PRICE_PER_MIN = 0.015      # Cartesia Sonic-2 (check current pricing)
TEL_PRICE_PER_MIN = 0.007      # Telnyx inbound (check current pricing)


@dataclass
class TurnUsage:
    role: str
    input_tokens: int
    output_tokens: int
    started_at: datetime
    ended_at: datetime

    @property
    def latency_ms(self) -> int:
        return int((self.ended_at - self.started_at).total_seconds() * 1000)


@dataclass
class CostTracker:
    call_id: str
    turns: list[TurnUsage] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    audio_seconds: float = 0.0

    async def record_turn(self, context: Any) -> None:
        """Inspect the LLM context for usage stats. Hook from the pipeline."""
        # Pipecat exposes usage as a frame attribute. The exact location moves
        # between versions — keep this resilient.
        try:
            usage = context.usage or {}
        except AttributeError:
            return
        now = datetime.now(tz=timezone.utc)
        self.turns.append(
            TurnUsage(
                role="assistant",
                input_tokens=int(usage.get("input_tokens", 0)),
                output_tokens=int(usage.get("output_tokens", 0)),
                started_at=now,
                ended_at=now,
            )
        )
        self.total_input_tokens += int(usage.get("input_tokens", 0))
        self.total_output_tokens += int(usage.get("output_tokens", 0))

    def add_audio_seconds(self, seconds: float) -> None:
        self.audio_seconds += seconds

    def estimate(
        self,
        *,
        llm_model: str = "claude-haiku-4-5",
    ) -> dict[str, float]:
        """Return a cost breakdown for the call so far. USD."""
        in_price, out_price = LLM_PRICE.get(llm_model, (0.0, 0.0))
        llm_cost = (
            self.total_input_tokens * in_price
            + self.total_output_tokens * out_price
        )
        minutes = self.audio_seconds / 60.0
        return {
            "llm_usd": round(llm_cost, 6),
            "stt_usd": round(minutes * STT_PRICE_PER_MIN, 6),
            "tts_usd": round(minutes * TTS_PRICE_PER_MIN, 6),
            "telephony_usd": round(minutes * TEL_PRICE_PER_MIN, 6),
            "total_usd": round(
                llm_cost
                + minutes * (STT_PRICE_PER_MIN + TTS_PRICE_PER_MIN + TEL_PRICE_PER_MIN),
                6,
            ),
        }