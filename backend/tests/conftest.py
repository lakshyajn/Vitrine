"""
Global Pytest Fixtures for Backend Tests.
Ensures database tables are initialized before each test function.
"""

from __future__ import annotations

import pytest
from backend.app.db.session import init_db


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield
