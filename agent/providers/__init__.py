"""Swappable provider configs.

The plan calls for everything to be a config choice rather than a hard-coded
implementation. Each module here wires a specific provider (e.g., Telnyx,
Twilio, ElevenLabs, OpenAI) to the interface the rest of the agent uses.

For now this is a placeholder. Add provider-specific serializers, fallback
LLM configs, and the alternate TTS voices here as we go.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TelnyxAudioSerializer:
    """Pipecat audio serializer for Telnyx media streams.

    Telnyx streams 16-bit signed PCM at 8 kHz by default (μ-law when the
    client requests it). Verify the exact wire format against current Telnyx
    docs and Pipecat's matching serializer.
    """

    sample_rate: int = 8000
    channels: int = 1
    sample_width: int = 2  # 16-bit