"""Runtime configuration for the Telegram bot."""

from __future__ import annotations

from pydantic import Field, HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from shared.enums import Locale


class BotSettings(BaseSettings):
    """Environment-driven settings.

    Values are loaded from the process environment and, if present, from a
    ``.env`` file in the current working directory.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    bot_token: SecretStr = Field(..., description="Telegram Bot API token.")
    backend_url: HttpUrl = Field(..., description="Base URL of the backend service.")
    bot_api_token: SecretStr = Field(
        ..., description="Shared secret sent as X-Bot-Token header to backend."
    )
    admin_api_token: SecretStr | None = Field(
        default=None,
        description="Shared secret sent as X-Admin-Token header for admin endpoints.",
    )
    bot_admin_ids: list[int] = Field(
        default_factory=list,
        description="Telegram user ids that may access admin commands.",
    )
    default_locale: Locale = Field(default=Locale.RU)
    log_level: str = Field(default="INFO")
    environment: str = Field(default="dev")
    backend_request_timeout: float = Field(default=10.0)

    @field_validator("bot_admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> object:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [int(part.strip()) for part in value.split(",") if part.strip()]
        return value

    @property
    def backend_base_url(self) -> str:
        """Backend URL without a trailing slash."""
        return str(self.backend_url).rstrip("/")


def load_settings() -> BotSettings:
    """Instantiate :class:`BotSettings` from the environment."""
    return BotSettings()
