"""
Unit and integration tests for POST /api/v1/demo/seed (Milestone D).
Tests:
1. Seeds only the calling user with realistic demo data (is_demo=True).
2. Idempotency: calling the endpoint twice does not duplicate records.
3. User isolation: User B cannot see or query User A's seeded demo data.
4. Returns 404 when APP_ENV=production.
"""

from __future__ import annotations

import time
from uuid import UUID, uuid4

from httpx import ASGITransport, AsyncClient
import jwt
import pytest
from sqlalchemy import select

from backend.app.core.config import get_settings
from backend.app.db.models import (
    LeadModel,
    OutreachDraftModel,
    ProductModel,
    ResearchRunModel,
)
from backend.app.db.session import async_session_maker
from backend.app.main import app

JWT_SECRET = "ws2-demo-seed-test-secret-777666"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("APP_ENV", "dev")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_token(user_id: UUID, email: str = "artisan@test.com") -> str:
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    _s = get_settings()
    if _s.supabase_url and "iss" not in payload:
        payload["iss"] = f"{_s.supabase_url.rstrip('/')}/auth/v1"
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def auth_headers(user_id: UUID, email: str = "artisan@test.com") -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id, email)}"}


@pytest.mark.asyncio
async def test_demo_seed_endpoint_success():
    """Verify POST /api/v1/demo/seed creates demo records scoped exclusively to caller."""
    user_a = uuid4()
    headers_a = auth_headers(user_a, email="user_a@maker.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Before seed: products is empty
        res_before = await client.get("/api/v1/products", headers=headers_a)
        assert res_before.status_code == 200
        assert len(res_before.json()) == 0

        # Call seed endpoint
        res_seed = await client.post("/api/v1/demo/seed", headers=headers_a)
        assert res_seed.status_code == 200
        data = res_seed.json()
        assert data["products_seeded"] == 4
        assert data["leads_seeded"] == 3
        assert data["runs_seeded"] == 1
        assert data["drafts_seeded"] == 1

        # After seed: products has 4 items
        res_after = await client.get("/api/v1/products", headers=headers_a)
        assert res_after.status_code == 200
        products = res_after.json()
        assert len(products) == 4
        for prod in products:
            assert prod["owner_id"] == str(user_a)
            assert prod["is_demo"] is True

        # Verify DB directly: all seeded records have owner_id == user_a and is_demo=True
        async with async_session_maker() as session:
            leads = (await session.execute(
                select(LeadModel).where(LeadModel.owner_id == user_a)
            )).scalars().all()
            assert len(leads) == 3
            assert all(l.is_demo is True for l in leads)

            runs = (await session.execute(
                select(ResearchRunModel).where(ResearchRunModel.owner_id == user_a)
            )).scalars().all()
            assert len(runs) == 1

            drafts = (await session.execute(
                select(OutreachDraftModel).where(OutreachDraftModel.owner_id == user_a)
            )).scalars().all()
            assert len(drafts) == 1
            assert drafts[0].is_demo is True


@pytest.mark.asyncio
async def test_demo_seed_idempotency():
    """Calling POST /api/v1/demo/seed twice for the same user does not duplicate records."""
    user_a = uuid4()
    headers_a = auth_headers(user_a, email="user_idempotent@maker.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First call
        res1 = await client.post("/api/v1/demo/seed", headers=headers_a)
        assert res1.status_code == 200

        # Second call
        res2 = await client.post("/api/v1/demo/seed", headers=headers_a)
        assert res2.status_code == 200

        # Products count remains 4
        res_prods = await client.get("/api/v1/products", headers=headers_a)
        assert res_prods.status_code == 200
        assert len(res_prods.json()) == 4

        # Leads count remains 3
        res_leads = await client.get("/api/v1/leads", headers=headers_a)
        assert res_leads.status_code == 200
        assert res_leads.json()["total"] == 3


@pytest.mark.asyncio
async def test_demo_seed_user_isolation():
    """User B cannot see or query User A's seeded demo data."""
    user_a = uuid4()
    user_b = uuid4()
    headers_a = auth_headers(user_a, email="maker_a@test.com")
    headers_b = auth_headers(user_b, email="maker_b@test.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # User A seeds demo data
        res_seed = await client.post("/api/v1/demo/seed", headers=headers_a)
        assert res_seed.status_code == 200

        # User A gets product list
        prods_a = (await client.get("/api/v1/products", headers=headers_a)).json()
        assert len(prods_a) == 4
        product_a_id = prods_a[0]["id"]

        # User B queries products: sees 0 products
        prods_b = (await client.get("/api/v1/products", headers=headers_b)).json()
        assert len(prods_b) == 0

        # User B queries leads: sees 0 leads
        leads_b = (await client.get("/api/v1/leads", headers=headers_b)).json()
        assert leads_b["total"] == 0

        # User B tries to read User A's product directly: returns 404
        direct_res = await client.get(f"/api/v1/products/{product_a_id}", headers=headers_b)
        assert direct_res.status_code == 404


@pytest.mark.asyncio
async def test_demo_seed_404_in_production(monkeypatch):
    """POST /api/v1/demo/seed returns 404 when APP_ENV=production."""
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()

    user = uuid4()
    headers = auth_headers(user)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post("/api/v1/demo/seed", headers=headers)
        assert res.status_code == 404
        data = res.json()
        msg = data.get("error", {}).get("message") or data.get("detail") or ""
        assert "only available in dev and test" in msg
