"""
Tests for Research Runs and Taste Anchors Phase 1 (Step 5).
Verifies:
1. Idempotency on POST /research-runs via Idempotency-Key header.
2. Background runner Phase 1 execution reaching awaiting_review (planning -> anchor_proposal -> anchor_review).
3. Creation of AI proposed anchors, resolved taste provider entities, and market hypotheses.
4. Adding custom anchors (DECISION-D3: source=user_added, status=confirmed, is_demo=False).
5. PATCH /taste-anchors/{id} updating status, label, entity_type, rationale.
6. POST /research-runs/{id}/confirm-anchors blocking when 0 anchors confirmed (422 validation_error)
   unless proceed_without_anchors is true (DECISION-D4).
7. Confirming anchors storing anchor_ids in run.inputs and transitioning status to queued (stage: discovery).
8. Rerunning existing runs copying inputs.
9. Strict user isolation across all research runs and anchor endpoints (404 not_found, never 403).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import time
from uuid import UUID, uuid4

from httpx import ASGITransport, AsyncClient
import jwt
import pytest
from sqlalchemy import select

from contracts.schemas import (
    ErrorCode,
    MarketHypothesis,
    MarketHypothesisStatus,
    Product,
    ResearchRun,
    ResearchRunActionResponse,
    TasteAnchor,
    TasteAnchorSource,
    TasteAnchorStatus,
)
from backend.app.core.config import get_settings
from backend.app.db.models import ProductModel, ResearchRunModel, TasteAnchorModel
from backend.app.main import app

JWT_SECRET = "ws2-step5-testing-jwt-secret-555444"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
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
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def auth_headers(user_id: UUID, email: str = "artisan@test.com") -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id, email)}"}


async def create_test_product(client: AsyncClient, headers: dict[str, str], name: str = "Block Print Runner") -> UUID:
    res = await client.post(
        "/api/v1/products",
        json={
            "name": name,
            "category": "Home Textiles",
            "description": "Artisan cotton table runner with botanical indigo motifs.",
            "materials": ["cotton", "indigo"],
            "style": ["botanical", "artisanal"],
            "motifs": ["floral"],
            "colours": ["indigo", "terracotta"],
            "moq": 25,
            "price_min": 35.0,
            "price_max": 90.0,
            "target_retailer_types": ["boutique", "concept store"],
        },
        headers=headers,
    )
    assert res.status_code == 201, res.text
    return UUID(res.json()["id"])


async def wait_for_run_state(
    client: AsyncClient,
    run_id: UUID,
    headers: dict[str, str],
    target_status: str = "awaiting_review",
    max_wait_seconds: float = 3.0,
) -> dict:
    start = time.time()
    while time.time() - start < max_wait_seconds:
        res = await client.get(f"/api/v1/research-runs/{run_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        if data.get("status") == target_status:
            return data
        await asyncio.sleep(0.05)
    raise TimeoutError(f"Run {run_id} did not reach status '{target_status}' within {max_wait_seconds}s")


# ==============================================================================
# 1. Idempotency & Creation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_create_research_run_idempotency():
    """Verify Idempotency-Key header returns the exact same run on duplicate POSTs."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prod_id = await create_test_product(client, headers)
        idem_key = f"idem-key-{uuid4()}"

        # 1. First request with Idempotency-Key
        res1 = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id), "inputs": {"regions": ["Western Europe"]}},
            headers={**headers, "Idempotency-Key": idem_key},
        )
        assert res1.status_code == 201
        run1 = ResearchRunActionResponse.model_validate(res1.json())
        assert run1.status == "queued"

        # 2. Second request with same Idempotency-Key returns same run ID
        res2 = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id), "inputs": {"regions": ["Western Europe"]}},
            headers={**headers, "Idempotency-Key": idem_key},
        )
        assert res2.status_code == 200 or res2.status_code == 201
        run2 = ResearchRunActionResponse.model_validate(res2.json())
        assert run2.id == run1.id

        # 3. Request with different Idempotency-Key returns new run ID
        res3 = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id), "inputs": {"regions": ["Western Europe"]}},
            headers={**headers, "Idempotency-Key": f"different-{uuid4()}"},
        )
        assert res3.status_code == 201
        run3 = ResearchRunActionResponse.model_validate(res3.json())
        assert run3.id != run1.id


