"""
Core Configuration Module.
Loads environment variables using pydantic-settings.
Missing optional keys signal mock/fixture mode and never crash startup.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT_DIR = Path(__file__).resolve().parents[3]
_ENV_FILE = _ROOT_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_env: str = "dev"
    allow_dev_tokens: bool = True

    # Supabase & Database
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    database_url: str = "sqlite+aiosqlite:///./vitrine.db"

    # AI Provider 1 (Ultra 550B - Deep Reasoning & Outreach)
    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1"
    nebius_api_key: str | None = None
    nebius_token_factory_api_key: str | None = None
    nebius_model_id: str = "nvidia/nemotron-3-ultra-550b-a55b"
    nebius_fallback_base_url: str = "https://integrate.api.nvidia.com/v1"

    # AI Provider 2 (Super VL 120B - Fast Extraction & Lead Assessment)
    nemotron_fast_base_url: str = "https://api.tokenfactory.nebius.com/v1"
    nemotron_fast_api_key: str | None = None
    nemotron_fast_model_id: str = "nvidia/nemotron-3.5-super-vl-120b-a12b"
    nemotron_fast_fallback_base_url: str = "https://integrate.api.nvidia.com/v1"

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
    max_leads_per_run: int = 6

    # Network / CORS
    cors_origins: Any = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v_clean = v.strip()
            if v_clean.startswith("[") and v_clean.endswith("]"):
                try:
                    import json
                    parsed = json.loads(v_clean)
                    if isinstance(parsed, list):
                        return [str(o).strip() for o in parsed if str(o).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def is_ai_live(self) -> bool:
        key = self.nebius_api_key or self.nebius_token_factory_api_key or self.nemotron_fast_api_key
        return bool(key and key.strip())

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
            self.nebius_token_factory_api_key,
            self.nemotron_fast_api_key,
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


# Singleton instance for backwards-compatible imports
settings = get_settings()
