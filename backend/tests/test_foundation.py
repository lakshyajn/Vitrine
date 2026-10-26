"""
Foundation Tests for WS2 Step 1.
Verifies /health, /integrations/status, 422 validation errors in Appendix A.5 format,
and log/error scrubbing of secret API keys and Bearer tokens.
"""

from __future__ import annotations

import io
import json
import logging
import os
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field
import pytest

from backend.app.core.config import Settings, get_settings
from backend.app.core.errors import AppError
from backend.app.core.logging import (
    SecretRedactionFilter,
    StructuredJsonFormatter,
    redact_secrets,
)
from backend.app.main import app, create_app


class SampleValidationModel(BaseModel):
    moq: int = Field(..., ge=1)
    name: str


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture ensuring a clean environment without real provider keys."""
    monkeypatch.setenv("QLOO_API_KEY", "")
    monkeypatch.setenv("NEBIUS_API_KEY", "")
    monkeypatch.setenv("TAVILY_API_KEY", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_health_endpoints():
    """Verify /api/v1/health and /health return 200 with request_id header."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test /api/v1/health
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}
        assert "x-request-id" in res.headers
        assert len(res.headers["x-request-id"]) > 0

        # Test root alias /health
        res_alias = await client.get("/health")
        assert res_alias.status_code == 200
        assert res_alias.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_integrations_status_mock_mode(clean_env):
    """Verify /api/v1/integrations/status reports mock mode when credentials are missing."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/integrations/status")
        assert res.status_code == 200
        data = res.json()

        assert data["ai"]["state"] == "mock"
        assert data["search"]["state"] == "mock"
        assert data["taste"]["state"] == "mock"
        assert data["taste"]["provider_name"] == "mock"
        assert data["search"]["provider_name"] == "fixture-tavily"


@pytest.mark.asyncio
async def test_integrations_status_live_mode(monkeypatch):
    """Verify /api/v1/integrations/status reports live mode when keys are present, never leaking keys."""
    qloo_key = "qloo-secret-live-xyz-777"
    nebius_key = "nebius-secret-live-abc-888"
    tavily_key = "tavily-secret-live-def-999"

    monkeypatch.setenv("QLOO_API_KEY", qloo_key)
    monkeypatch.setenv("NEBIUS_API_KEY", nebius_key)
    monkeypatch.setenv("TAVILY_API_KEY", tavily_key)
    get_settings.cache_clear()

    test_app = create_app()

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        res = await client.get("/api/v1/integrations/status")
        assert res.status_code == 200
        data = res.json()

        assert data["ai"]["state"] == "live"
        assert data["search"]["state"] == "live"
        assert data["taste"]["state"] == "live"
        assert data["taste"]["provider_name"] == "qloo"
        assert data["search"]["provider_name"] == "tavily"

        # Security check: secret values must NEVER appear anywhere in response text
        raw_text = res.text
        assert qloo_key not in raw_text
        assert nebius_key not in raw_text
        assert tavily_key not in raw_text


@pytest.mark.asyncio
async def test_validation_error_format_appendix_a5():
    """Verify that a 422 RequestValidationError formats according to Appendix A.5 error envelope."""
    test_app = create_app()

    @test_app.post("/api/v1/test-validation")
    async def sample_endpoint(payload: SampleValidationModel):
        return {"status": "ok"}

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        # Send payload violating moq >= 1 and missing 'name'
        res = await client.post("/api/v1/test-validation", json={"moq": 0})
        assert res.status_code == 422
        data = res.json()

        assert "error" in data
        error = data["error"]
        assert error["code"] == "validation_error"
        assert "moq" in error["details"]
        assert "name" in error["details"]
        assert "request_id" in error
        assert len(error["request_id"]) > 0
        assert res.headers["x-request-id"] == error["request_id"]


def test_log_and_error_scrubbing_of_qloo_key(monkeypatch):
    """Verify that QLOO_API_KEY and Bearer tokens are scrubbed from logs and messages."""
    secret_key = "qloo-secret-live-testkey-1234"
    bearer_token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummytoken"

    monkeypatch.setenv("QLOO_API_KEY", secret_key)
    get_settings.cache_clear()

    # 1. Test redact_secrets function directly
    raw_message = f"Failed request to Qloo with api_key={secret_key} and auth={bearer_token}"
    sanitized = redact_secrets(raw_message)

    assert secret_key not in sanitized
    assert "dummytoken" not in sanitized
    assert "[REDACTED]" in sanitized
    assert "Bearer [REDACTED]" in sanitized

    # 2. Test StructuredJsonFormatter and SecretRedactionFilter
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(SecretRedactionFilter())

    test_logger = logging.getLogger("test_security_logger")
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(handler)

    test_logger.info("Attempted Qloo connection with key: %s and %s", secret_key, bearer_token)
    log_output = stream.getvalue()

    assert secret_key not in log_output
    assert "dummytoken" not in log_output
    assert "[REDACTED]" in log_output

    parsed_log = json.loads(log_output.strip())
    assert secret_key not in parsed_log["message"]
    assert "dummytoken" not in parsed_log["message"]


@pytest.mark.asyncio
async def test_app_error_scrubbing(monkeypatch):
    """Verify that custom AppError redacts configured secrets when returning error response."""
    secret_key = "qloo-secret-sensitive-val-999"
    monkeypatch.setenv("QLOO_API_KEY", secret_key)
    get_settings.cache_clear()

    test_app = create_app()

    @test_app.get("/api/v1/test-app-error")
    async def failing_endpoint():
        raise AppError(
            code="upstream_unavailable",
            message=f"Upstream Qloo failed with key={secret_key}",
            status_code=503,
        )

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        res = await client.get("/api/v1/test-app-error")
        assert res.status_code == 503
        data = res.json()

        assert data["error"]["code"] == "upstream_unavailable"
        assert secret_key not in data["error"]["message"]
        assert "[REDACTED]" in data["error"]["message"]