# ==============================================================================
# 2. Phase 1 Runner Execution & Anchors/Hypotheses Proposals
# ==============================================================================

@pytest.mark.asyncio
async def test_research_run_reaches_awaiting_review():
    """
    Verify run executes Phase 1 runner:
    planning -> anchor_proposal -> awaiting_review (stage: anchor_review).
    Verifies plan, taste anchors, and market hypotheses are created and persisted.
    """
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prod_id = await create_test_product(client, headers)

        create_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id), "inputs": {"regions": ["Western Europe"]}},
            headers=headers,
        )
        assert create_res.status_code == 201
        run_id = UUID(create_res.json()["id"])

        # Wait for Phase 1 runner to complete and stop at awaiting_review
        run_data = await wait_for_run_state(client, run_id, headers, target_status="awaiting_review")
        run = ResearchRun.model_validate(run_data)
        assert run.status == "awaiting_review"
        assert run.stage == "anchor_review"
        assert run.plan is not None
        assert len(run.plan.aesthetic_candidates) >= 1
        assert run.provider_modes is not None
        assert run.started_at is not None

        # Verify anchors were generated
        anchors_res = await client.get(f"/api/v1/research-runs/{run_id}/anchors", headers=headers)
        assert anchors_res.status_code == 200
        anchors = [TasteAnchor.model_validate(a) for a in anchors_res.json()]
        assert len(anchors) >= 1

        # Check AI proposed anchors and resolved taste entities
        sources = {a.source for a in anchors}
        assert TasteAnchorSource.AI_PROPOSED in sources or TasteAnchorSource.DEMO in sources

        # Verify hypotheses were generated with status=proposed (DECISION-D13)
        hypos_res = await client.get(f"/api/v1/research-runs/{run_id}/hypotheses", headers=headers)
        assert hypos_res.status_code == 200
        hypos = [MarketHypothesis.model_validate(h) for h in hypos_res.json()]
        assert len(hypos) >= 1
        for h in hypos:
            assert h.status == MarketHypothesisStatus.PROPOSED


# ==============================================================================
# 3. Custom Anchors (D3) & Patching Anchors
# ==============================================================================

@pytest.mark.asyncio
async def test_custom_anchor_creation_and_patching():
    """
    Verify POST /research-runs/{id}/anchors creates custom anchor (source=user_added, status=confirmed, is_demo=False).
    Verify PATCH /taste-anchors/{id} updates status and fields.
    """
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prod_id = await create_test_product(client, headers)
        create_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id)},
            headers=headers,
        )
        run_id = UUID(create_res.json()["id"])
        await wait_for_run_state(client, run_id, headers, target_status="awaiting_review")

        # 1. Add custom anchor (D3)
        custom_res = await client.post(
            f"/api/v1/research-runs/{run_id}/anchors",
            json={
                "label": "Nordic Japandi Minimalism",
                "entity_type": "brand",
                "rationale": "Matches organic handcrafted aesthetic of collection.",
            },
            headers=headers,
        )
        assert custom_res.status_code == 201
        custom = TasteAnchor.model_validate(custom_res.json())
        assert custom.label == "Nordic Japandi Minimalism"
        assert custom.source == TasteAnchorSource.USER_ADDED
        assert custom.status == TasteAnchorStatus.CONFIRMED
        assert custom.is_demo is False
        assert custom.owner_id == user_id

        # 2. PATCH taste anchor: reject it
        patch1 = await client.patch(
            f"/api/v1/taste-anchors/{custom.id}",
            json={"status": "rejected"},
            headers=headers,
        )
        assert patch1.status_code == 200
        assert patch1.json()["status"] == "rejected"

        # 3. PATCH taste anchor: re-confirm and update rationale
        patch2 = await client.patch(
            f"/api/v1/taste-anchors/{custom.id}",
            json={"status": "confirmed", "rationale": "Updated rationale after artisan review."},
            headers=headers,
        )
        assert patch2.status_code == 200
        assert patch2.json()["status"] == "confirmed"
        assert patch2.json()["rationale"] == "Updated rationale after artisan review."


# ==============================================================================
# 4. Confirm Anchors (D4) Validation & Transition
# ==============================================================================

@pytest.mark.asyncio
async def test_confirm_anchors_blocks_when_zero_confirmed():
    """Verify confirm-anchors returns 422 validation_error if 0 anchors are confirmed."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prod_id = await create_test_product(client, headers)
        create_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id)},
            headers=headers,
        )
        run_id = UUID(create_res.json()["id"])
        await wait_for_run_state(client, run_id, headers, target_status="awaiting_review")

        # Explicitly reject all existing anchors
        anchors_res = await client.get(f"/api/v1/research-runs/{run_id}/anchors", headers=headers)
        for a in anchors_res.json():
            await client.patch(
                f"/api/v1/taste-anchors/{a['id']}",
                json={"status": "rejected"},
                headers=headers,
            )

        # Confirm anchors without proceed_without_anchors flag -> 422 validation_error
        blocked_res = await client.post(
            f"/api/v1/research-runs/{run_id}/confirm-anchors",
            json={"proceed_without_anchors": False},
            headers=headers,
        )
        assert blocked_res.status_code == 422
        data = blocked_res.json()
        assert "error" in data
        assert data["error"]["code"] == "validation_error"


@pytest.mark.asyncio
async def test_confirm_anchors_with_proceed_without_anchors_flag():
    """Verify proceed_without_anchors=true allows resuming with 0 confirmed anchors (DECISION-D4)."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prod_id = await create_test_product(client, headers)
        create_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id)},
            headers=headers,
        )
        run_id = UUID(create_res.json()["id"])
        await wait_for_run_state(client, run_id, headers, target_status="awaiting_review")

        # Reject all anchors
        anchors_res = await client.get(f"/api/v1/research-runs/{run_id}/anchors", headers=headers)
        for a in anchors_res.json():
            await client.patch(f"/api/v1/taste-anchors/{a['id']}", json={"status": "rejected"}, headers=headers)

        # Confirm with proceed_without_anchors: true
        ok_res = await client.post(
            f"/api/v1/research-runs/{run_id}/confirm-anchors",
            json={"proceed_without_anchors": True},
            headers=headers,
        )
        assert ok_res.status_code == 200
        run = ResearchRun.model_validate(ok_res.json())
        assert run.status == "queued"
        assert run.stage == "discovery"


@pytest.mark.asyncio
async def test_confirm_anchors_stores_anchor_ids_and_queues_run():
    """Verify confirming >= 1 anchor stores anchor_ids in run.inputs and transitions to queued."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prod_id = await create_test_product(client, headers)
        create_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id)},
            headers=headers,
        )
        run_id = UUID(create_res.json()["id"])
        await wait_for_run_state(client, run_id, headers, target_status="awaiting_review")

        # Add confirmed custom anchor
        custom_res = await client.post(
            f"/api/v1/research-runs/{run_id}/anchors",
            json={"label": "Confirmed Anchor A"},
            headers=headers,
        )
        anchor_id = custom_res.json()["id"]

        # Confirm anchors
        confirm_res = await client.post(
            f"/api/v1/research-runs/{run_id}/confirm-anchors",
            json={"proceed_without_anchors": False},
            headers=headers,
        )
        assert confirm_res.status_code == 200
        run = ResearchRun.model_validate(confirm_res.json())
        assert run.status == "queued"
        assert run.stage == "discovery"
        assert anchor_id in [str(a) for a in run.inputs.anchor_ids]


# ==============================================================================
# 5. Rerun Functionality
# ==============================================================================

@pytest.mark.asyncio
async def test_rerun_research_run():
    """Verify POST /research-runs/{id}/rerun creates new run with merged inputs."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        prod_id = await create_test_product(client, headers)
        create_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id), "inputs": {"regions": ["Europe"], "notes": "Initial run"}},
            headers=headers,
        )
        old_run_id = UUID(create_res.json()["id"])

        rerun_res = await client.post(
            f"/api/v1/research-runs/{old_run_id}/rerun",
            json={"product_id": str(prod_id), "inputs": {"notes": "Rerun note with extra detail"}},
            headers=headers,
        )
        assert rerun_res.status_code == 200
        new_run_id = UUID(rerun_res.json()["id"])
        assert new_run_id != old_run_id

        # Verify new run reaches awaiting_review and has merged inputs
        new_run_data = await wait_for_run_state(client, new_run_id, headers, target_status="awaiting_review")
        new_run = ResearchRun.model_validate(new_run_data)
        assert new_run.inputs.regions == ["Europe"]
        assert new_run.inputs.notes == "Rerun note with extra detail"


