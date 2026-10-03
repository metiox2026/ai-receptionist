"""Audio format conversions for the Twilio phone integration.

Twilio's Media Streams default to **PCMU (G.711 mu-law) 8 kHz mono**.
The voice pipeline (Deepgram, Cartesia) wants **L16 16 kHz mono**, so we
decode mulaw → linear, resample 8 k → 16 k on the way in, and reverse
on the way out.

  inbound:  Twilio (mulaw 8k) -> mulaw_to_pcm16 -> upsample 8k->16k -> Deepgram
  outbound: Cartesia (L16 16k) -> downsample 16k->8k -> pcm16_to_mulaw -> Twilio

The codec table is built once at import. Resampling is linear (each input
sample plus the midpoint with the next), which is fine for voice — better
than a boxcar average, simpler than a polyphase filter.
"""

from __future__ import annotations

import numpy as np


_MULAW_BIAS = 0x84  # 132 — the standard G.711 mu-law bias
_MULAW_MAX = 32635   # 32767 - BIAS; clamp value after the bias is added


def _build_decode_table() -> np.ndarray:
    """256-entry lookup: uint8 mulaw -> int16 linear PCM."""
    table = np.empty(256, dtype=np.int16)
    for i in range(256):
        v = (~i) & 0xFF
        sign = (v & 0x80) >> 7
        exp_ = (v & 0x70) >> 4
        mant = v & 0x0F
        sample = (((mant << 3) | 0x84) << exp_) - 0x84
        if sign:
            sample = -sample
        # Clamp to int16 range (shouldn't be needed for valid mulaw)
        if sample > 32767:
            sample = 32767
        elif sample < -32768:
            sample = -32768
        table[i] = sample
    return table


_DECODE_TABLE = _build_decode_table()


def mulaw_to_pcm16(data: bytes) -> np.ndarray:
    """Decode mulaw 8-bit to int16 linear PCM (numpy array)."""
    if not data:
        return np.empty(0, dtype=np.int16)
    return _DECODE_TABLE[np.frombuffer(data, dtype=np.uint8)]


def pcm16_to_mulaw(samples: np.ndarray) -> bytes:
    """Encode int16 linear PCM to mulaw 8-bit (bytes)."""
    if len(samples) == 0:
        return b""
    pcm = samples.astype(np.int32)
    sign_bit = (pcm < 0).astype(np.uint8) << 7
    pcm = np.abs(pcm)
    pcm = np.minimum(pcm + _MULAW_BIAS, _MULAW_MAX)

    # Find leading exponent: largest e in [1..7] such that pcm >= 2^(e+7).
    exp_ = np.zeros(pcm.shape, dtype=np.uint8)
    for e in range(7, 0, -1):
        exp_ = np.where(
            (exp_ == 0) & (pcm >= (1 << (e + 7))),
            np.uint8(e),
            exp_,
        )
    mant = (pcm >> (exp_.astype(np.int32) + 3)) & 0x0F
    encoded = (~(sign_bit | (exp_ << 4) | mant.astype(np.uint8))) & 0xFF
    return encoded.astype(np.uint8).tobytes()


def upsample_8k_to_16k(samples: np.ndarray) -> np.ndarray:
    """Linear interpolation: 8 kHz -> 16 kHz (doubles the length)."""
    n = len(samples)
    if n == 0:
        return np.empty(0, dtype=np.int16)
    if n == 1:
        return np.array([samples[0], samples[0]], dtype=np.int16)
    out = np.empty(n * 2, dtype=np.int16)
    out[0::2] = samples
    # Midpoint between adjacent samples
    mid = (samples[:-1].astype(np.int32) + samples[1:].astype(np.int32)) // 2
    out[1:-1:2] = mid.astype(np.int16)
    out[-1] = samples[-1]
    return out


def downsample_16k_to_8k(samples: np.ndarray) -> np.ndarray:
    """Average adjacent pairs: 16 kHz -> 8 kHz (halves the length)."""
    n = (len(samples) // 2) * 2
    if n < 2:
        return np.empty(0, dtype=np.int16)
    pairs = samples[:n].reshape(-1, 2).astype(np.int32)
    return ((pairs[:, 0] + pairs[:, 1]) // 2).astype(np.int16)
