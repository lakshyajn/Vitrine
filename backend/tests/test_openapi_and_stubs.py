"""
Tests for OpenAPI generation, authentication enforcement, and stub responses (Step 3).
Verifies:
1. /openapi.json generates cleanly and contains all contract paths.
2. Unauthenticated calls to protected routes return 401 unauthorized in A.5 envelope.
3. Authenticated calls return schema-valid objects matching the Fixed Demo Scenario.
"""

from __future__ import annotations

import asyncio
import time
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
import jwt
import pytest

from contracts.schemas import (
    Lead,
    LeadPagedResponse,
    MarketHypothesis,
    OutreachDraft,
    Product,
    ProductAttributes,
    Profile,
    ResearchRun,
    ResearchRunActionResponse,
    TasteAnchor,
    TasteAnchorSource,
)
from backend.app.core.config import get_settings
from backend.app.main import app

JWT_SECRET = "ws2-step3-jwt-secret-testing-key-777888"


@pytest.fixture(autouse=True)
def setup_jwt_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_auth_header(user_id=None, email="artisan@sampleseller.test") -> dict[str, str]:
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


@pytest.mark.asyncio
async def test_openapi_spec_generation():
    """Verify that /openapi.json is served, valid, and documents all 21 endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/openapi.json")
        assert res.status_code == 200
        schema = res.json()

        assert "openapi" in schema
        assert "paths" in schema
        paths = schema["paths"]

        expected_paths = [
            "/api/v1/health",
            "/api/v1/integrations/status",
            "/api/v1/profile",
            "/api/v1/products",
            "/api/v1/products/{id}",
            "/api/v1/products/{id}/images",
            "/api/v1/products/extract-profile",
            "/api/v1/research-runs",
            "/api/v1/research-runs/{id}",
            "/api/v1/research-runs/{id}/rerun",
            "/api/v1/research-runs/{id}/anchors",
            "/api/v1/taste-anchors/{id}",
            "/api/v1/research-runs/{id}/confirm-anchors",
            "/api/v1/research-runs/{id}/hypotheses",
            "/api/v1/leads",
            "/api/v1/leads/{id}",
            "/api/v1/leads/{id}/evidence",
            "/api/v1/outreach-drafts",
            "/api/v1/leads/{id}/outreach-drafts",
            "/api/v1/outreach-drafts/{id}",
            "/api/v1/outreach-drafts/{id}/regenerate",
        ]

        for p in expected_paths:
            assert p in paths, f"Path {p} missing from OpenAPI schema"


@pytest.mark.asyncio
async def test_auth_enforcement_on_protected_endpoints():
    """Verify that protected endpoints reject unauthenticated requests with 401 unauthorized."""
    dummy_id = uuid4()
    endpoints_to_test = [
        ("GET", "/api/v1/profile"),
        ("GET", "/api/v1/products"),
        ("POST", "/api/v1/products"),
        ("GET", f"/api/v1/products/{dummy_id}"),
        ("GET", "/api/v1/research-runs"),
        ("POST", "/api/v1/research-runs"),
        ("GET", f"/api/v1/research-runs/{dummy_id}"),
        ("GET", "/api/v1/leads"),
        ("GET", f"/api/v1/leads/{dummy_id}"),
        ("GET", "/api/v1/outreach-drafts"),
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for method, path in endpoints_to_test:
            if method == "GET":
                res = await client.get(path)
            elif method == "POST":
                res = await client.post(path, json={})
            assert res.status_code == 401, f"{method} {path} did not return 401"
            assert res.json()["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_profile_endpoints_stub():
    """Verify GET /profile and PUT /profile return valid Profile models."""
    headers = make_auth_header()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # GET /profile
        res = await client.get("/api/v1/profile", headers=headers)
        assert res.status_code == 200
        profile = Profile.model_validate(res.json())
        assert isinstance(profile.business_name, str)

        # PUT /profile
        put_res = await client.put(
            "/api/v1/profile",
            json={"business_name": "Updated Workshop"},
            headers=headers,
        )
        assert put_res.status_code == 200
        updated = Profile.model_validate(put_res.json())
        assert updated.business_name == "Updated Workshop"


@pytest.mark.asyncio
async def test_products_endpoints_stub():
    """Verify products CRUD, image upload, and extract-profile return valid schemas."""
    headers = make_auth_header()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. POST /products
        post_res = await client.post(
            "/api/v1/products",
            json={
                "name": "Botanical Cushion Set",
                "category": "Home Decor",
                "description": "Block-printed cushion covers.",
                "price_segment": "mid_premium",
                "price_min": 25.0,
                "price_max": 60.0,
                "moq": 50,
            },
            headers=headers,
        )
        assert post_res.status_code == 201
        created = Product.model_validate(post_res.json())
        assert created.name == "Botanical Cushion Set"
        prod_id = created.id

        # 2. GET /products
        res = await client.get("/api/v1/products", headers=headers)
        assert res.status_code == 200
        products = [Product.model_validate(p) for p in res.json()]
        assert len(products) >= 1
        assert products[0].price_min == 25.0

        # 3. GET /products/{id}
        get_res = await client.get(f"/api/v1/products/{prod_id}", headers=headers)
        assert get_res.status_code == 200
        retrieved = Product.model_validate(get_res.json())
        assert retrieved.id == prod_id

        # 4. PUT /products/{id}
        put_res = await client.put(
            f"/api/v1/products/{prod_id}",
            json={"name": "Updated Cushion Set"},
            headers=headers,
        )
        assert put_res.status_code == 200
        updated = Product.model_validate(put_res.json())
        assert updated.name == "Updated Cushion Set"

        # 5. POST /products/{id}/images
        img_res = await client.post(
            f"/api/v1/products/{prod_id}/images",
            files={"file": ("sample.jpg", b"fake-image-bytes", "image/jpeg")},
            headers=headers,
        )
        assert img_res.status_code == 200
        img_urls = img_res.json()
        assert isinstance(img_urls, list)
        assert len(img_urls) >= 1

        # 6. DELETE /products/{id}
        del_res = await client.delete(f"/api/v1/products/{prod_id}", headers=headers)
        assert del_res.status_code == 200

        # 7. POST /products/extract-profile
        extract_res = await client.post(
            "/api/v1/products/extract-profile",
            json={"description": "Handcrafted botanical linen runners and throws."},
            headers=headers,
        )
        assert extract_res.status_code == 200
        attrs = ProductAttributes.model_validate(extract_res.json())
        assert len(attrs.style) > 0


@pytest.mark.asyncio
async def test_research_runs_endpoints_stub():
    """Verify research runs lifecycle endpoints return valid models."""
    headers = make_auth_header()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 0. Create product so run has a valid product_id
        prod_res = await client.post(
            "/api/v1/products",
            json={
                "name": "Run Test Product",
                "category": "Home Textiles",
                "description": "Product for research runs testing.",
                "moq": 1,
            },
            headers=headers,
        )
        assert prod_res.status_code == 201
        prod_id = prod_res.json()["id"]

        # 1. POST /research-runs
        create_res = await client.post(
            "/api/v1/research-runs",
            json={"product_id": str(prod_id), "inputs": {"regions": ["Europe"]}},
            headers=headers,
        )
        assert create_res.status_code == 201
        run_act = ResearchRunActionResponse.model_validate(create_res.json())
        assert run_act.status == "queued"
        run_id = run_act.id

        # Wait briefly for Phase 1 runner to reach awaiting_review
        for _ in range(30):
            check_res = await client.get(f"/api/v1/research-runs/{run_id}", headers=headers)
            if check_res.json().get("status") == "awaiting_review":
                break
            await asyncio.sleep(0.05)

        # 2. GET /research-runs
        list_res = await client.get("/api/v1/research-runs", headers=headers)
        assert list_res.status_code == 200
        runs = [ResearchRun.model_validate(r) for r in list_res.json()]
        assert len(runs) >= 1

        # 3. GET /research-runs/{id}
        get_res = await client.get(f"/api/v1/research-runs/{run_id}", headers=headers)
        assert get_res.status_code == 200
        retrieved_run = ResearchRun.model_validate(get_res.json())
        assert retrieved_run.id == run_id

        # 4. POST /research-runs/{id}/rerun
        rerun_res = await client.post(f"/api/v1/research-runs/{run_id}/rerun", headers=headers)
        assert rerun_res.status_code == 200
        assert rerun_res.json()["status"] == "queued"

        # 5. GET /research-runs/{id}/anchors
        anchors_res = await client.get(f"/api/v1/research-runs/{run_id}", headers=headers)
        anchors_res = await client.get(f"/api/v1/research-runs/{run_id}/anchors", headers=headers)
        assert anchors_res.status_code == 200
        anchors = [TasteAnchor.model_validate(a) for a in anchors_res.json()]
        assert len(anchors) >= 1

        # 6. POST /research-runs/{id}/anchors (D3 custom anchor)
        custom_res = await client.post(
            f"/api/v1/research-runs/{run_id}/anchors",
            json={"label": "Custom Ceramic Aesthetic", "entity_type": "brand"},
            headers=headers,
        )
        assert custom_res.status_code == 201
        custom_anchor = TasteAnchor.model_validate(custom_res.json())
        assert custom_anchor.source == "user_added"
        assert custom_anchor.is_demo is False

        # 7. PATCH /taste-anchors/{id}
        patch_res = await client.patch(
            f"/api/v1/taste-anchors/{custom_anchor.id}",
            json={"status": "confirmed"},
            headers=headers,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "confirmed"

        # 8. POST /research-runs/{id}/confirm-anchors (D4)
        confirm_res = await client.post(
            f"/api/v1/research-runs/{run_id}/confirm-anchors",
            json={"proceed_without_anchors": False},
            headers=headers,
        )
        assert confirm_res.status_code == 200
        confirmed_run = ResearchRun.model_validate(confirm_res.json())
        assert confirmed_run.stage == "discovery"

        # 9. GET /research-runs/{id}/hypotheses
        hypo_res = await client.get(f"/api/v1/research-runs/{run_id}/hypotheses", headers=headers)
        assert hypo_res.status_code == 200
        hypos = [MarketHypothesis.model_validate(h) for h in hypo_res.json()]
        assert len(hypos) >= 1

        # Await Phase 2 runner completion to prevent background task bleeding into next test
        for _ in range(50):
            r_check = await client.get(f"/api/v1/research-runs/{run_id}", headers=headers)
            if r_check.json().get("status") in ("completed", "failed"):
                break
            await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_leads_and_evidence_endpoints_stub():
    """Verify leads listing, detail, patch, and evidence endpoints return valid models."""
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    lead_id = uuid4()
    run_id = uuid4()
    prod_id = uuid4()

    from backend.app.db.models import LeadEvidenceModel, LeadModel, ProductModel, ResearchRunModel
    from backend.app.db.session import async_session_maker

    async with async_session_maker() as session:
        session.add(
            ProductModel(
                id=prod_id,
                owner_id=user_id,
                name="Test Linen Runner",
                category="Table Linens",
                description="Test description.",
                moq=1,
            )
        )
        session.add(
            ResearchRunModel(
                id=run_id,
                owner_id=user_id,
                product_id=prod_id,
                status="completed",
                stage="done",
            )
        )
        session.add(
            LeadModel(
                id=lead_id,
                owner_id=user_id,
                run_id=run_id,
                product_id=prod_id,
                name="Atelier Living & Design",
                website="https://atelierlivingdemo.com",
                canonical_domain="atelierlivingdemo.com",
                location={"city": "Amsterdam", "region": "North Holland", "country": "Netherlands"},
                retailer_type="Independent Home Decor Boutique",
                website_verified=True,
                tier="qualified",
                scores={
                    "category_fit": 100.0,
                    "aesthetic_fit": 100.0,
                    "evidence_quality": 80.0,
                    "seller_compat": 60.0,
                    "overall": 88.0,
                    "completeness": 1.0,
                    "tier_reasons": ["Verified site"],
                },
                review_status="new",
                notes="High priority target.",
                is_demo=True,
            )
        )
        session.add(
            LeadEvidenceModel(
                id=uuid4(),
                owner_id=user_id,
                lead_id=lead_id,
                url="https://atelierlivingdemo.com/about",
                excerpt="Artisanal home goods and table linens.",
                source_type="official_site",
                domain_matches_lead=True,
                provenance="verified_fact",
                is_demo=True,
            )
        )
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. GET /leads (D7 pagination envelope)
        list_res = await client.get("/api/v1/leads?page=1&page_size=10", headers=headers)
        assert list_res.status_code == 200
        paged = LeadPagedResponse.model_validate(list_res.json())
        assert paged.total == 1
        assert len(paged.items) == 1
        assert paged.items[0].scores.category_fit == 100.0

        # 2. GET /leads/{id}
        get_res = await client.get(f"/api/v1/leads/{lead_id}", headers=headers)
        assert get_res.status_code == 200
        lead = Lead.model_validate(get_res.json())
        assert lead.id == lead_id

        # 3. PATCH /leads/{id}
        patch_res = await client.patch(
            f"/api/v1/leads/{lead_id}",
            json={"review_status": "saved", "notes": "Contact in November"},
            headers=headers,
        )
        assert patch_res.status_code == 200
        patched = Lead.model_validate(patch_res.json())
        assert patched.review_status == "saved"
        assert patched.notes == "Contact in November"

        # 4. GET /leads/{id}/evidence
        ev_res = await client.get(f"/api/v1/leads/{lead_id}/evidence", headers=headers)
        assert ev_res.status_code == 200
        evidence_list = ev_res.json()
        assert len(evidence_list) >= 1
        assert evidence_list[0]["domain_matches_lead"] is True


@pytest.mark.asyncio
async def test_outreach_endpoints_stub():
    """Verify outreach draft endpoints return valid OutreachDraft models."""
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    lead_id = uuid4()
    prod_id = uuid4()
    run_id = uuid4()

    from backend.app.db.models import LeadEvidenceModel, LeadModel, ProductModel, ResearchRunModel
    from backend.app.db.session import async_session_maker

    async with async_session_maker() as session:
        session.add(
            ProductModel(
                id=prod_id,
                owner_id=user_id,
                name="Test Linen Runner",
                category="Table Linens",
                description="Test description.",
                moq=1,
            )
        )
        session.add(
            ResearchRunModel(
                id=run_id,
                owner_id=user_id,
                product_id=prod_id,
                status="completed",
                stage="done",
            )
        )
        session.add(
            LeadModel(
                id=lead_id,
                owner_id=user_id,
                run_id=run_id,
                product_id=prod_id,
                name="Atelier Living & Design",
                website="https://atelierlivingdemo.com",
                canonical_domain="atelierlivingdemo.com",
                tier="qualified",
                review_status="new",
            )
        )
        session.add(
            LeadEvidenceModel(
                id=uuid4(),
                owner_id=user_id,
                lead_id=lead_id,
                url="https://atelierlivingdemo.com/about",
                excerpt="Artisanal home goods and table linens.",
                source_type="official_site",
                domain_matches_lead=True,
                provenance="verified_fact",
            )
        )
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. POST /leads/{id}/outreach-drafts
        create_res = await client.post(f"/api/v1/leads/{lead_id}/outreach-drafts", headers=headers)
        assert create_res.status_code == 201
        draft = OutreachDraft.model_validate(create_res.json())
        assert draft.lead_id == lead_id
        assert draft.version == 1
        draft_id = draft.id

        # 2. GET /outreach-drafts (D17)
        list_res = await client.get("/api/v1/outreach-drafts", headers=headers)
        assert list_res.status_code == 200
        drafts = [OutreachDraft.model_validate(d) for d in list_res.json()]
        assert len(drafts) >= 1

        # 3. GET /leads/{id}/outreach-drafts
        lead_drafts_res = await client.get(f"/api/v1/leads/{lead_id}/outreach-drafts", headers=headers)
        assert lead_drafts_res.status_code == 200
        assert len(lead_drafts_res.json()) >= 1

        # 4. PATCH /outreach-drafts/{id}
        patch_res = await client.patch(
            f"/api/v1/outreach-drafts/{draft_id}",
            json={"status": "ready", "subject": "Customized Subject Line"},
            headers=headers,
        )
        assert patch_res.status_code == 200
        patched_draft = OutreachDraft.model_validate(patch_res.json())
        assert patched_draft.status == "ready"
        assert patched_draft.subject == "Customized Subject Line"

        # 5. POST /outreach-drafts/{id}/regenerate
        regen_res = await client.post(f"/api/v1/outreach-drafts/{draft_id}/regenerate", headers=headers)
        assert regen_res.status_code == 201
        new_version_draft = OutreachDraft.model_validate(regen_res.json())
        assert new_version_draft.version == 2
        assert new_version_draft.parent_draft_id == draft_id
