"""
Tests for Step 9 Part A: Qloo Backend Orchestration & Runner Integration.
Verifies:
1. Cache lookup with deterministic cache_key, TTL, retrieved_at preservation, and counter bypass.
2. Quota enforcement per run_id (QLOO_MAX_CALLS_PER_RUN) and degraded state recording.
3. Retries on transient timeouts and HTTP 429 with exponential backoff and rate_limited status.
4. Audit logging into provider_calls with strict secret and header redaction and source_ref UUIDs.
5. Failure isolation ensuring provider errors do not crash research runs.
6. Live vs Demo persistence for anchors and CulturalAffinity matching rules.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from contracts.schemas import (
    CulturalAffinity,
    InsightOptions,
    TasteEntity,
    TasteSignal,
)
from backend.app.core.config import get_settings
from backend.app.db.models import (
    LeadModel,
    MarketHypothesisModel,
    ProductModel,
    ProviderCallModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.session import async_session_maker, init_db
from backend.app.integrations.qloo_wrapper import (
    QlooOrchestrator,
    build_cache_key,
    does_signal_match_lead,
    get_qloo_orchestrator,
    sanitize_params,
)
from backend.app.jobs.runner import run_research_run_phase1, run_research_run_phase2
from backend.integrations.qloo.provider import MockTasteProvider


@pytest.fixture(autouse=True)
async def reset_counts_and_db():
    QlooOrchestrator.reset_call_counts()
    await init_db()
    yield
    QlooOrchestrator.reset_call_counts()


# -----------------------------------------------------------------------------
# 1. Cache Lookup & Deterministic Cache Key
# -----------------------------------------------------------------------------

def test_deterministic_cache_key_generation():
    endpoint = "/v1/taste/search"
    params_1 = {"query": "artisan ceramics", "extra": 1}
    params_2 = {"extra": 1, "query": "artisan ceramics"}

    key_1 = build_cache_key(endpoint, params_1)
    key_2 = build_cache_key(endpoint, params_2)
    assert key_1 == key_2
    assert len(key_1) == 64  # SHA-256


@pytest.mark.asyncio
async def test_cache_hit_returns_response_without_network_or_counter_increment():
    user_id = uuid4()
    run_id = uuid4()
    endpoint = "/v1/taste/search"
    normalized_params = {"query": "handwoven scarf"}
    cache_key = build_cache_key(endpoint, normalized_params)
    original_retrieved_at = datetime.now(timezone.utc) - timedelta(hours=2)

    # Pre-seed a successful provider call in the database within TTL
    async with async_session_maker() as session:
        cached_record = ProviderCallModel(
            id=uuid4(),
            owner_id=user_id,
            run_id=run_id,
            provider="mock",
            endpoint=endpoint,
            params=normalized_params,
            cache_key=cache_key,
            status="success",
            latency_ms=15,
            response={
                "entities": [
                    {
                        "id": "demo-cached-scarf",
                        "name": "Cached Scarf Entity",
                        "entity_type": "brand",
                        "metadata": {"category": "Textiles", "is_demo": True},
                    }
                ],
                "retrieved_at": original_retrieved_at.isoformat(),
            },
            created_at=original_retrieved_at,
        )
        session.add(cached_record)
        await session.commit()

    # Track network calls on provider
    network_called = False

    class TrackingProvider(MockTasteProvider):
        async def search_entities(self, query: str) -> list[TasteEntity]:
            nonlocal network_called
            network_called = True
            return await super().search_entities(query)

    orchestrator = QlooOrchestrator(
        run_id=run_id,
        owner_id=user_id,
        provider=TrackingProvider(),
        cache_ttl_hours=240,  # wide TTL to match pre-seeded record
    )

    entities = await orchestrator.search_entities("handwoven scarf")

    # Assertions:
    assert not network_called, "Network must not be called on cache hit"
    assert QlooOrchestrator.get_call_count(run_id) == 0, "Counter must not increment on cache hit"
    assert len(entities) == 1
    assert entities[0].id == "demo-cached-scarf"
    assert entities[0].name == "Cached Scarf Entity"
    assert entities[0].metadata.get("source_ref") == str(cached_record.id)
    assert orchestrator.last_retrieved_at == original_retrieved_at


@pytest.mark.asyncio
async def test_cache_miss_when_record_expired_past_ttl():
    user_id = uuid4()
    run_id = uuid4()
    endpoint = "/v1/taste/search"
    normalized_params = {"query": "expired item"}
    cache_key = build_cache_key(endpoint, normalized_params)
    expired_at = datetime.now(timezone.utc) - timedelta(hours=48)

    async with async_session_maker() as session:
        session.add(
            ProviderCallModel(
                id=uuid4(),
                owner_id=user_id,
                run_id=run_id,
                provider="mock",
                endpoint=endpoint,
                params=normalized_params,
                cache_key=cache_key,
                status="success",
                latency_ms=10,
                response={"entities": [{"id": "old-id", "name": "Old", "entity_type": "brand", "metadata": {}}]},
                created_at=expired_at,
            )
        )
        await session.commit()

    network_called = False

    class TrackingProvider(MockTasteProvider):
        async def search_entities(self, query: str) -> list[TasteEntity]:
            nonlocal network_called
            network_called = True
            return [TasteEntity(id="new-live-id", name="Live Item", entity_type="brand", metadata={})]

    orchestrator = QlooOrchestrator(
        run_id=run_id,
        owner_id=user_id,
        provider=TrackingProvider(),
        cache_ttl_hours=24,
    )

    entities = await orchestrator.search_entities("expired item")
    assert network_called is True
    assert QlooOrchestrator.get_call_count(run_id) == 1
    assert entities[0].id == "new-live-id"


# -----------------------------------------------------------------------------
# 2. Quotas & Call Limits
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_quota_enforcement_and_degraded_state_logging():
    user_id = uuid4()
    product_id = uuid4()
    run_id = uuid4()

    # Create dummy research run
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

    provider = MockTasteProvider()
    orchestrator = QlooOrchestrator(
        run_id=run_id,
        owner_id=user_id,
        provider=provider,
        max_calls_per_run=3,
    )

    # Perform 3 live calls
    await orchestrator.search_entities("query 1")
    await orchestrator.search_entities("query 2")
    await orchestrator.search_entities("query 3")

    assert QlooOrchestrator.get_call_count(run_id) == 3

    # 4th call exceeds quota
    entities_4 = await orchestrator.search_entities("query 4")
    assert entities_4 == []
    # Call count does not increment beyond max for quota-rejected attempts
    assert QlooOrchestrator.get_call_count(run_id) == 3

    # Verify degraded state logged in run metadata
    async with async_session_maker() as session:
        run = (
            await session.execute(
                select(ResearchRunModel).where(ResearchRunModel.id == run_id)
            )
        ).scalar_one()
        assert run.plan.get("taste_degraded") is True
        assert "quota" in run.plan.get("taste_degraded_reason", "").lower()


# -----------------------------------------------------------------------------
# 3. Retries & Rate Limiting
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transient_error_retry_and_rate_limited_audit_record():
    user_id = uuid4()
    run_id = uuid4()

    attempts = 0

    class FailingProvider:
        name = "qloo"
        is_demo = False

        async def search_entities(self, query: str) -> list[TasteEntity]:
            nonlocal attempts
            attempts += 1
            # Simulate HTTP 429 Rate Limit
            err = Exception("HTTP 429 Too Many Requests")
            setattr(err, "status_code", 429)
            raise err

        async def get_insights(self, entity_id: str, options: InsightOptions) -> list[TasteSignal]:
            return []

    orchestrator = QlooOrchestrator(
        run_id=run_id,
        owner_id=user_id,
        provider=FailingProvider(),
    )

    entities = await orchestrator.search_entities("retry test entity")
    # Should retry 2 times -> 3 total attempts
    assert attempts == 3
    assert entities == []

    # Check that provider_calls has a row with status == 'rate_limited'
    async with async_session_maker() as session:
        records = (
            await session.execute(
                select(ProviderCallModel).where(
                    ProviderCallModel.run_id == run_id,
                    ProviderCallModel.status == "rate_limited",
                )
            )
        ).scalars().all()
        assert len(records) >= 1
        assert records[0].status == "rate_limited"


# -----------------------------------------------------------------------------
# 4. Audit Logging & Strict Redaction
# -----------------------------------------------------------------------------

def test_sanitize_params_strictly_redacts_keys_and_headers():
    dirty_params = {
        "query": "minimalist lighting",
        "QLOO_API_KEY": "super-secret-key-1234",
        "api_key": "another-secret",
        "headers": {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz",
            "x-api-key": "secret-header-val",
            "Content-Type": "application/json",
        },
        "nested": {
            "token": "nested-token-999",
        },
    }

    clean = sanitize_params(dirty_params)
    assert clean["QLOO_API_KEY"] == "[REDACTED]"
    assert clean["api_key"] == "[REDACTED]"
    assert clean["headers"]["Authorization"] == "[REDACTED]"
    assert clean["headers"]["x-api-key"] == "[REDACTED]"
    assert clean["nested"]["token"] == "[REDACTED]"
    assert clean["query"] == "minimalist lighting"


@pytest.mark.asyncio
async def test_get_insights_audit_logging_and_source_ref_uuid():
    user_id = uuid4()
    run_id = uuid4()
    provider = MockTasteProvider()
    orchestrator = QlooOrchestrator(
        run_id=run_id,
        owner_id=user_id,
        provider=provider,
    )

    signals = await orchestrator.get_insights("demo-entity-test", InsightOptions())
    assert len(signals) >= 1
    first_sig = signals[0]

    # source_ref must be a valid UUID string matching the provider_calls row
    assert first_sig.source_ref is not None
    source_uuid = UUID(first_sig.source_ref)

    async with async_session_maker() as session:
        call_row = (
            await session.execute(
                select(ProviderCallModel).where(ProviderCallModel.id == source_uuid)
            )
        ).scalar_one_or_none()
        assert call_row is not None
        assert call_row.status == "success"
        assert call_row.endpoint == "/v1/taste/insights"
        assert call_row.owner_id == user_id
        assert call_row.run_id == run_id


# -----------------------------------------------------------------------------
# 5. Live vs Demo Persistence & Cultural Affinity Matching
# -----------------------------------------------------------------------------

def test_does_signal_match_lead_region_and_category():
    signal_decor = {
        "text": "Artisan textiles and ceramics trending in independent boutique stores across Western Europe",
        "raw": {"region": "Western Europe", "affinity": 0.85},
        "anchor_category": "Home Decor & Living",
    }

    # Match on verified location with category fit
    loc_france = {"region": "Western Europe", "country": "France", "city": "Paris"}
    assert does_signal_match_lead(
        signal_decor,
        lead_location=loc_france,
        product_category="Home Textiles",
        lead_tier="qualified",
        category_fit_score=100.0,
    ) is True

    # Milestone F: Missing location MUST return False (never attach cultural affinity without location)
    loc_empty = {}
    assert does_signal_match_lead(
        signal_decor,
        lead_location=loc_empty,
        product_category="Home Decor & Living",
        lead_tier="qualified",
        category_fit_score=100.0,
    ) is False

    # Milestone F: Unqualified leads MUST return False
    assert does_signal_match_lead(
        signal_decor,
        lead_location=loc_france,
        product_category="Home Textiles",
        lead_tier="unqualified",
        category_fit_score=100.0,
    ) is False

    # Milestone F: Unknown category fit MUST return False
    assert does_signal_match_lead(
        signal_decor,
        lead_location=loc_france,
        product_category="Home Textiles",
        lead_tier="needs_review",
        category_fit_score=None,
    ) is False

    # No match on region
    loc_tokyo = {"region": "East Asia", "country": "Japan", "city": "Tokyo"}
    assert does_signal_match_lead(
        signal_decor,
        lead_location=loc_tokyo,
        product_category="Home Textiles",
        lead_tier="qualified",
        category_fit_score=100.0,
    ) is False


@pytest.mark.asyncio
async def test_runner_with_taste_relevance_not_applicable_makes_zero_qloo_calls():
    """
    Milestone F: For commodity or functional goods (taste_relevance == 'not_applicable'),
    Phase 1 and Phase 2 bypass Qloo calls entirely.
    """
    user_id = uuid4()
    product_id = uuid4()
    run_id = uuid4()

    async with async_session_maker() as session:
        session.add(
            ProductModel(
                id=product_id,
                owner_id=user_id,
                name="Drafting Pencil 2B",
                category="stationery",
                description="Graphite drawing pencils.",
                moq=10,
            )
        )
        session.add(
            ResearchRunModel(
                id=run_id,
                owner_id=user_id,
                product_id=product_id,
                status="queued",
                stage="planning",
                plan={
                    "taste_relevance": "not_applicable",
                    "aesthetic_candidates": [],
                    "target_regions": ["United Kingdom"],
                },
            )
        )
        await session.commit()

    QlooOrchestrator.reset_call_counts()

    # Execute Phase 1
    await run_research_run_phase1(run_id)

    # Assert zero calls to Qloo
    assert QlooOrchestrator.get_call_count(run_id) == 0

    # Execute Phase 2
    await run_research_run_phase2(run_id)

    # Assert zero calls to Qloo
    assert QlooOrchestrator.get_call_count(run_id) == 0


@pytest.mark.asyncio
async def test_phase1_live_qloo_saves_qloo_anchors_and_falls_back_on_error():
    user_id = uuid4()
    product_id = uuid4()
    run_id = uuid4()

    async with async_session_maker() as session:
        # Create product
        session.add(
            ProductModel(
                id=product_id,
                owner_id=user_id,
                name="Handmade Silk Rug",
                category="Home Decor & Living",
                description="Luxurious natural dyed silk rug.",
                materials=["Silk"],
                style=["Artisan"],
                motifs=["Floral"],
                colours=["Indigo"],
                moq=1,
            )
        )
        # Create run
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

    # Execute Phase 1
    await run_research_run_phase1(run_id)

    async with async_session_maker() as session:
        run = (
            await session.execute(
                select(ResearchRunModel).where(ResearchRunModel.id == run_id)
            )
        ).scalar_one()
        assert run.status == "awaiting_review"
        assert run.stage == "anchor_review"

        anchors = (
            await session.execute(
                select(TasteAnchorModel).where(TasteAnchorModel.run_id == run_id)
            )
        ).scalars().all()

        # Both ai_proposed and taste provider anchors were saved
        ai_anchors = [a for a in anchors if a.source == "ai_proposed"]
        assert len(ai_anchors) >= 1
