"""
Global Pytest Fixtures for Backend Tests.
Ensures database tables are initialized before each test function.
"""

from __future__ import annotations

import asyncio
import pytest
from backend.app.db.session import init_db


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
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