# ==============================================================================
# 6. User Isolation Tests (Defense-in-Depth, 404 Not Found)
# ==============================================================================

@pytest.mark.asyncio
async def test_research_runs_user_isolation():
    """
    Verify User A cannot read, rerun, view anchors/hypotheses, add anchors,
    patch anchors, or confirm anchors for User B's run.
    All must return 404 not_found (never 403).
    """
    user_a = uuid4()
    user_b = uuid4()
    headers_a = auth_headers(user_a)
    headers_b = auth_headers(user_b)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # User B sets up product and run
        prod_b = await create_test_product(client, headers_b, name="User B Product")
        create_b = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_b)},
            headers=headers_b,
        )
        run_b_id = UUID(create_b.json()["id"])
        await wait_for_run_state(client, run_b_id, headers_b, target_status="awaiting_review")

        # User B creates an anchor
        custom_b = await client.post(
            f"/api/v1/research-runs/{run_b_id}/anchors",
            json={"label": "User B Secret Anchor"},
            headers=headers_b,
        )
        anchor_b_id = custom_b.json()["id"]

        # 1. User A cannot GET User B's run
        get_res = await client.get(f"/api/v1/research-runs/{run_b_id}", headers=headers_a)
        assert get_res.status_code == 404
        assert get_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # 2. User A cannot rerun User B's run
        rerun_res = await client.post(f"/api/v1/research-runs/{run_b_id}/rerun", headers=headers_a)
        assert rerun_res.status_code == 404
        assert rerun_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # 3. User A cannot list User B's anchors
        anchors_res = await client.get(f"/api/v1/research-runs/{run_b_id}/anchors", headers=headers_a)
        assert anchors_res.status_code == 404
        assert anchors_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # 4. User A cannot add anchors to User B's run
        add_res = await client.post(
            f"/api/v1/research-runs/{run_b_id}/anchors",
            json={"label": "Injected Anchor"},
            headers=headers_a,
        )
        assert add_res.status_code == 404
        assert add_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # 5. User A cannot PATCH User B's anchor
        patch_res = await client.patch(
            f"/api/v1/taste-anchors/{anchor_b_id}",
            json={"status": "rejected"},
            headers=headers_a,
        )
        assert patch_res.status_code == 404
        assert patch_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # 6. User A cannot confirm User B's anchors
        confirm_res = await client.post(
            f"/api/v1/research-runs/{run_b_id}/confirm-anchors",
            json={"proceed_without_anchors": True},
            headers=headers_a,
        )
        assert confirm_res.status_code == 404
        assert confirm_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # 7. User A cannot view User B's hypotheses
        hypo_res = await client.get(f"/api/v1/research-runs/{run_b_id}/hypotheses", headers=headers_a)
        assert hypo_res.status_code == 404
        assert hypo_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # 8. User A cannot see User B's run in list
        list_a = await client.get("/api/v1/research-runs", headers=headers_a)
        assert list_a.status_code == 200
        run_ids_a = [r["id"] for r in list_a.json()]
        assert str(run_b_id) not in run_ids_a

        # 9. User A cannot start a run referencing User B's product
        cross_prod_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_b)},
            headers=headers_a,
        )
        assert cross_prod_res.status_code == 404
        assert cross_prod_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value
