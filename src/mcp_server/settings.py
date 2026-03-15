"""Application settings — pydantic-settings with env var binding."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for the SearXNG MCP server.

    All values can be overridden via environment variables prefixed
    with ``MCP_SEARXNG_``.  A ``.env`` file in the working directory
    is loaded automatically.
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_SEARXNG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Server ───────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8101
    workers_count: int = 1
    reload: bool = False
    environment: str = "production"
    log_level: str = "info"

    # ── Auth (optional — incoming MCP requests) ──────────────────
    auth_token: str = ""

    # ── SearXNG instance ─────────────────────────────────────────
    base_url: str = "http://127.0.0.1:8080"
    request_timeout: int = 15
    default_result_count: int = 10
    max_result_count: int = 50

    # ── Observability ────────────────────────────────────────────
    sentry_dsn: str = ""
    sentry_sample_rate: float = 1.0
    opentelemetry_endpoint: str = ""

    # ── Derived ──────────────────────────────────────────────────

    @property
    def auth_enabled(self) -> bool:
        return bool(self.auth_token)


settings = Settings()
