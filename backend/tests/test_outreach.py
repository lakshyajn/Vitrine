"""
Unit and Integration Tests for Outreach Studio Endpoints (Step 8 Deliverable).

Covers:
1. POST /api/v1/leads/{id}/outreach-drafts: Grounded generation with facts_used, warnings (D5), is_demo (D1).
2. Subsequent generation increments version (max(version) + 1).
3. GET /api/v1/leads/{id}/outreach-drafts: Version history ordered by version desc.
4. PATCH /api/v1/outreach-drafts/{id}: In-place update of subject, body, status, followup_notes.
5. Atomic rule (DECISION-D11): Marking draft 'contacted' atomically updates lead.review_status = 'contacted'.
6. POST /api/v1/outreach-drafts/{id}/regenerate: Inserts new version row, sets parent_draft_id, preserves edited draft.
7. GET /api/v1/outreach-drafts (DECISION-D17): Top-level filtering by status, product_id, lead_id, ordered by updated_at desc.
8. User isolation: Strict 404 not_found when accessing another seller's lead or draft.
9. Zero-evidence lead outreach draft generation adds warning without crashing.
10. Verification that NO email-sending endpoint exists anywhere.
"""

from __future__ import annotations

import time
from uuid import UUID, uuid4
import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from contracts.schemas import (
    EvidenceSourceType,
    Lead,
    LeadReviewStatus,
    OutreachDraft,
    OutreachDraftStatus,
    Product,
)
from backend.app.core.config import get_settings
from backend.app.db.models import (
    LeadEvidenceModel,
    LeadModel,
    OutreachDraftModel,
    ProductModel,
    ResearchRunModel,
)
from backend.app.db.session import async_session_maker
from backend.app.main import app

JWT_SECRET = "ws2-step8-jwt-secret-testing-key-333444"


