import pytest
from backend.app.core.config import get_settings
from backend.app.core.errors import AppError
from backend.research.pipeline import get_research_pipeline
from backend.ai.service import get_ai_service

def test_research_pipeline_blocks_fixtures_in_production(monkeypatch):
    """Ensure production environment raises AppError rather than fabricating fake retailers."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    get_settings.cache_clear()

    with pytest.raises(AppError) as exc_info:
        get_research_pipeline()
    assert exc_info.value.code == "upstream_unavailable"

    get_settings.cache_clear()

def test_ai_service_blocks_fixtures_in_production(monkeypatch):
    """Ensure production environment raises AppError rather than fabricating fake AI outputs."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("NEBIUS_API_KEY", "")
    monkeypatch.setenv("NEMOTRON_FAST_API_KEY", "")
    get_settings.cache_clear()

    with pytest.raises(AppError) as exc_info:
        get_ai_service()
    assert exc_info.value.code == "ai_generation_failed"

    get_settings.cache_clear()

