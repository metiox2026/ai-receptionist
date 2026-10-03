"""Agent settings loaded from environment variables.

Split from api.config.py because the agent has its own concerns (provider keys,
turn detection, voice IDs) that the API service does not need.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- General ----------
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    api_base_url: str = Field(..., alias="PUBLIC_BASE_URL")
    secret_key: str = Field(..., alias="SECRET_KEY")

    # ---------- Telephony (Telnyx) ----------
    telnyx_api_key: str | None = Field(default=None, alias="TELNYX_API_KEY")
    telnyx_public_key: str | None = Field(default=None, alias="TELNYX_PUBLIC_KEY")
    telnyx_phone_number: str | None = Field(default=None, alias="TELNYX_PHONE_NUMBER")
    telnyx_fallback_number: str | None = Field(default=None, alias="TELNYX_FALLBACK_NUMBER")

    # ---------- STT (Deepgram) ----------
    deepgram_api_key: str | None = Field(default=None, alias="DEEPGRAM_API_KEY")
    deepgram_model: str = Field(default="nova-3", alias="DEEPGRAM_MODEL")
    deepgram_language: str = Field(default="en", alias="DEEPGRAM_LANGUAGE")

    # ---------- TTS (Cartesia) ----------
    cartesia_api_key: str | None = Field(default=None, alias="CARTESIA_API_KEY")
    cartesia_voice_id: str | None = Field(default=None, alias="CARTESIA_VOICE_ID")
    cartesia_model: str = Field(default="sonic-2", alias="CARTESIA_MODEL")

    # ---------- LLM (Anthropic + Gemini fallback) ----------
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-haiku-4-5", alias="ANTHROPIC_MODEL")
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    google_model: str = Field(default="gemini-2.5-flash-lite", alias="GOOGLE_MODEL")

    # ---------- OpenAI-compatible (OpenRouter, etc.) ----------
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # ---------- Limits ----------
    max_call_duration_sec: int = Field(default=600, alias="MAX_CALL_DURATION_SEC")
    max_tool_calls_per_call: int = Field(default=10, alias="MAX_TOOL_CALLS_PER_CALL")
    max_concurrent_calls: int = Field(default=20, alias="MAX_CONCURRENT_CALLS")

    # ---------- Turn detection ----------
    # ms of silence before we consider the caller done. Tune from real data.
    endpointing_ms: int = 400

    # ---------- Provider fallback ----------
    # If the primary LLM fails repeatedly, switch to the fallback for the call.
    primary_llm_failure_threshold: int = 3


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor. Use this instead of instantiating Settings directly."""
    return Settings()