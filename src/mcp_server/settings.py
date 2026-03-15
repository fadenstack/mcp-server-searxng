"""Application settings — split into infrastructure (static) and provider (dynamic).

Infrastructure settings are loaded once at startup via environment variables
and are not changeable at runtime.

Provider settings can be updated at runtime through the settings REST API
and are persisted to disk.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from mcp_server.services.settings_manager import SettingsManager


# ── Infrastructure settings (static, env-only) ──────────────────


class InfraSettings(BaseSettings):
    """Fixed infrastructure config — set via env vars, read-only at runtime."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_SEARXNG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8101
    workers_count: int = 1
    reload: bool = False
    environment: str = "production"
    log_level: str = "info"
    auth_token: str = ""
    sentry_dsn: str = ""
    sentry_sample_rate: float = 1.0
    opentelemetry_endpoint: str = ""

    @property
    def auth_enabled(self) -> bool:
        return bool(self.auth_token)


# ── Provider settings (dynamic, runtime-mutable) ────────────────


class SearXNGProviderSettings(BaseModel):
    """SearXNG provider config — mutable at runtime via REST API."""

    base_url: str = Field(
        default="http://127.0.0.1:8080",
        title="SearXNG Base URL",
        description="Base URL of the SearXNG instance",
    )
    request_timeout: int = Field(
        default=15,
        title="Request Timeout",
        description="HTTP request timeout in seconds",
        ge=1,
        le=120,
    )
    default_result_count: int = Field(
        default=10,
        title="Default Result Count",
        description="Number of results returned by default",
        ge=1,
        le=100,
    )
    max_result_count: int = Field(
        default=50,
        title="Max Result Count",
        description="Maximum number of results allowed per request",
        ge=1,
        le=200,
    )


# ── Singletons ──────────────────────────────────────────────────

settings = InfraSettings()

provider_settings_manager: SettingsManager[SearXNGProviderSettings] = SettingsManager(
    schema_class=SearXNGProviderSettings,
    env_prefix="MCP_SEARXNG_",
    persist_path="data/settings.json",
)
