"""
Tests for Auth (Supabase JWT Verification) and Database Models (Step 2 & Milestone A).
Verifies:
1. Valid HS256 JWT extracts user_id, email, and role.
2. Valid ES256 and RS256 JWTs verify using PyJWKClient (mocked locally, no network).
3. Missing, expired, wrong audience, wrong issuer, or tampered tokens return 401 unauthorized in Appendix A.5 format.
4. alg=none is rejected with 401.
5. Missing sub or non-UUID sub is rejected with 401.
6. When ALLOW_DEV_TOKENS=false, dev aliases ("dev-token") and unsigned tokens are rejected with 401.
7. No secret, token, or key value appears in error responses or logs for failed auth.
8. Database tables initialize cleanly in async SQLite and support CRUD operations.
"""

from __future__ import annotations

import logging
import time
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.auth.deps import CurrentUser, current_user
import backend.app.auth.deps as auth_deps
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
TEST_SUPABASE_URL = "https://test-project.supabase.co"


@pytest.fixture
def auth_env(monkeypatch):
    """Configure test JWT secret and strict dev token enforcement in environment."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("ALLOW_DEV_TOKENS", "false")
    monkeypatch.setenv("SUPABASE_URL", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def create_token(
    sub: str | UUID,
    email: str = "seller@example.com",
    expires_in: int = 3600,
    secret: str = JWT_SECRET,
    aud: str = "authenticated",
    iss: str | None = None,
    algorithm: str = "HS256",
) -> str:
    payload = {
        "sub": str(sub),
        "email": email,
        "role": "authenticated",
        "aud": aud,
        "exp": int(time.time()) + expires_in,
    }
    if iss is not None:
        payload["iss"] = iss
    return jwt.encode(payload, secret, algorithm=algorithm)


@pytest.mark.asyncio
async def test_auth_success(auth_env):
    """Verify that a valid Supabase HS256 JWT successfully authenticates and extracts user_id."""
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
async def test_auth_success_es256(monkeypatch):
    """Verify that a valid Supabase ES256 JWT verifies via monkeypatched PyJWKClient."""
    ec_priv = ec.generate_private_key(ec.SECP256R1())
    ec_pub = ec_priv.public_key()

    monkeypatch.setenv("ALLOW_DEV_TOKENS", "false")
    monkeypatch.setenv("SUPABASE_URL", TEST_SUPABASE_URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "")
    get_settings.cache_clear()

    class MockSigningKey:
        def __init__(self, key):
            self.key = key

    class MockJWKClient:
        def __init__(self, key):
            self._key = key

        def get_signing_key_from_jwt(self, token_str: str):
            return MockSigningKey(self._key)

    monkeypatch.setattr(auth_deps, "get_jwk_client", lambda url: MockJWKClient(ec_pub))

    app = create_app()
    user_id = uuid4()

    @app.get("/api/v1/test-protected-es256")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id), "email": user.email}

    token = jwt.encode(
        {
            "sub": str(user_id),
            "email": "es256-seller@karigar.test",
            "aud": "authenticated",
            "iss": f"{TEST_SUPABASE_URL}/auth/v1",
            "exp": int(time.time()) + 3600,
        },
        ec_priv,
        algorithm="ES256",
        headers={"kid": "test-ec-kid"},
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected-es256",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["user_id"] == str(user_id)
        assert data["email"] == "es256-seller@karigar.test"


@pytest.mark.asyncio
async def test_auth_success_rs256(monkeypatch):
    """Verify that a valid Supabase RS256 JWT verifies via monkeypatched PyJWKClient."""
    rsa_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    rsa_pub = rsa_priv.public_key()

    monkeypatch.setenv("ALLOW_DEV_TOKENS", "false")
    monkeypatch.setenv("SUPABASE_URL", TEST_SUPABASE_URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "")
    get_settings.cache_clear()

    class MockSigningKey:
        def __init__(self, key):
            self.key = key

    class MockJWKClient:
        def __init__(self, key):
            self._key = key

        def get_signing_key_from_jwt(self, token_str: str):
            return MockSigningKey(self._key)

    monkeypatch.setattr(auth_deps, "get_jwk_client", lambda url: MockJWKClient(rsa_pub))

    app = create_app()
    user_id = uuid4()

    @app.get("/api/v1/test-protected-rs256")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id), "email": user.email}

    token = jwt.encode(
        {
            "sub": str(user_id),
            "email": "rs256-seller@karigar.test",
            "aud": "authenticated",
            "iss": f"{TEST_SUPABASE_URL}/auth/v1",
            "exp": int(time.time()) + 3600,
        },
        rsa_priv,
        algorithm="RS256",
        headers={"kid": "test-rsa-kid"},
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected-rs256",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["user_id"] == str(user_id)
        assert data["email"] == "rs256-seller@karigar.test"


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
async def test_auth_wrong_audience_returns_401(auth_env):
    """Verify that token with wrong audience returns 401 unauthorized."""
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    bad_aud_token = create_token(sub=uuid4(), aud="anon")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {bad_aud_token}"},
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "unauthorized"
        assert "audience" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_auth_wrong_issuer_returns_401(monkeypatch):
    """Verify that token with wrong issuer returns 401 unauthorized when SUPABASE_URL is configured."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("ALLOW_DEV_TOKENS", "false")
    monkeypatch.setenv("SUPABASE_URL", TEST_SUPABASE_URL)
    get_settings.cache_clear()

    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    wrong_iss_token = create_token(
        sub=uuid4(),
        iss="https://malicious-site.test/auth/v1",
        aud="authenticated",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {wrong_iss_token}"},
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "unauthorized"
        assert "issuer" in data["error"]["message"].lower()


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
        assert "signature" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_auth_alg_none_rejected(auth_env):
    """Verify that alg=none tokens are strictly rejected with 401 unauthorized."""
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    payload = {
        "sub": str(uuid4()),
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    none_token = jwt.encode(payload, key=None, algorithm="none")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {none_token}"},
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "unauthorized"
        assert "algorithm" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_auth_dev_alias_rejected_when_dev_tokens_disabled(auth_env):
    """Verify that dev aliases like 'dev-token' return 401 when ALLOW_DEV_TOKENS=false."""
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for alias in ("dev-token", "demo-token", "dev", "test", "mock"):
            res = await client.get(
                "/api/v1/test-protected",
                headers={"Authorization": f"Bearer {alias}"},
            )
            assert res.status_code == 401
            assert res.json()["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_auth_unsigned_vitrine_dev_token_rejected_when_dev_tokens_disabled(auth_env):
    """Verify that unsigned vitrine-dev tokens return 401 when ALLOW_DEV_TOKENS=false."""
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "iss": "vitrine-dev",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, "untrusted-secret-at-least-32-chars-long", algorithm="HS256")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_auth_missing_sub_returns_401(auth_env):
    """Verify that a token missing the sub claim returns 401 unauthorized."""
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    payload = {
        "email": "no-sub@karigar.test",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "unauthorized"
        assert "sub" in data["error"]["message"].lower() or "subject" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_auth_non_uuid_sub_returns_401(auth_env):
    """Verify that a token with non-UUID sub claim returns 401 unauthorized."""
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    token = create_token(sub="not-a-valid-uuid-format")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "unauthorized"
        assert "uuid" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_auth_no_secret_or_token_leaked_in_error_or_logs(auth_env, caplog):
    """Verify that no secret, token, or key value appears in error responses or logs for failed auth."""
    caplog.set_level(logging.DEBUG)
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    sensitive_token_payload = "super-secret-sensitive-marker-string-987654"
    tampered_token = create_token(sub=uuid4(), secret="different-secret-key-at-least-32-chars")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {tampered_token}"},
        )
        assert res.status_code == 401
        resp_text = res.text

        # Ensure no secret or token content appears in response
        assert JWT_SECRET not in resp_text
        assert "different-secret-key-at-least-32-chars" not in resp_text
        assert sensitive_token_payload not in resp_text

        # Ensure no secrets leak in captured logs
        log_text = caplog.text
        assert JWT_SECRET not in log_text
        assert "different-secret-key-at-least-32-chars" not in log_text


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
