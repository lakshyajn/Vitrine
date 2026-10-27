"""
Global Pytest Fixtures for Backend Tests.
Ensures database tables are initialized before each test function.
"""

from __future__ import annotations

import asyncio
import pytest
from backend.app.db.session import init_db


@pytest.fixture(autouse=True)
def clean_test_env(monkeypatch):
    """Ensure pytest tests default to fixture/mock stubs to prevent slow live network calls and quota drain."""
    monkeypatch.setenv("QLOO_API_KEY", "")
    monkeypatch.setenv("NEBIUS_API_KEY", "")
    monkeypatch.setenv("NEMOTRON_FAST_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("ALLOW_DEV_TOKENS", "true")
    try:
        from backend.app.core.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass
    yield
    try:
        from backend.app.core.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
async def setup_test_db():
    from backend.app.db.models import Base
    from backend.app.db.session import engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Await any pending background tasks (Phase 1 / Phase 2 runners) before next test runs
    pending = [
        t for t in asyncio.all_tasks()
        if t is not asyncio.current_task() and not t.done()
    ]
    if pending:
        try:
            await asyncio.wait(pending, timeout=1.0)
        except Exception:
            pass
