"""
Verification Test Suite: Step 9 Part B Hardening & Qloo Integration.
Covers:
1. Qloo provider_calls Caching
2. Per-Run Quota Cap
3. Graceful Degradation (Timeout / 401 / 429)
4. Stuck-Run Recovery
5. Rate Limiting
6. Key Redaction in provider_calls, logs, and /api/v1/integrations/status
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import io
import json
import logging
import time
from uuid import UUID, uuid4

from httpx import ASGITransport, AsyncClient
import jwt
import pytest
from sqlalchemy import delete, select

from contracts.schemas import (
    InsightOptions,
    TasteAnchorSource,
    TasteEntity,
    TasteSignal,
)
from backend.app.core.config import get_settings
from backend.app.core.logging import (
    SecretRedactionFilter,
    StructuredJsonFormatter,
    redact_secrets,
)
from backend.app.core.rate_limit import reset_rate_limiters
from backend.app.db.models import (
    ProductModel,
    ProviderCallModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.session import async_session_maker, init_db
from backend.app.integrations.qloo_wrapper import (
    QlooOrchestrator,
    build_cache_key,
    sanitize_params,
)
from backend.app.jobs.runner import (
    recover_stuck_runs,
    run_research_run_phase1,
    run_research_run_phase2,
)
from backend.app.main import app, create_app
from backend.integrations.qloo.provider import MockTasteProvider

JWT_SECRET = "jwt-secret-qloo-and-hardening-test-key-999"


@pytest.fixture(autouse=True)
async def test_suite_setup(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    get_settings.cache_clear()
    reset_rate_limiters()
    QlooOrchestrator.reset_call_counts()
    await init_db()
    yield
    reset_rate_limiters()
    QlooOrchestrator.reset_call_counts()
    get_settings.cache_clear()


def make_auth_header(user_id: UUID | None = None) -> dict[str, str]:
    uid = user_id or uuid4()
    payload = {
        "sub": str(uid),
        "email": "artisan@qloo-hardening.test",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    _s = get_settings()
    if _s.supabase_url and "iss" not in payload:
        payload["iss"] = f"{_s.supabase_url.rstrip('/')}/auth/v1"
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. Qloo provider_calls Caching
# ==============================================================================

@pytest.mark.asyncio
async def test_qloo_provider_calls_caching():
    """
    Calling QlooOrchestrator twice with identical (endpoint, params)
    hits the cache on the second call, returns the original retrieved_at,
    and only invokes the underlying provider once.
    """
    user_id = uuid4()
    run_id = uuid4()
    provider_call_count = 0

    class CountingProvider(MockTasteProvider):
        async def search_entities(self, query: str) -> list[TasteEntity]:
            nonlocal provider_call_count
            provider_call_count += 1
            return [
                TasteEntity(
                    id="entity-ceramics-1",
                    name="Handmade Ceramic Studio",
                    entity_type="brand",
                    metadata={"category": "Home Decor", "is_demo": True},
                )
            ]

    provider = CountingProvider()
    orchestrator = QlooOrchestrator(
        run_id=run_id,
        owner_id=user_id,
        provider=provider,
        cache_ttl_hours=24,
    )

    query_str = "Artisan Ceramics"

    # Call 1: Cache miss -> invokes provider, logs to provider_calls
    entities_1 = await orchestrator.search_entities(query_str)
    assert len(entities_1) == 1
    assert entities_1[0].name == "Handmade Ceramic Studio"
    assert provider_call_count == 1
    assert QlooOrchestrator.get_call_count(run_id) == 1
    original_retrieved_at = orchestrator.last_retrieved_at
    assert original_retrieved_at is not None

    # Verify 1 record written to provider_calls
    async with async_session_maker() as session:
        calls = (
            await session.execute(
                select(ProviderCallModel).where(ProviderCallModel.run_id == run_id)
            )
        ).scalars().all()
        assert len(calls) == 1
        assert calls[0].status == "success"

    # Call 2: Identical query -> Cache hit
    entities_2 = await orchestrator.search_entities(query_str)
    assert len(entities_2) == 1
    assert entities_2[0].name == "Handmade Ceramic Studio"

    # Provider was NOT invoked a second time
    assert provider_call_count == 1
    # Run call counter was NOT incremented on cache hit
    assert QlooOrchestrator.get_call_count(run_id) == 1
    # Original retrieved_at is preserved
    assert orchestrator.last_retrieved_at == original_retrieved_at

    # Still only 1 record in provider_calls
    async with async_session_maker() as session:
        calls_after = (
            await session.execute(
                select(ProviderCallModel).where(ProviderCallModel.run_id == run_id)
            )
        ).scalars().all()
        assert len(calls_after) == 1


# ==============================================================================
# 2. Per-Run Quota Cap
# ==============================================================================

@pytest.mark.asyncio
async def test_per_run_quota_cap(monkeypatch):
    """
    Setting QLOO_MAX_CALLS_PER_RUN=2 blocks the 3rd call in the same run
    without crashing the run.
    """
    monkeypatch.setenv("QLOO_MAX_CALLS_PER_RUN", "2")
    get_settings.cache_clear()

    user_id = uuid4()
    run_id = uuid4()
    product_id = uuid4()

    async with async_session_maker() as session:
        session.add(
            ResearchRunModel(
                id=run_id,
                owner_id=user_id,
                product_id=product_id,
                status="running",
                stage="anchor_proposal",
                inputs={},
                plan={},
                provider_modes={"taste": "mock"},
            )
        )
        await session.commit()

    orchestrator = QlooOrchestrator(
        run_id=run_id,
        owner_id=user_id,
        provider=MockTasteProvider(),
    )
    assert orchestrator.max_calls_per_run == 2

    # Call 1: Allowed
    res1 = await orchestrator.search_entities("botanical linen")
    assert len(res1) >= 1
    assert QlooOrchestrator.get_call_count(run_id) == 1

    # Call 2: Allowed
    res2 = await orchestrator.search_entities("ceramic bowls")
    assert len(res2) >= 1
    assert QlooOrchestrator.get_call_count(run_id) == 2

    # Call 3: Blocked by quota cap without crashing
    res3 = await orchestrator.search_entities("wool throws")
    assert res3 == []
    assert QlooOrchestrator.get_call_count(run_id) == 2

    # Verify degraded state logged in run metadata
    async with async_session_maker() as session:
        run = (
            await session.execute(
                select(ResearchRunModel).where(ResearchRunModel.id == run_id)
            )
        ).scalar_one()
        assert run.plan.get("taste_degraded") is True
        assert "quota" in run.plan.get("taste_degraded_reason", "").lower()


# ==============================================================================
# 3. Graceful Degradation (Timeout / 401 / 429)
# ==============================================================================

@pytest.mark.parametrize(
    "error_factory,err_name",
    [
        (lambda: asyncio.TimeoutError("Upstream timeout from Qloo"), "timeout"),
        (lambda: Exception("HTTP 401 Unauthorized: Invalid API key"), "401"),
        (lambda: Exception("HTTP 429 Too Many Requests: Rate limit reached"), "429"),
    ],
)
@pytest.mark.asyncio
async def test_graceful_degradation_on_qloo_errors(monkeypatch, error_factory, err_name):
    """
    When the Qloo provider raises a timeout, 401, or 429 error,
    the research run does NOT fail; it falls back to ai_proposed anchors and completes.
    """
    monkeypatch.setenv("QLOO_CACHE_TTL_HOURS", "0")
    get_settings.cache_clear()

    user_id = uuid4()
    product_id = uuid4()
    run_id = uuid4()

    async with async_session_maker() as session:
        await session.execute(delete(ProviderCallModel))
        session.add(
            ProductModel(
                id=product_id,
                owner_id=user_id,
                name=f"Degradation Cushion {uuid4().hex[:8]}",
                category="Home Textiles",
                description="Natural plant-dyed cushion with heritage floral motifs.",
                materials=["Cotton"],
                style=["Artisan"],
                motifs=["botanical motifs"],
                colours=["terracotta", "indigo"],
                moq=20,
            )
        )
        session.add(
            ResearchRunModel(
                id=run_id,
                owner_id=user_id,
                product_id=product_id,
                status="queued",
                stage="planning",
                inputs={},
                provider_modes={"taste": "qloo"},
            )
        )
        await session.commit()

    # Create a provider that raises the specific error
    class ErroringProvider:
        name = "qloo"
        is_demo = False

        async def search_entities(self, query: str) -> list[TasteEntity]:
            raise error_factory()

        async def get_insights(self, entity_id: str, options: InsightOptions) -> list[TasteSignal]:
            raise error_factory()

    # Monkeypatch get_taste_provider to return the erroring provider
    monkeypatch.setattr(
        "backend.app.integrations.qloo_wrapper.get_taste_provider",
        lambda: ErroringProvider(),
    )

    # 1. Execute Phase 1
    await run_research_run_phase1(run_id)

    # Phase 1 must NOT fail; transitions to awaiting_review
    async with async_session_maker() as session:
        r1 = (
            await session.execute(
                select(ResearchRunModel).where(ResearchRunModel.id == run_id)
            )
        ).scalar_one()
        assert r1.status == "awaiting_review"
        assert r1.stage == "anchor_review"

        # Verify fallback to ai_proposed anchors
        anchors = (
            await session.execute(
                select(TasteAnchorModel).where(TasteAnchorModel.run_id == run_id)
            )
        ).scalars().all()
        assert len(anchors) >= 1
        for a in anchors:
            assert a.source == TasteAnchorSource.AI_PROPOSED.value

        # Confirm the first anchor to proceed to Phase 2
        anchors[0].status = "confirmed"
        await session.commit()

    # 2. Execute Phase 2
    await run_research_run_phase2(run_id)

    # Phase 2 must complete cleanly despite upstream Qloo error
    async with async_session_maker() as session:
        r2 = (
            await session.execute(
                select(ResearchRunModel).where(ResearchRunModel.id == run_id)
            )
        ).scalar_one()
        assert r2.status == "completed"
        assert r2.stage == "done"
        assert r2.finished_at is not None


# ==============================================================================
# 4. Stuck-Run Recovery
# ==============================================================================

@pytest.mark.asyncio
async def test_stuck_run_recovery():
    """
    A running run with an expired heartbeat_at is marked failed with
    error.code == "internal_error" and error.message == "interrupted" on startup,
    while an awaiting_review run remains awaiting_review.
    """
    user_id = uuid4()
    product_id = uuid4()

    now = datetime.now(timezone.utc)
    expired_hb = now - timedelta(seconds=200)  # > 120s timeout

    stuck_run_id = uuid4()
    awaiting_run_id = uuid4()

    async with async_session_maker() as session:
        session.add(
            ProductModel(
                id=product_id,
                owner_id=user_id,
                name="Block Print Runner",
                category="Home Textiles",
                description="Test Runner",
                moq=1,
            )
        )
        # Stuck run in 'running' state
        session.add(
            ResearchRunModel(
                id=stuck_run_id,
                owner_id=user_id,
                product_id=product_id,
                status="running",
                stage="discovery",
                heartbeat_at=expired_hb,
                created_at=expired_hb,
            )
        )
        # Normal run in 'awaiting_review' state with expired heartbeat
        session.add(
            ResearchRunModel(
                id=awaiting_run_id,
                owner_id=user_id,
                product_id=product_id,
                status="awaiting_review",
                stage="anchor_review",
                heartbeat_at=expired_hb,
                created_at=expired_hb,
            )
        )
        await session.commit()

    # Execute recovery function called during startup
    recovered_ids = await recover_stuck_runs()
    assert stuck_run_id in recovered_ids
    assert awaiting_run_id not in recovered_ids

    async with async_session_maker() as session:
        stuck_run = (
            await session.execute(
                select(ResearchRunModel).where(ResearchRunModel.id == stuck_run_id)
            )
        ).scalar_one()
        assert stuck_run.status == "failed"
        assert stuck_run.error == {"code": "internal_error", "message": "interrupted"}
        assert stuck_run.finished_at is not None

        awaiting_run = (
            await session.execute(
                select(ResearchRunModel).where(ResearchRunModel.id == awaiting_run_id)
            )
        ).scalar_one()
        assert awaiting_run.status == "awaiting_review"
        assert awaiting_run.stage == "anchor_review"


# ==============================================================================
# 5. Rate Limiting
# ==============================================================================

@pytest.mark.asyncio
async def test_per_user_rate_limiting_returns_429():
    """
    Exceeding the per-user rate limit on POST /api/v1/research-runs
    returns HTTP 429 with error.code == "rate_limited".
    """
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create product
        prod_res = await client.post(
            "/api/v1/products",
            json={"name": "Linen Napkins", "category": "Home Textiles", "description": "Test", "moq": 10},
            headers=headers,
        )
        assert prod_res.status_code == 201
        prod_id = prod_res.json()["id"]

        # 10 calls succeed (within 10 req/min limit)
        for _ in range(10):
            res = await client.post(
                "/api/v1/research-runs",
                json={"product_id": prod_id, "inputs": {}},
                headers=headers,
            )
            assert res.status_code == 201

        # 11th call breaches limit -> HTTP 429
        limit_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": prod_id, "inputs": {}},
            headers=headers,
        )
        assert limit_res.status_code == 429
        data = limit_res.json()
        assert "error" in data
        assert data["error"]["code"] == "rate_limited"
        assert "Too many requests" in data["error"]["message"]


# ==============================================================================
# 6. Key Redaction
# ==============================================================================

@pytest.mark.asyncio
async def test_key_redaction_in_provider_calls_logs_and_status(monkeypatch):
    """
    Verify that QLOO_API_KEY never appears in provider_calls.params, logs,
    or /api/v1/integrations/status responses.
    """
    secret_key = "qloo-secret-never-leak-998877"
    monkeypatch.setenv("QLOO_API_KEY", secret_key)
    get_settings.cache_clear()

    # 1. Verify /api/v1/integrations/status never leaks QLOO_API_KEY
    test_app = create_app()
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        status_res = await client.get("/api/v1/integrations/status")
        assert status_res.status_code == 200
        assert secret_key not in status_res.text
        data = status_res.json()
        assert data["taste"]["state"] == "live"
        assert data["taste"]["provider_name"] == "qloo"

    # 2. Verify provider_calls.params redacts QLOO_API_KEY and Authorization headers
    user_id = uuid4()
    run_id = uuid4()
    endpoint = "/v1/taste/search"
    dirty_params = {
        "query": "botanical cotton",
        "api_key": secret_key,
        "QLOO_API_KEY": secret_key,
        "headers": {
            "Authorization": f"Bearer {secret_key}",
            "x-api-key": secret_key,
        },
        "nested": {
            "token": secret_key,
        },
    }

    sanitized = sanitize_params(dirty_params)
    sanitized_str = json.dumps(sanitized)
    assert secret_key not in sanitized_str
    assert "[REDACTED]" in sanitized_str

    # Write to database and verify row does not contain secret_key
    async with async_session_maker() as session:
        call_id = uuid4()
        session.add(
            ProviderCallModel(
                id=call_id,
                owner_id=user_id,
                run_id=run_id,
                provider="qloo",
                endpoint=endpoint,
                params=sanitized,
                cache_key="test-key",
                status="success",
                latency_ms=25,
                response={"entities": []},
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()

        row = (
            await session.execute(
                select(ProviderCallModel).where(ProviderCallModel.id == call_id)
            )
        ).scalar_one()
        raw_db_params = json.dumps(row.params)
        assert secret_key not in raw_db_params

    # 3. Verify logging scrubbing
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(SecretRedactionFilter())

    test_logger = logging.getLogger("test_redaction_logger")
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(handler)

    test_logger.info("Attempted Qloo request with key: %s", secret_key)
    output = stream.getvalue()
    assert secret_key not in output
    assert "[REDACTED]" in output
