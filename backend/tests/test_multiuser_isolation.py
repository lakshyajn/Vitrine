"""
Milestone E: End-to-end Multi-Tenant Isolation Tests (WS2).
Verifies that two distinct valid authenticated users (User A and User B) can both
exist simultaneously with independent tokens, and User B receives 404 Not Found
for all cross-user read, update, create-child, or delete operations across:
- Profile
- Products & Images
- Research Runs, Anchors & Hypotheses
- Buyer Leads & Evidence
- Outreach Drafts
"""

from __future__ import annotations

import time
from uuid import UUID, uuid4

from httpx import ASGITransport, AsyncClient
import jwt
import pytest

from backend.app.core.config import get_settings
from backend.app.db.seed_demo import seed_demo_data
from backend.app.db.session import async_session_maker
from backend.app.main import app

JWT_SECRET = "ws2-multiuser-isolation-secret-111222"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("APP_ENV", "dev")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_token(user_id: UUID, email: str) -> str:
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


def auth_headers(user_id: UUID, email: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id, email)}"}


@pytest.mark.asyncio
async def test_multiuser_simultaneous_isolation():
    """
    User A seeds workspace. User B attempts to access every single entity of User A.
    Verifies that all operations return 404.
    """
    user_a = uuid4()
    user_b = uuid4()

    headers_a = auth_headers(user_a, "maker_a@studio.com")
    headers_b = auth_headers(user_b, "maker_b@studio.com")

    # Seed User A with the full suite of records (products, runs, anchors, hypotheses, leads, evidence, drafts)
    async with async_session_maker() as session:
        seed_result = await seed_demo_data(session, user_a)

    prod_a_id = str(seed_result["products"][0].id)
    run_a_id = str(seed_result["run"].id)
    anchor_a_id = str(seed_result["anchors"][0].id)
    lead_a_id = str(seed_result["leads"][0].id)
    draft_a_id = str(seed_result["draft"].id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Profile Isolation: User B's profile is isolated from User A
        res_profile_a = await client.get("/api/v1/profile", headers=headers_a)
        assert res_profile_a.status_code == 200
        assert res_profile_a.json()["business_name"] == "Sample Seller"

        res_profile_b = await client.get("/api/v1/profile", headers=headers_b)
        assert res_profile_b.status_code == 200
        # User B has newly created empty profile, not User A's
        assert res_profile_b.json()["user_id"] == str(user_b)
        assert res_profile_b.json()["business_name"] == ""

        # 2. Products Isolation:
        # User B reading User A's product -> 404
        assert (await client.get(f"/api/v1/products/{prod_a_id}", headers=headers_b)).status_code == 404

        # User B updating User A's product -> 404
        assert (await client.put(f"/api/v1/products/{prod_a_id}", json={"name": "Hacked"}, headers=headers_b)).status_code == 404

        # User B uploading image to User A's product -> 404
        image_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        files = {"file": ("test.png", image_content, "image/png")}
        assert (await client.post(f"/api/v1/products/{prod_a_id}/images", files=files, headers=headers_b)).status_code == 404

        # User B deleting User A's product -> 404
        assert (await client.delete(f"/api/v1/products/{prod_a_id}", headers=headers_b)).status_code == 404

        # 3. Research Runs & Anchors Isolation:
        # User B reading User A's run -> 404
        assert (await client.get(f"/api/v1/research-runs/{run_a_id}", headers=headers_b)).status_code == 404

        # User B rerunning User A's run -> 404
        assert (await client.post(f"/api/v1/research-runs/{run_a_id}/rerun", headers=headers_b)).status_code == 404

        # User B reading User A's anchors -> 404
        assert (await client.get(f"/api/v1/research-runs/{run_a_id}/anchors", headers=headers_b)).status_code == 404

        # User B confirming User A's anchors -> 404
        assert (await client.post(
            f"/api/v1/research-runs/{run_a_id}/confirm-anchors",
            json={"confirmed_anchor_ids": [anchor_a_id], "rejected_anchor_ids": []},
            headers=headers_b,
        )).status_code == 404

        # User B updating User A's anchor directly -> 404
        assert (await client.patch(
            f"/api/v1/taste-anchors/{anchor_a_id}",
            json={"status": "rejected"},
            headers=headers_b,
        )).status_code == 404

        # User B reading User A's hypotheses -> 404
        assert (await client.get(f"/api/v1/research-runs/{run_a_id}/hypotheses", headers=headers_b)).status_code == 404

        # 4. Leads & Evidence Isolation:
        # User B reading User A's lead -> 404
        assert (await client.get(f"/api/v1/leads/{lead_a_id}", headers=headers_b)).status_code == 404

        # User B reading User A's lead evidence -> 404
        assert (await client.get(f"/api/v1/leads/{lead_a_id}/evidence", headers=headers_b)).status_code == 404

        # User B updating review status of User A's lead -> 404
        assert (await client.patch(
            f"/api/v1/leads/{lead_a_id}",
            json={"review_status": "saved"},
            headers=headers_b,
        )).status_code == 404

        # 5. Outreach Drafts Isolation:
        # User B updating User A's outreach draft -> 404
        assert (await client.patch(
            f"/api/v1/outreach-drafts/{draft_a_id}",
            json={"subject": "Tampered subject"},
            headers=headers_b,
        )).status_code == 404

        # User B regenerating User A's draft -> 404
        assert (await client.post(
            f"/api/v1/outreach-drafts/{draft_a_id}/regenerate",
            headers=headers_b,
        )).status_code == 404

        # User B listing drafts for User A's lead -> 404
        assert (await client.get(f"/api/v1/leads/{lead_a_id}/outreach-drafts", headers=headers_b)).status_code == 404
