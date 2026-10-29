"""
Tests for Auth (Supabase JWT Verification) and Database Models (Step 2 & Milestones A & B).
Verifies:
1. Valid HS256 JWT extracts user_id, email, and role.
2. Valid ES256 and RS256 JWTs verify using PyJWKClient (mocked locally, no network).
3. SUPABASE_URL trailing slash normalization.
4. Clock skew tolerance: iat 30s in future accepted (leeway=60), 10m in future rejected (not_yet_valid).
5. All 12 failure reason codes are logged at WARNING without leaking tokens or secrets:
   missing_token, malformed, unsupported_alg, bad_signature, bad_issuer, bad_audience,
   expired, not_yet_valid, jwks_unavailable, no_matching_key, secret_not_configured, invalid_sub.
6. Startup configuration checks (sb_ secret, JWT-as-secret, trailing slash, allow_dev_tokens).
7. Database tables initialize cleanly in async SQLite and support CRUD operations.
"""

from __future__ import annotations

import logging
import time
from uuid import UUID, uuid4

from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import Depends
from httpx import ASGITransport, AsyncClient
import jwt
from jwt import PyJWKClientConnectionError, PyJWKClientError, PyJWKSetError
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.app.auth.deps import (
    CurrentUser,
    check_startup_config,
    current_user,
)
import backend.app.auth.deps as auth_deps
from backend.app.core.config import Settings, get_settings
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
    iat_offset: int = 0,
    secret: str = JWT_SECRET,
    aud: str = "authenticated",
    iss: str | None = None,
    algorithm: str = "HS256",
    headers: dict | None = None,
) -> str:
    now = int(time.time())
    payload = {
        "sub": str(sub),
        "email": email,
        "role": "authenticated",
        "aud": aud,
        "iat": now + iat_offset,
        "exp": now + expires_in,
    }
    if iss is not None:
        payload["iss"] = iss
    return jwt.encode(payload, secret, algorithm=algorithm, headers=headers)


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
            "iat": int(time.time()),
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
            "iat": int(time.time()),
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
async def test_supabase_url_with_trailing_slash_normalized(monkeypatch):
    """Verify that SUPABASE_URL with trailing slash is normalized and correctly verifies issuer."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("ALLOW_DEV_TOKENS", "false")
    monkeypatch.setenv("SUPABASE_URL", f"{TEST_SUPABASE_URL}/  ")
    get_settings.cache_clear()

    app = create_app()
    user_id = uuid4()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    token = create_token(
        sub=user_id,
        iss=f"{TEST_SUPABASE_URL}/auth/v1",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["user_id"] == str(user_id)


@pytest.mark.asyncio
async def test_auth_iat_clock_skew(auth_env, caplog):
    """Verify leeway=60s: iat 30s in future accepted; 10m in future rejected with not_yet_valid."""
    caplog.set_level(logging.WARNING)
    app = create_app()
    user_id = uuid4()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    # 1. 30 seconds in future: accepted via leeway=60s
    token_30s_future = create_token(sub=user_id, iat_offset=30)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token_30s_future}"},
        )
        assert res.status_code == 200

    # 2. 10 minutes (600s) in future: rejected with 401 and not_yet_valid logged
    caplog.clear()
    token_10m_future = create_token(sub=user_id, iat_offset=600)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token_10m_future}"},
        )
        assert res.status_code == 401
        assert "not_yet_valid" in caplog.text


@pytest.mark.asyncio
async def test_auth_missing_token_returns_401(auth_env, caplog):
    """Verify missing Authorization header logs reason=missing_token and returns 401."""
    caplog.set_level(logging.WARNING)
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/test-protected")
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["code"] == "unauthorized"
        assert "missing_token" in caplog.text


@pytest.mark.asyncio
async def test_auth_expired_token_returns_401(auth_env, caplog):
    """Verify expired token logs reason=expired and returns 401."""
    caplog.set_level(logging.WARNING)
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
        assert "expired" in caplog.text


@pytest.mark.asyncio
async def test_auth_wrong_audience_returns_401(auth_env, caplog):
    """Verify wrong audience logs reason=bad_audience and returns 401."""
    caplog.set_level(logging.WARNING)
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
        assert "bad_audience" in caplog.text


@pytest.mark.asyncio
async def test_auth_wrong_issuer_returns_401(monkeypatch, caplog):
    """Verify wrong issuer logs reason=bad_issuer and returns 401."""
    caplog.set_level(logging.WARNING)
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
        assert "bad_issuer" in caplog.text


@pytest.mark.asyncio
async def test_auth_invalid_signature_returns_401(auth_env, caplog):
    """Verify wrong secret logs reason=bad_signature and returns 401."""
    caplog.set_level(logging.WARNING)
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
        assert "bad_signature" in caplog.text


@pytest.mark.asyncio
async def test_auth_alg_none_rejected(auth_env, caplog):
    """Verify alg=none logs reason=unsupported_alg and returns 401."""
    caplog.set_level(logging.WARNING)
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
        assert "unsupported_alg" in caplog.text


@pytest.mark.asyncio
async def test_auth_empty_secret_with_hs256_token(monkeypatch, caplog):
    """Verify empty SUPABASE_JWT_SECRET logs reason=secret_not_configured and returns 401."""
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "")
    monkeypatch.setenv("ALLOW_DEV_TOKENS", "false")
    monkeypatch.setenv("SUPABASE_URL", "")
    get_settings.cache_clear()

    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    token = create_token(sub=uuid4(), secret="any-secret-at-least-32-chars-long")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401
        assert "secret_not_configured" in caplog.text


@pytest.mark.asyncio
async def test_auth_unreachable_jwks(monkeypatch, caplog):
    """Verify unreachable JWKS logs reason=jwks_unavailable and returns 401."""
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("ALLOW_DEV_TOKENS", "false")
    monkeypatch.setenv("SUPABASE_URL", TEST_SUPABASE_URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "")
    get_settings.cache_clear()

    class FailingJWKClient:
        def get_signing_key_from_jwt(self, token_str: str):
            raise PyJWKClientConnectionError("JWKS endpoint unreachable")

    monkeypatch.setattr(auth_deps, "get_jwk_client", lambda url: FailingJWKClient())

    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    ec_priv = ec.generate_private_key(ec.SECP256R1())
    token = jwt.encode(
        {"sub": str(uuid4()), "aud": "authenticated", "exp": int(time.time()) + 3600},
        ec_priv,
        algorithm="ES256",
        headers={"kid": "some-kid"},
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401
        assert "jwks_unavailable" in caplog.text


@pytest.mark.asyncio
async def test_auth_missing_kid_es256(monkeypatch, caplog):
    """Verify missing kid in ES256 header logs reason=no_matching_key and returns 401."""
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("ALLOW_DEV_TOKENS", "false")
    monkeypatch.setenv("SUPABASE_URL", TEST_SUPABASE_URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "")
    get_settings.cache_clear()

    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    ec_priv = ec.generate_private_key(ec.SECP256R1())
    # Token without 'kid' in headers
    token = jwt.encode(
        {"sub": str(uuid4()), "aud": "authenticated", "exp": int(time.time()) + 3600},
        ec_priv,
        algorithm="ES256",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401
        assert "no_matching_key" in caplog.text


@pytest.mark.asyncio
async def test_auth_no_matching_kid_in_jwks(monkeypatch, caplog):
    """Verify non-matching kid in JWKS logs reason=no_matching_key and returns 401."""
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv("ALLOW_DEV_TOKENS", "false")
    monkeypatch.setenv("SUPABASE_URL", TEST_SUPABASE_URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "")
    get_settings.cache_clear()

    class MissingKeyJWKClient:
        def get_signing_key_from_jwt(self, token_str: str):
            raise PyJWKClientError('Unable to find a signing key that matches: "unknown-kid"')

    monkeypatch.setattr(auth_deps, "get_jwk_client", lambda url: MissingKeyJWKClient())

    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    ec_priv = ec.generate_private_key(ec.SECP256R1())
    token = jwt.encode(
        {"sub": str(uuid4()), "aud": "authenticated", "exp": int(time.time()) + 3600},
        ec_priv,
        algorithm="ES256",
        headers={"kid": "unknown-kid"},
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401
        assert "no_matching_key" in caplog.text


@pytest.mark.asyncio
async def test_auth_missing_sub_returns_401(auth_env, caplog):
    """Verify token missing sub claim logs reason=invalid_sub and returns 401."""
    caplog.set_level(logging.WARNING)
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
        assert "invalid_sub" in caplog.text


@pytest.mark.asyncio
async def test_auth_non_uuid_sub_returns_401(auth_env, caplog):
    """Verify token with non-UUID sub logs reason=invalid_sub and returns 401."""
    caplog.set_level(logging.WARNING)
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
        assert "invalid_sub" in caplog.text


@pytest.mark.asyncio
async def test_auth_malformed_token_returns_401(auth_env, caplog):
    """Verify completely malformed token string logs reason=malformed and returns 401."""
    caplog.set_level(logging.WARNING)
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": "Bearer not-a-valid.jwt-token.at-all"},
        )
        assert res.status_code == 401
        assert "malformed" in caplog.text


@pytest.mark.asyncio
async def test_auth_no_secret_or_token_leaked_in_error_or_logs(auth_env, caplog):
    """Verify that no secret, token, or Authorization header appears in error responses or logs."""
    caplog.set_level(logging.DEBUG)
    app = create_app()

    @app.get("/api/v1/test-protected")
    async def protected_route(user: CurrentUser = Depends(current_user)):
        return {"user_id": str(user.id)}

    sensitive_token = create_token(sub=uuid4(), secret="different-secret-key-at-least-32-chars")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(
            "/api/v1/test-protected",
            headers={"Authorization": f"Bearer {sensitive_token}"},
        )
        assert res.status_code == 401
        resp_text = res.text

        # Ensure no secret or token content appears in response
        assert JWT_SECRET not in resp_text
        assert "different-secret-key-at-least-32-chars" not in resp_text
        assert sensitive_token not in resp_text

        # Ensure no secrets, token, or Authorization header leak in captured logs
        log_text = caplog.text
        assert JWT_SECRET not in log_text
        assert "different-secret-key-at-least-32-chars" not in log_text
        assert sensitive_token not in log_text
        assert f"Bearer {sensitive_token}" not in log_text


def test_startup_warnings_config_check(caplog):
    """Verify startup warnings for sb_ secret, JWT secret, trailing slash, and allow_dev_tokens."""
    caplog.set_level(logging.WARNING)

    # 1. Warning when SUPABASE_JWT_SECRET starts with sb_
    caplog.clear()
    settings_sb = Settings(
        supabase_jwt_secret="sb_secret_key_1234567890",
        supabase_url="https://xyz.supabase.co",
        allow_dev_tokens=False,
    )
    check_startup_config(settings_sb)
    assert "starts with 'sb_'" in caplog.text

    # 2. Warning when SUPABASE_JWT_SECRET is a 3-part JWT
    caplog.clear()
    settings_jwt = Settings(
        supabase_jwt_secret="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig",
        supabase_url="https://xyz.supabase.co",
        allow_dev_tokens=False,
    )
    check_startup_config(settings_jwt)
    assert "looks like a JWT" in caplog.text

    # 3. Warning when SUPABASE_URL has trailing slash
    caplog.clear()
    settings_slash = Settings(
        supabase_jwt_secret="valid_secret_key_32_characters_long",
        supabase_url="https://xyz.supabase.co/",
        allow_dev_tokens=False,
    )
    check_startup_config(settings_slash)
    assert "trailing slash" in caplog.text

    # 4. Warning when ALLOW_DEV_TOKENS is true
    caplog.clear()
    settings_dev = Settings(
        supabase_jwt_secret="valid_secret_key_32_characters_long",
        supabase_url="https://xyz.supabase.co",
        allow_dev_tokens=True,
    )
    auth_deps._warned_allow_dev_tokens = False
    check_startup_config(settings_dev)
    assert "ALLOW_DEV_TOKENS is true" in caplog.text


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
