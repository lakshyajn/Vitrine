"""
Core Configuration Module.
Loads environment variables using pydantic-settings.
Missing optional keys signal mock/fixture mode and never crash startup.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_env: str = "dev"

    # Supabase & Database
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    database_url: str = "sqlite+aiosqlite:///:memory:"

    # AI Provider (Nebius / Nemotron)
    nebius_api_key: str | None = None
    nebius_model_id: str = "meta/llama-3.1-70b-instruct"

    # Research Provider (Tavily)
    tavily_api_key: str | None = None

    # Taste Provider (Qloo)
    qloo_api_key: str | None = None
    qloo_base_url: str | None = None
    qloo_timeout_seconds: int = 15
    qloo_max_calls_per_run: int = 20
    qloo_cache_ttl_hours: int = 24

    # Execution Limits
    run_max_seconds: int = 600
    stage_timeout_seconds: int = 120
    max_leads_per_run: int = 40

    # Network / CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["http://localhost:5173"]

    @property
    def is_ai_live(self) -> bool:
        return bool(self.nebius_api_key and self.nebius_api_key.strip())

    @property
    def is_search_live(self) -> bool:
        return bool(self.tavily_api_key and self.tavily_api_key.strip())

    @property
    def is_taste_live(self) -> bool:
        return bool(self.qloo_api_key and self.qloo_api_key.strip())

    def get_configured_secrets(self) -> set[str]:
        """Return a set of all non-empty configured secret strings to be redacted."""
        secrets: set[str] = set()
        candidates = [
            self.supabase_service_role_key,
            self.supabase_jwt_secret,
            self.nebius_api_key,
            self.tavily_api_key,
            self.qloo_api_key,
        ]
        for c in candidates:
            if c and isinstance(c, str) and len(c.strip()) >= 4:
                secrets.add(c.strip())
        return secrets


@lru_cache
def get_settings() -> Settings:
    return Settings()
