"""API settings loaded from environment."""

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

    environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = Field(..., alias="SECRET_KEY")

    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")

    public_base_url: str = Field(..., alias="PUBLIC_BASE_URL")

    # Calendar
    google_calendar_client_id: str | None = Field(default=None, alias="GOOGLE_CALENDAR_CLIENT_ID")
    google_calendar_client_secret: str | None = Field(
        default=None, alias="GOOGLE_CALENDAR_CLIENT_SECRET"
    )
    google_calendar_redirect_uri: str | None = Field(
        default=None, alias="GOOGLE_CALENDAR_REDIRECT_URI"
    )
    google_calendar_default_id: str = Field(default="primary", alias="GOOGLE_CALENDAR_DEFAULT_ID")

    # Notifications
    telegram_bot_token: str | None = Field(default=None, alias="TELEGRAM_BOT_TOKEN")
    telegram_default_chat_id: str | None = Field(default=None, alias="TELEGRAM_DEFAULT_CHAT_ID")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(
        default="Receptionist <noreply@example.com>", alias="SMTP_FROM"
    )

    # Storage
    recordings_bucket: str = Field(default="receptionist-recordings", alias="RECORDINGS_BUCKET")
    recordings_endpoint: str | None = Field(default=None, alias="RECORDINGS_S3_ENDPOINT")
    recordings_region: str = Field(default="auto", alias="RECORDINGS_S3_REGION")
    recordings_access_key: str | None = Field(default=None, alias="RECORDINGS_ACCESS_KEY")
    recordings_secret_key: str | None = Field(default=None, alias="RECORDINGS_SECRET_KEY")
    recordings_public_url: str | None = Field(default=None, alias="RECORDINGS_PUBLIC_URL")

    # Limits
    max_daily_spend_usd: float = Field(default=50.0, alias="MAX_DAILY_SPEND_USD")


@lru_cache
def get_settings() -> Settings:
    return Settings()