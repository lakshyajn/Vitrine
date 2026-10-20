"""
Tests for Auth (Supabase JWT Verification) and Database Models (Step 2).
Verifies:
1. Valid JWT extracts user_id and email.
2. Missing, expired, or invalid tokens return 401 unauthorized in Appendix A.5 format.
3. Database tables initialize cleanly in async SQLite and support CRUD operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
import time
from uuid import UUID, uuid4

from fastapi import Depends
from httpx import ASGITransport, AsyncClient
import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.auth.deps import CurrentUser, current_user
from backend.app.core.config import get_settings
from backend.app.db.models import (
    Base,
    LeadModel,
    ProductModel,
    ProfileModel,
    ResearchRunModel,
)
from backend.app.db.session import create_engine_from_url, init_db
from backend.app.main import create_app

JWT_SECRET = "test-supabase-jwt-secret-for-ws2-unit-tests-123456"


@pytest.fixture
def auth_env(monkeypatch):
    """Configure test JWT secret in environment."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def create_token(
    sub: str | UUID,
    email: str = "seller@example.com",
    expires_in: int = 3600,
    secret: str = JWT_SECRET,
) -> str:
    payload = {
        "sub": str(sub),
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + expires_in,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_auth_success(auth_env):
    """Verify that a valid Supabase JWT successfully authenticates and extracts user_id."""
    app = create_app()
    user_id = uuid4()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id), "email": user.email, "role": user.role}

    token = create_token(sub=user_id, email="artisan@karigar.test")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["user_id"] == str(user_id)
        assert data["email"] == "artisan@karigar.test"
        assert data["role"] == "authenticated"


@pytest.mark.asyncio
async def test_auth_missing_token_returns_401(auth_env):
    """Verify that missing Authorization header returns 401 unauthorized in A.5 envelope."""
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/test-protected")
        assert res.status_code == 401
        data = res.json()

        assert "error" in data
        error = data["error"]
        assert error["code"] == "unauthorized"
        assert "Missing" in error["message"]
        assert "request_id" in error


@pytest.mark.asyncio
async def test_auth_expired_token_returns_401(auth_env):
    """Verify that an expired token returns 401 unauthorized with expired message."""
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    expired_token = create_token(sub=uuid4(), expires_in=-120)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert res.status_code == 401
        data = res.json()

        assert data["error"]["code"] == "unauthorized"
        assert "expired" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_auth_invalid_signature_returns_401(auth_env):
    """Verify that token signed with wrong secret returns 401 unauthorized."""
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    fake_token = create_token(sub=uuid4(), secret="completely-wrong-secret-signature")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert res.status_code == 401
        data = res.json()

        assert data["error"]["code"] == "unauthorized"
        assert "invalid" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_database_initialization_and_crud():
    """Verify that SQLAlchemy async models initialize cleanly and support CRUD operations."""
    test_engine = create_engine_from_url("sqlite+aiosqlite:///:memory:")
    await init_db(test_engine)

    session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        user_id = uuid4()

        # 1. Create and verify Profile
        profile = ProfileModel(
            user_id=user_id,
            business_name="Botanical Studio Workshop",
            country="India",
            website="https://botanicalstudio.test",
            contact_email="hello@botanicalstudio.test",
            about="Hand block printed artisanal home textiles.",
        )
        session.add(profile)
        await session.commit()

        stmt = select(ProfileModel).where(ProfileModel.user_id == user_id)
        saved_profile = (await session.execute(stmt)).scalar_one()
        assert saved_profile.business_name == "Botanical Studio Workshop"
        assert saved_profile.id is not None

        # 2. Create and verify Product
        product = ProductModel(
            owner_id=user_id,
            name="Block Printed Table Linen Set",
            category="Home Textiles",
            description="Handmade cotton table linen with natural dyes.",
            materials=["cotton", "natural linen"],
            style=["botanical", "artisanal"],
            motifs=["floral", "leaf"],
            colours=["terracotta", "indigo"],
            price_segment="mid_premium",
            price_min=35.0,
            price_max=85.0,
            moq=50,
            monthly_capacity=1500,
            target_retailer_types=["boutique", "concept store"],
            images=["https://storage.supabase.co/img1.jpg"],
            is_demo=True,
        )
        session.add(product)
        await session.commit()

        prod_stmt = select(ProductModel).where(ProductModel.owner_id == user_id)
        saved_prod = (await session.execute(prod_stmt)).scalar_one()
        assert saved_prod.name == "Block Printed Table Linen Set"
        assert saved_prod.moq == 50
        assert saved_prod.price_min == 35.0
        assert saved_prod.is_demo is True

        # 3. Create Research Run
        run = ResearchRunModel(
            owner_id=user_id,
            product_id=saved_prod.id,
            status="queued",
            stage="planning",
            inputs={"regions": ["Europe"], "notes": "Target small design shops"},
            provider_modes={"taste": "mock", "search": "mock", "ai": "mock"},
        )
        session.add(run)
        await session.commit()

        run_stmt = select(ResearchRunModel).where(ResearchRunModel.id == run.id)
        saved_run = (await session.execute(run_stmt)).scalar_one()
        assert saved_run.status == "queued"
        assert saved_run.stage == "planning"

        # 4. Create Lead
        lead = LeadModel(
            owner_id=user_id,
            run_id=saved_run.id,
            product_id=saved_prod.id,
            name="Amsterdam Concept Store",
            website="https://amsterdamconcept.test",
            canonical_domain="amsterdamconcept.test",
            tier="qualified",
            scores={"overall": 85.0, "category_fit": 100.0, "tier_reasons": ["Verified site"]},
            is_demo=True,
        )
        session.add(lead)
        await session.commit()

        lead_stmt = select(LeadModel).where(LeadModel.canonical_domain == "amsterdamconcept.test")
        saved_lead = (await session.execute(lead_stmt)).scalar_one()
        assert saved_lead.name == "Amsterdam Concept Store"
        assert saved_lead.tier == "qualified"
        assert saved_lead.is_demo is True

    await test_engine.dispose()
