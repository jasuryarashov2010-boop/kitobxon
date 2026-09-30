from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    webhook_base_url: str | None = Field(default=None, alias="WEBHOOK_BASE_URL")
    render_external_url: str | None = Field(default=None, alias="RENDER_EXTERNAL_URL")
    webhook_path: str = Field(default="/telegram/webhook", alias="WEBHOOK_PATH")
    webhook_secret: str = Field(alias="WEBHOOK_SECRET")
    bot_username: str = Field(alias="BOT_USERNAME")
    admin_ids_raw: str = Field(alias="ADMIN_IDS")
    channel_id: str = Field(alias="CHANNEL_ID")
    channel_username: str = Field(default="", alias="CHANNEL_USERNAME")
    channel_url: str = Field(alias="CHANNEL_URL")
    app_name: str = Field(default="Kitobxon Tavsiya Bot", alias="APP_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def admin_ids(self) -> set[int]:
        values: set[int] = set()
        for item in self.admin_ids_raw.split(","):
            item = item.strip()
            if item:
                values.add(int(item))
        return values

    @property
    def webhook_url(self) -> str:
        base = self.webhook_base_url or self.render_external_url
        if not base:
            raise ValueError("Set WEBHOOK_BASE_URL locally or use Render's RENDER_EXTERNAL_URL")
        return f"{base.rstrip('/')}/{self.webhook_path.lstrip('/')}"

    @property
    def async_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql+asyncpg://"):
            return url
        raise ValueError("DATABASE_URL must be a PostgreSQL URL")

    @property
    def normalized_redis_url(self) -> str:
        # redis-py accepts redis:// and rediss:// directly.
        parsed = urlsplit(self.redis_url)
        if parsed.scheme not in {"redis", "rediss"}:
            raise ValueError("REDIS_URL must be redis:// or rediss://")
        return urlunsplit(parsed)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