@pytest.fixture(autouse=True)
def setup_jwt_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_auth_header(user_id: UUID | None = None, email: str = "artisan@sampleseller.test") -> dict[str, str]:
    uid = user_id or uuid4()
    payload = {
        "sub": str(uid),
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    _s = get_settings()
    if _s.supabase_url and "iss" not in payload:
        payload["iss"] = f"{_s.supabase_url.rstrip('/')}/auth/v1"
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


async def _seed_lead_with_product_and_evidence(
    user_id: UUID,
    lead_name: str = "Atelier Living & Design",
    canonical_domain: str = "atelierlivingdemo.com",
    with_evidence: bool = True,
) -> tuple[ProductModel, LeadModel, list[LeadEvidenceModel]]:
    async with async_session_maker() as session:
        product = ProductModel(
            id=uuid4(),
            owner_id=user_id,
            name="Block-Printed Table Runner",
            category="Table Linens",
            description="Hand block-printed cotton table runner in terracotta and indigo.",
            materials=["cotton"],
            style=["artisanal", "block-printed"],
            motifs=["botanical", "floral"],
            colours=["terracotta", "indigo"],
            price_segment="mid_premium",
            price_min=35.0,
            price_max=85.0,
            currency="USD",
            moq=25,
            is_demo=True,
        )
        session.add(product)

        run = ResearchRunModel(
            id=uuid4(),
            owner_id=user_id,
            product_id=product.id,
            status="completed",
            stage="done",
        )
        session.add(run)

        lead = LeadModel(
            id=uuid4(),
            owner_id=user_id,
            run_id=run.id,
            product_id=product.id,
            name=lead_name,
            website=f"https://{canonical_domain}",
            canonical_domain=canonical_domain,
            tier="qualified",
            scores={"overall": 85.0, "category_fit": 100.0},
            review_status="new",
            is_demo=True,
        )
        session.add(lead)

        ev_models: list[LeadEvidenceModel] = []
        if with_evidence:
            ev1 = LeadEvidenceModel(
                id=uuid4(),
                owner_id=user_id,
                lead_id=lead.id,
                url=f"https://{canonical_domain}/about",
                excerpt="Curated independent boutique stocking artisan ceramics, handcrafted textiles, and botanical linens.",
                source_type="official_site",
                domain_matches_lead=True,
                provenance="verified_fact",
                is_demo=True,
            )
            session.add(ev1)
            ev_models.append(ev1)

            ev2 = LeadEvidenceModel(
                id=uuid4(),
                owner_id=user_id,
                lead_id=lead.id,
                url=f"https://{canonical_domain}/collections/linens",
                excerpt="Artisanal cotton table runners and napkins with botanical block prints.",
                source_type="product_page",
                domain_matches_lead=True,
                provenance="verified_fact",
                is_demo=True,
            )
            session.add(ev2)
            ev_models.append(ev2)

        await session.commit()
        await session.refresh(product)
        await session.refresh(lead)
        return product, lead, ev_models


# ==============================================================================
# 1. Outreach Draft Generation (Task D)
# ==============================================================================

@pytest.mark.asyncio
async def test_generate_outreach_draft_initial_version() -> None:
    """
    Verify POST /leads/{id}/outreach-drafts:
    - Generates draft with version=1, parent_draft_id=None, status='draft'.
    - Populates facts_used, warnings (D5), is_demo (D1).
    """
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    product, lead, evs = await _seed_lead_with_product_and_evidence(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        assert res.status_code == 201
        draft = OutreachDraft.model_validate(res.json())

        assert draft.lead_id == lead.id
        assert draft.product_id == product.id
        assert draft.owner_id == user_id
        assert draft.version == 1
        assert draft.parent_draft_id is None
        assert draft.status == OutreachDraftStatus.DRAFT
        assert len(draft.subject) > 0
        assert len(draft.body) > 0
        assert len(draft.facts_used) >= 1
        assert isinstance(draft.warnings, list)
        assert draft.is_demo is True


@pytest.mark.asyncio
async def test_subsequent_generation_increments_version_and_sets_parent() -> None:
    """Verify generating another draft for the same lead creates version 2 with parent_draft_id."""
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    product, lead, evs = await _seed_lead_with_product_and_evidence(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Version 1
        res1 = await client.post(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        assert res1.status_code == 201
        draft1 = OutreachDraft.model_validate(res1.json())
        assert draft1.version == 1

        # Version 2
        res2 = await client.post(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        assert res2.status_code == 201
        draft2 = OutreachDraft.model_validate(res2.json())
        assert draft2.version == 2
        assert draft2.parent_draft_id == draft1.id


# ==============================================================================
# 2. Lead Outreach Drafts Version History
# ==============================================================================

@pytest.mark.asyncio
async def test_get_lead_outreach_drafts_ordered_by_version_desc() -> None:
    """Verify GET /leads/{id}/outreach-drafts returns all draft versions ordered by version desc."""
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    product, lead, evs = await _seed_lead_with_product_and_evidence(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create versions 1 and 2
        await client.post(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        await client.post(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)

        res = await client.get(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        assert res.status_code == 200
        drafts = [OutreachDraft.model_validate(d) for d in res.json()]
        assert len(drafts) == 2
        assert drafts[0].version == 2
        assert drafts[1].version == 1


# ==============================================================================
# 3. Patching Draft & Atomic Lead review_status Update (D11)
# ==============================================================================

@pytest.mark.asyncio
async def test_patch_outreach_draft_in_place_updates() -> None:
    """Verify PATCH /outreach-drafts/{id} updates subject, body, followup_notes, and status=ready."""
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    product, lead, evs = await _seed_lead_with_product_and_evidence(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        draft = OutreachDraft.model_validate(res.json())

        patch_res = await client.patch(
            f"/api/v1/outreach-drafts/{draft.id}",
            json={
                "subject": "Tailored inquiry for Amsterdam stockist",
                "body": "Dear Atelier Living, we have reserved 50 pieces for you.",
                "status": "ready",
                "followup_notes": "Follow up after London Design Week.",
            },
            headers=headers,
        )
        assert patch_res.status_code == 200
        patched = OutreachDraft.model_validate(patch_res.json())
        assert patched.subject == "Tailored inquiry for Amsterdam stockist"
        assert patched.body == "Dear Atelier Living, we have reserved 50 pieces for you."
        assert patched.status == OutreachDraftStatus.READY
        assert patched.followup_notes == "Follow up after London Design Week."

        # Verify lead review_status is still 'new'
        lead_res = await client.get(f"/api/v1/leads/{lead.id}", headers=headers)
        assert lead_res.json()["review_status"] == "new"


@pytest.mark.asyncio
async def test_patch_status_contacted_atomically_updates_lead_review_status() -> None:
    """
    Verify DECISION-D11:
    When draft.status is set to 'contacted', the parent lead.review_status is
    atomically updated to 'contacted' in the same transaction.
    """
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    product, lead, evs = await _seed_lead_with_product_and_evidence(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        draft = OutreachDraft.model_validate(res.json())

        # Update draft to contacted
        patch_res = await client.patch(
            f"/api/v1/outreach-drafts/{draft.id}",
            json={"status": "contacted"},
            headers=headers,
        )
        assert patch_res.status_code == 200
        patched = OutreachDraft.model_validate(patch_res.json())
        assert patched.status == OutreachDraftStatus.CONTACTED

        # Verify parent lead.review_status is now contacted
        lead_res = await client.get(f"/api/v1/leads/{lead.id}", headers=headers)
        assert lead_res.status_code == 200
        lead_data = lead_res.json()
        assert lead_data["review_status"] == "contacted"


# ==============================================================================
# 4. Draft Regeneration (Inserts New Row, Preserves Existing)
# ==============================================================================

@pytest.mark.asyncio
async def test_regenerate_draft_inserts_new_row_and_preserves_edited_draft() -> None:
    """
    Verify POST /outreach-drafts/{id}/regenerate:
    - Calls draft_outreach passing current draft as previous.
    - Inserts a new row with version = max_version + 1 and parent_draft_id = id.
    - NEVER overwrites the existing edited draft.
    """
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    product, lead, evs = await _seed_lead_with_product_and_evidence(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create version 1
        res1 = await client.post(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        draft1 = OutreachDraft.model_validate(res1.json())

        # 2. Edit version 1
        await client.patch(
            f"/api/v1/outreach-drafts/{draft1.id}",
            json={"subject": "Manual artisan edit on v1", "status": "ready"},
            headers=headers,
        )

        # 3. Regenerate from version 1
        regen_res = await client.post(f"/api/v1/outreach-drafts/{draft1.id}/regenerate", headers=headers)
        assert regen_res.status_code == 201
        draft2 = OutreachDraft.model_validate(regen_res.json())

        # 4. Verify new draft has version=2 and parent_draft_id=draft1.id
        assert draft2.id != draft1.id
        assert draft2.version == 2
        assert draft2.parent_draft_id == draft1.id
        assert draft2.status == OutreachDraftStatus.DRAFT

        # 5. Verify draft1 was NOT overwritten and preserves edits
        lead_drafts_res = await client.get(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        drafts = [OutreachDraft.model_validate(d) for d in lead_drafts_res.json()]
        assert len(drafts) == 2

        d1_persisted = next(d for d in drafts if d.id == draft1.id)
        assert d1_persisted.subject == "Manual artisan edit on v1"
        assert d1_persisted.status == OutreachDraftStatus.READY


# ==============================================================================
# 5. Top-Level List Filtering (DECISION-D17)
# ==============================================================================

@pytest.mark.asyncio
async def test_list_outreach_drafts_filtering_and_sorting() -> None:
    """
    Verify GET /outreach-drafts:
    - Filters by status, product_id, lead_id.
    - Orders by updated_at desc.
    """
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    p1, l1, _ = await _seed_lead_with_product_and_evidence(user_id, "Shop 1", "shop1.test")
    p2, l2, _ = await _seed_lead_with_product_and_evidence(user_id, "Shop 2", "shop2.test")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create draft for l1 (draft status)
        r1 = await client.post(f"/api/v1/leads/{l1.id}/outreach-drafts", headers=headers)
        d1 = OutreachDraft.model_validate(r1.json())

        # Create draft for l2 and mark ready
        r2 = await client.post(f"/api/v1/leads/{l2.id}/outreach-drafts", headers=headers)
        d2 = OutreachDraft.model_validate(r2.json())
        await client.patch(
            f"/api/v1/outreach-drafts/{d2.id}",
            json={"status": "ready"},
            headers=headers,
        )

        # 1. Top-level list with no filter returns both
        all_res = await client.get("/api/v1/outreach-drafts", headers=headers)
        assert all_res.status_code == 200
        all_drafts = [OutreachDraft.model_validate(d) for d in all_res.json()]
        assert len(all_drafts) == 2
        # d2 was updated last, should appear first
        assert all_drafts[0].id == d2.id

        # 2. Filter by status=ready
        ready_res = await client.get("/api/v1/outreach-drafts?status=ready", headers=headers)
        assert ready_res.status_code == 200
        ready_drafts = [OutreachDraft.model_validate(d) for d in ready_res.json()]
        assert len(ready_drafts) == 1
        assert ready_drafts[0].id == d2.id

        # 3. Filter by product_id=p1.id
        p1_res = await client.get(f"/api/v1/outreach-drafts?product_id={p1.id}", headers=headers)
        assert p1_res.status_code == 200
        p1_drafts = [OutreachDraft.model_validate(d) for d in p1_res.json()]
        assert len(p1_drafts) == 1
        assert p1_drafts[0].id == d1.id

        # 4. Filter by lead_id=l2.id
        l2_res = await client.get(f"/api/v1/outreach-drafts?lead_id={l2.id}", headers=headers)
        assert l2_res.status_code == 200
        l2_drafts = [OutreachDraft.model_validate(d) for d in l2_res.json()]
        assert len(l2_drafts) == 1
        assert l2_drafts[0].id == d2.id


# ==============================================================================
# 6. Multi-Tenant User Isolation (Section 8)
# ==============================================================================

@pytest.mark.asyncio
async def test_user_isolation_returns_404_on_unowned_records() -> None:
    """
    Verify cross-user isolation:
    Accessing another user's lead or draft returns 404 not_found (never 403).
    """
    user_a = uuid4()
    user_b = uuid4()
    headers_a = make_auth_header(user_id=user_a)
    headers_b = make_auth_header(user_id=user_b)

    product_a, lead_a, _ = await _seed_lead_with_product_and_evidence(user_a)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # User A creates draft
        res = await client.post(f"/api/v1/leads/{lead_a.id}/outreach-drafts", headers=headers_a)
        assert res.status_code == 201
        draft_a = OutreachDraft.model_validate(res.json())

        # 1. User B attempts to generate draft for User A's lead -> 404
        post_res = await client.post(f"/api/v1/leads/{lead_a.id}/outreach-drafts", headers=headers_b)
        assert post_res.status_code == 404
        assert post_res.json()["error"]["code"] == "not_found"

        # 2. User B attempts to list drafts for User A's lead -> 404
        get_lead_res = await client.get(f"/api/v1/leads/{lead_a.id}/outreach-drafts", headers=headers_b)
        assert get_lead_res.status_code == 404
        assert get_lead_res.json()["error"]["code"] == "not_found"

        # 3. User B attempts to patch User A's draft -> 404
        patch_res = await client.patch(
            f"/api/v1/outreach-drafts/{draft_a.id}",
            json={"status": "contacted"},
            headers=headers_b,
        )
        assert patch_res.status_code == 404
        assert patch_res.json()["error"]["code"] == "not_found"

        # 4. User B attempts to regenerate User A's draft -> 404
        regen_res = await client.post(f"/api/v1/outreach-drafts/{draft_a.id}/regenerate", headers=headers_b)
        assert regen_res.status_code == 404
        assert regen_res.json()["error"]["code"] == "not_found"

        # 5. User B's top-level list does not include User A's draft
        list_res = await client.get("/api/v1/outreach-drafts", headers=headers_b)
        assert list_res.status_code == 200
        b_drafts = list_res.json()
        assert not any(d["id"] == str(draft_a.id) for d in b_drafts)


# ==============================================================================
# 7. Zero Evidence Lead Handling
# ==============================================================================

@pytest.mark.asyncio
async def test_zero_evidence_lead_adds_warning_without_failing() -> None:
    """Verify drafting outreach for a lead with no evidence succeeds with a warning."""
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    product, lead, _ = await _seed_lead_with_product_and_evidence(user_id, with_evidence=False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(f"/api/v1/leads/{lead.id}/outreach-drafts", headers=headers)
        assert res.status_code == 201
        draft = OutreachDraft.model_validate(res.json())
        assert draft.version == 1
        assert len(draft.warnings) >= 1
        assert any("personalize" in w.lower() or "no verified store excerpt" in w.lower() for w in draft.warnings)


# ==============================================================================
# 8. Verification: No Email Sending Endpoint Anywhere
# ==============================================================================

@pytest.mark.asyncio
async def test_no_email_sending_endpoint_exists() -> None:
    """
    Verify that NO email sending endpoint exists anywhere in the API.
    Per AGENT.md Section 14: Never add PayPal, payment code, or email-sending functionality.
    """
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    fake_id = uuid4()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Check standard email sending paths
        for path in [
            f"/api/v1/outreach-drafts/{fake_id}/send",
            f"/api/v1/outreach-drafts/{fake_id}/email",
            "/api/v1/outreach/send",
            "/api/v1/email/send",
        ]:
            res = await client.post(path, headers=headers)
            assert res.status_code in (404, 405), f"Path {path} returned {res.status_code}"

        # Inspect OpenAPI paths to confirm no send/email route is defined
        openapi_res = await client.get("/openapi.json")
        assert openapi_res.status_code == 200
        paths = openapi_res.json().get("paths", {})
        for p in paths:
            assert "send" not in p.lower(), f"Forbidden send endpoint in OpenAPI: {p}"
            assert "email" not in p.lower() or "profile" in p.lower(), f"Forbidden email endpoint: {p}"
