"""
Tests for Step 9 Part B: Day 4 Hardening, Stuck-Run Recovery, Rate Limiting, and Demo Seed.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import time
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
import jwt
import pytest
from sqlalchemy import select

from backend.app.core.config import get_settings
from backend.app.core.rate_limit import reset_rate_limiters
from backend.app.db.models import (
    LeadModel,
    OutreachDraftModel,
    ProductModel,
    ProfileModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.seed_demo import seed_demo_data
from backend.app.db.session import async_session_maker, init_db
from backend.app.jobs.runner import recover_stuck_runs
from backend.app.main import app

JWT_SECRET = "test-secret-key-hardening-777888"


@pytest.fixture(autouse=True)
async def setup_test_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    get_settings.cache_clear()
    reset_rate_limiters()
    await init_db()
    yield
    reset_rate_limiters()
    get_settings.cache_clear()


def make_auth_header(user_id=None) -> dict[str, str]:
    uid = user_id or uuid4()
    payload = {
        "sub": str(uid),
        "email": "test@artisan.io",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


# -----------------------------------------------------------------------------
# 1. Stuck-Run Recovery
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_recover_stuck_runs_marks_stale_running_as_failed():
    user_id = uuid4()
    prod_id = uuid4()

    now = datetime.now(timezone.utc)
    stale_heartbeat = now - timedelta(seconds=300)  # > STAGE_TIMEOUT_SECONDS (120)
    fresh_heartbeat = now - timedelta(seconds=10)

    stale_run_id = uuid4()
    null_hb_run_id = uuid4()
    fresh_run_id = uuid4()
    awaiting_run_id = uuid4()

    async with async_session_maker() as session:
        # Seed product
        session.add(
            ProductModel(
                id=prod_id,
                owner_id=user_id,
                name="Test Silk Scarf",
                category="Accessories",
                description="Silk scarf for stuck run test",
                moq=1,
            )
        )
        # 1. Stale heartbeat run (status: running)
        session.add(
            ResearchRunModel(
                id=stale_run_id,
                owner_id=user_id,
                product_id=prod_id,
                status="running",
                stage="discovery",
                heartbeat_at=stale_heartbeat,
                created_at=stale_heartbeat,
            )
        )
        # 2. Null heartbeat run (status: running)
        session.add(
            ResearchRunModel(
                id=null_hb_run_id,
                owner_id=user_id,
                product_id=prod_id,
                status="running",
                stage="planning",
                heartbeat_at=None,
                created_at=stale_heartbeat,
            )
        )
        # 3. Fresh heartbeat run (status: running)
        session.add(
            ResearchRunModel(
                id=fresh_run_id,
                owner_id=user_id,
                product_id=prod_id,
                status="running",
                stage="discovery",
                heartbeat_at=fresh_heartbeat,
                created_at=fresh_heartbeat,
            )
        )
        # 4. Awaiting review run (status: awaiting_review) with stale heartbeat
        session.add(
            ResearchRunModel(
                id=awaiting_run_id,
                owner_id=user_id,
                product_id=prod_id,
                status="awaiting_review",
                stage="anchor_review",
                heartbeat_at=stale_heartbeat,
                created_at=stale_heartbeat,
            )
        )
        await session.commit()

    # Call recover_stuck_runs
    recovered = await recover_stuck_runs()
    assert stale_run_id in recovered
    assert null_hb_run_id in recovered
    assert fresh_run_id not in recovered
    assert awaiting_run_id not in recovered

    async with async_session_maker() as session:
        # Verify stale run is marked failed with error code internal_error and message interrupted
        r_stale = (await session.execute(select(ResearchRunModel).where(ResearchRunModel.id == stale_run_id))).scalar_one()
        assert r_stale.status == "failed"
        assert r_stale.error == {"code": "internal_error", "message": "interrupted"}
        assert r_stale.finished_at is not None

        # Verify null heartbeat run is also marked failed
        r_null = (await session.execute(select(ResearchRunModel).where(ResearchRunModel.id == null_hb_run_id))).scalar_one()
        assert r_null.status == "failed"
        assert r_null.error == {"code": "internal_error", "message": "interrupted"}
        assert r_null.finished_at is not None

        # Verify fresh run was NOT touched
        r_fresh = (await session.execute(select(ResearchRunModel).where(ResearchRunModel.id == fresh_run_id))).scalar_one()
        assert r_fresh.status == "running"

        # Verify awaiting_review run was COMPLETELY untouched
        r_awaiting = (await session.execute(select(ResearchRunModel).where(ResearchRunModel.id == awaiting_run_id))).scalar_one()
        assert r_awaiting.status == "awaiting_review"
        assert r_awaiting.stage == "anchor_review"


# -----------------------------------------------------------------------------
# 2. Per-User Rate Limiting
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_per_user_rate_limiting_exceeded_returns_429():
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    other_user = uuid4()
    other_headers = make_auth_header(user_id=other_user)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create products for both users upfront before any research runs start
        prod_res = await client.post(
            "/api/v1/products",
            json={"name": "Rate Limit Product", "category": "Home", "description": "Test", "moq": 1},
            headers=headers,
        )
        assert prod_res.status_code == 201
        prod_id = prod_res.json()["id"]

        prod_other = await client.post(
            "/api/v1/products",
            json={"name": "Other Product", "category": "Home", "description": "Test", "moq": 1},
            headers=other_headers,
        )
        assert prod_other.status_code == 201
        prod_other_id = prod_other.json()["id"]

        # 10 calls within limit of 10
        for i in range(10):
            res = await client.post(
                "/api/v1/research-runs",
                json={"product_id": prod_id, "inputs": {}},
                headers=headers,
            )
            assert res.status_code == 201

        # 11th call must trigger 429 rate_limited in Appendix A.5 error envelope
        res_limit = await client.post(
            "/api/v1/research-runs",
            json={"product_id": prod_id, "inputs": {}},
            headers=headers,
        )
        assert res_limit.status_code == 429
        data = res_limit.json()
        assert "error" in data
        assert data["error"]["code"] == "rate_limited"
        assert "Too many requests" in data["error"]["message"]
        assert "request_id" in data["error"]

        # Different user must NOT be rate limited
        other_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": prod_other_id, "inputs": {}},
            headers=other_headers,
        )
        assert other_res.status_code == 201


# -----------------------------------------------------------------------------
# 3. Fixed Demo Scenario Seed Script
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_seed_demo_data_idempotency_and_is_demo_flag():
    owner_id = uuid4()

    async with async_session_maker() as session:
        res1 = await seed_demo_data(session, owner_id)
        assert res1["profile"].business_name == "Sample Seller"
        assert len(res1["products"]) == 4
        assert res1["run"].status == "completed"
        assert len(res1["anchors"]) == 2
        assert len(res1["leads"]) == 3
        assert res1["draft"] is not None

        # Verify all products have required attributes and is_demo=True
        for prod in res1["products"]:
            assert prod.is_demo is True
            assert prod.price_segment == "mid_premium"
            assert prod.moq == 50
            assert prod.monthly_capacity == 1500
            assert "botanical motifs" in prod.motifs
            assert "terracotta" in prod.colours

        # Verify all anchors, leads, draft have is_demo=True
        for a in res1["anchors"]:
            assert a.is_demo is True
            assert a.status == "confirmed"

        for lead in res1["leads"]:
            assert lead.is_demo is True
            assert lead.tier in ("qualified", "needs_review")
            assert "overall" in lead.scores

        assert res1["draft"].is_demo is True
        assert res1["draft"].status == "draft"

    # Idempotency check: run seed again with same owner_id
    async with async_session_maker() as session:
        res2 = await seed_demo_data(session, owner_id)
        assert res2["profile"].business_name == "Sample Seller"
        assert len(res2["products"]) == 4

        # Total count in database for this owner should still be exactly 4 products, 3 leads, etc.
        p_count = (await session.execute(select(ProductModel).where(ProductModel.owner_id == owner_id))).scalars().all()
        assert len(p_count) == 4
        l_count = (await session.execute(select(LeadModel).where(LeadModel.owner_id == owner_id))).scalars().all()
        assert len(l_count) == 3
