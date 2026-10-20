"""
Comprehensive tests for Profile and Products DB Persistence (Step 4).
Tests:
1. Profile GET auto-creation (DECISION-D16) & PUT persistence.
2. Products CRUD lifecycle and deterministic ordering.
3. Validation errors: moq < 1, price_min > price_max (returning 422 validation_error with field details).
4. User isolation: User A cannot read, update, upload images to, or delete User B's product (all return 404 not_found).
5. Cascade delete child records on DELETE /products/{id} (DECISION-D12).
6. Image upload with MIME type and size validation (DECISION-D18).
7. AI extract-profile returning suggested attributes without saving a product, plus error mapping.
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
    Product,
    ProductAttributes,
    Profile,
)
from backend.app.core.config import get_settings
from backend.app.db.models import (
    LeadEvidenceModel,
    LeadModel,
    MarketHypothesisModel,
    OutreachDraftModel,
    ProductModel,
    ProfileModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.session import async_session_maker, get_db_session
from backend.app.main import app

JWT_SECRET = "ws2-step4-testing-jwt-secret-999888"


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


# ==============================================================================
# 1. Profile Persistence & Auto-creation Tests (D16)
# ==============================================================================

@pytest.mark.asyncio
async def test_profile_auto_creation_on_first_get():
    """Verify GET /profile auto-creates an empty profile row if none exists."""
    user_id = uuid4()
    headers = auth_headers(user_id, email="artisan1@test.com")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First GET creates profile
        res1 = await client.get("/api/v1/profile", headers=headers)
        assert res1.status_code == 200
        data1 = res1.json()
        profile1 = Profile.model_validate(data1)
        assert profile1.user_id == user_id
        assert profile1.business_name == ""
        assert profile1.contact_email == "artisan1@test.com"

        # Second GET returns the same profile row without creating another
        res2 = await client.get("/api/v1/profile", headers=headers)
        assert res2.status_code == 200
        profile2 = Profile.model_validate(res2.json())
        assert profile2.id == profile1.id
        assert profile2.user_id == user_id


@pytest.mark.asyncio
async def test_profile_update_and_persistence():
    """Verify PUT /profile persists business_name, country, website, contact_email, about."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        update_payload = {
            "business_name": "Jaipur Block Print Studio",
            "country": "India",
            "website": "https://jaipurprints.test",
            "contact_email": "hello@jaipurprints.test",
            "about": "Artisanal hand block printing on natural cotton and linen fabrics.",
        }
        put_res = await client.put("/api/v1/profile", json=update_payload, headers=headers)
        assert put_res.status_code == 200
        updated = Profile.model_validate(put_res.json())
        assert updated.business_name == "Jaipur Block Print Studio"
        assert updated.country == "India"
        assert updated.website == "https://jaipurprints.test"
        assert updated.contact_email == "hello@jaipurprints.test"
        assert updated.about == update_payload["about"]

        # Verify persistence via subsequent GET
        get_res = await client.get("/api/v1/profile", headers=headers)
        assert get_res.status_code == 200
        fetched = Profile.model_validate(get_res.json())
        assert fetched.id == updated.id
        assert fetched.business_name == "Jaipur Block Print Studio"
        assert fetched.country == "India"


@pytest.mark.asyncio
async def test_profile_user_isolation():
    """Verify User A and User B maintain separate isolated profiles."""
    user_a = uuid4()
    user_b = uuid4()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # User A sets profile
        await client.put(
            "/api/v1/profile",
            json={"business_name": "User A Studio", "country": "India"},
            headers=auth_headers(user_a),
        )

        # User B sets profile
        await client.put(
            "/api/v1/profile",
            json={"business_name": "User B Workshop", "country": "Portugal"},
            headers=auth_headers(user_b),
        )

        # Verify User A sees User A's data
        res_a = await client.get("/api/v1/profile", headers=auth_headers(user_a))
        assert res_a.json()["business_name"] == "User A Studio"
        assert res_a.json()["country"] == "India"

        # Verify User B sees User B's data
        res_b = await client.get("/api/v1/profile", headers=auth_headers(user_b))
        assert res_b.json()["business_name"] == "User B Workshop"
        assert res_b.json()["country"] == "Portugal"


# ==============================================================================
# 2. Products CRUD Lifecycle & Ordering
# ==============================================================================

@pytest.mark.asyncio
async def test_products_crud_lifecycle_and_ordering():
    """Verify complete CRUD lifecycle: POST -> GET -> PUT -> DELETE."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Initially empty list
        empty_res = await client.get("/api/v1/products", headers=headers)
        assert empty_res.status_code == 200
        assert empty_res.json() == []

        # 1. Create Product 1
        payload1 = {
            "name": "Handmade Indigo Throw",
            "category": "Home Textiles",
            "description": "Natural dyed botanical indigo throw blanket.",
            "materials": ["cotton", "indigo"],
            "style": ["artisanal", "botanical"],
            "motifs": ["geometric", "floral"],
            "colours": ["indigo", "cream"],
            "price_segment": "mid_premium",
            "price_min": 40.0,
            "price_max": 95.0,
            "currency": "USD",
            "moq": 25,
            "monthly_capacity": 500,
            "target_retailer_types": ["boutique", "concept store"],
        }
        res1 = await client.post("/api/v1/products", json=payload1, headers=headers)
        assert res1.status_code == 201
        prod1 = Product.model_validate(res1.json())
        assert prod1.name == payload1["name"]
        assert prod1.owner_id == user_id
        assert prod1.moq == 25

        # 2. Create Product 2
        payload2 = {
            "name": "Terracotta Table Linen Set",
            "category": "Tableware",
            "description": "Block-printed linen placemats and napkins.",
            "moq": 10,
            "price_min": 20.0,
            "price_max": 50.0,
        }
        res2 = await client.post("/api/v1/products", json=payload2, headers=headers)
        assert res2.status_code == 201
        prod2 = Product.model_validate(res2.json())

        # 3. List products - check deterministic ordering (newest first: prod2 before prod1)
        list_res = await client.get("/api/v1/products", headers=headers)
        assert list_res.status_code == 200
        products = [Product.model_validate(p) for p in list_res.json()]
        assert len(products) == 2
        assert products[0].id == prod2.id
        assert products[1].id == prod1.id

        # 4. GET /products/{id}
        get_res = await client.get(f"/api/v1/products/{prod1.id}", headers=headers)
        assert get_res.status_code == 200
        retrieved = Product.model_validate(get_res.json())
        assert retrieved.id == prod1.id
        assert retrieved.name == payload1["name"]

        # 5. PUT /products/{id} - update name and price range
        update_payload = {
            "name": "Organic Indigo Throw (Updated)",
            "price_min": 45.0,
            "price_max": 110.0,
            "moq": 30,
        }
        put_res = await client.put(
            f"/api/v1/products/{prod1.id}",
            json=update_payload,
            headers=headers,
        )
        assert put_res.status_code == 200
        updated = Product.model_validate(put_res.json())
        assert updated.name == "Organic Indigo Throw (Updated)"
        assert updated.price_min == 45.0
        assert updated.price_max == 110.0
        assert updated.moq == 30

        # Verify update persisted
        verify_res = await client.get(f"/api/v1/products/{prod1.id}", headers=headers)
        assert verify_res.json()["name"] == "Organic Indigo Throw (Updated)"

        # 6. DELETE /products/{id}
        del_res = await client.delete(f"/api/v1/products/{prod1.id}", headers=headers)
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "deleted"

        # Verify product is gone
        get_deleted = await client.get(f"/api/v1/products/{prod1.id}", headers=headers)
        assert get_deleted.status_code == 404
        assert get_deleted.json()["error"]["code"] == "not_found"

        # Verify list now only has prod2
        remaining_res = await client.get("/api/v1/products", headers=headers)
        remaining = [Product.model_validate(p) for p in remaining_res.json()]
        assert len(remaining) == 1
        assert remaining[0].id == prod2.id


# ==============================================================================
# 3. Product Validation Errors (moq < 1, price_min > price_max)
# ==============================================================================

@pytest.mark.asyncio
async def test_product_validation_moq_below_one():
    """Verify creating a product with moq < 1 returns 422 validation_error with field details."""
    headers = auth_headers(uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test moq = 0
        res = await client.post(
            "/api/v1/products",
            json={
                "name": "Invalid MOQ Product",
                "category": "Home Textiles",
                "description": "Sample description.",
                "moq": 0,
            },
            headers=headers,
        )
        assert res.status_code == 422
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "validation_error"
        assert "moq" in data["error"]["details"]

        # Test negative moq
        res_neg = await client.post(
            "/api/v1/products",
            json={
                "name": "Invalid MOQ Product",
                "category": "Home Textiles",
                "description": "Sample description.",
                "moq": -5,
            },
            headers=headers,
        )
        assert res_neg.status_code == 422
        assert res_neg.json()["error"]["code"] == "validation_error"
        assert "moq" in res_neg.json()["error"]["details"]


@pytest.mark.asyncio
async def test_product_validation_price_min_greater_than_max():
    """Verify creating a product with price_min > price_max returns 422 validation_error."""
    headers = auth_headers(uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            "/api/v1/products",
            json={
                "name": "Inverted Price Product",
                "category": "Home Textiles",
                "description": "Sample description.",
                "price_min": 150.0,
                "price_max": 50.0,
            },
            headers=headers,
        )
        assert res.status_code == 422
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "validation_error"
        assert "price_min" in data["error"]["details"]


@pytest.mark.asyncio
async def test_product_update_validation_errors():
    """Verify PUT /products/{id} enforces price_min <= price_max and moq >= 1."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create valid base product
        post_res = await client.post(
            "/api/v1/products",
            json={
                "name": "Valid Product",
                "category": "Textiles",
                "description": "Valid description.",
                "price_min": 30.0,
                "price_max": 80.0,
                "moq": 10,
            },
            headers=headers,
        )
        assert post_res.status_code == 201
        prod_id = post_res.json()["id"]

        # 1. Update with invalid moq < 1
        bad_moq = await client.put(
            f"/api/v1/products/{prod_id}",
            json={"moq": 0},
            headers=headers,
        )
        assert bad_moq.status_code == 422
        assert bad_moq.json()["error"]["code"] == "validation_error"
        assert "moq" in bad_moq.json()["error"]["details"]

        # 2. Update price_min higher than existing price_max (80.0)
        bad_price = await client.put(
            f"/api/v1/products/{prod_id}",
            json={"price_min": 100.0},
            headers=headers,
        )
        assert bad_price.status_code == 422
        assert bad_price.json()["error"]["code"] == "validation_error"
        assert "price_min" in bad_price.json()["error"]["details"]


# ==============================================================================
# 4. User Isolation Tests (Defense-in-Depth, 404 Not Found)
# ==============================================================================

@pytest.mark.asyncio
async def test_product_user_isolation_returns_404():
    """
    Verify User A cannot read, update, upload images to, or delete User B's product.
    All operations must return 404 not_found (never 403).
    """
    user_a = uuid4()
    user_b = uuid4()
    headers_a = auth_headers(user_a)
    headers_b = auth_headers(user_b)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # User B creates a product
        create_res = await client.post(
            "/api/v1/products",
            json={
                "name": "User B Secret Product",
                "category": "Textiles",
                "description": "Confidential artisan craft.",
                "price_min": 50.0,
                "price_max": 100.0,
                "moq": 5,
            },
            headers=headers_b,
        )
        assert create_res.status_code == 201
        prod_b_id = create_res.json()["id"]

        # User A cannot see User B's product in GET /products
        list_a = await client.get("/api/v1/products", headers=headers_a)
        assert list_a.status_code == 200
        ids_a = [p["id"] for p in list_a.json()]
        assert prod_b_id not in ids_a

        # User A cannot GET User B's product (must return 404, never 403)
        get_res = await client.get(f"/api/v1/products/{prod_b_id}", headers=headers_a)
        assert get_res.status_code == 404
        assert get_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # User A cannot PUT User B's product (must return 404, never 403)
        put_res = await client.put(
            f"/api/v1/products/{prod_b_id}",
            json={"name": "Tampered By User A"},
            headers=headers_a,
        )
        assert put_res.status_code == 404
        assert put_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # User A cannot upload images to User B's product (must return 404, never 403)
        img_res = await client.post(
            f"/api/v1/products/{prod_b_id}/images",
            files={"file": ("hack.jpg", b"fake-img", "image/jpeg")},
            headers=headers_a,
        )
        assert img_res.status_code == 404
        assert img_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # User A cannot DELETE User B's product (must return 404, never 403)
        del_res = await client.delete(f"/api/v1/products/{prod_b_id}", headers=headers_a)
        assert del_res.status_code == 404
        assert del_res.json()["error"]["code"] == ErrorCode.NOT_FOUND.value

        # Verify User B's product is completely intact
        verify_b = await client.get(f"/api/v1/products/{prod_b_id}", headers=headers_b)
        assert verify_b.status_code == 200
        assert verify_b.json()["name"] == "User B Secret Product"


# ==============================================================================
# 5. Cascade Deletion of Child Records (DECISION-D12)
# ==============================================================================

@pytest.mark.asyncio
async def test_product_cascade_deletion():
    """Verify DELETE /products/{id} cascades to research runs, leads, evidence, anchors, hypotheses, drafts."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create product
        prod_res = await client.post(
            "/api/v1/products",
            json={
                "name": "Cascade Parent Product",
                "category": "Textiles",
                "description": "Parent product for cascade test.",
                "moq": 1,
            },
            headers=headers,
        )
        assert prod_res.status_code == 201
        prod_id = UUID(prod_res.json()["id"])

    # 2. Directly insert child records in DB to simulate active research workflow
    async with async_session_maker() as session:
        # Create research run
        run = ResearchRunModel(
            owner_id=user_id,
            product_id=prod_id,
            status="completed",
            stage="done",
            inputs={},
            provider_modes={"taste": "mock", "search": "mock", "ai": "mock"},
        )
        session.add(run)
        await session.flush()

        # Create taste anchor & hypothesis
        anchor = TasteAnchorModel(
            owner_id=user_id,
            run_id=run.id,
            label="Artisan Decor",
            source="ai_proposed",
            status="confirmed",
            metadata_json={},
            is_demo=True,
        )
        hypothesis = MarketHypothesisModel(
            owner_id=user_id,
            run_id=run.id,
            title="Design Shops Hypothesis",
            signals=[],
            status="confirmed",
        )
        session.add_all([anchor, hypothesis])

        # Create lead
        lead = LeadModel(
            owner_id=user_id,
            run_id=run.id,
            product_id=prod_id,
            name="Cascade Lead Shop",
            website="https://cascadelead.test",
            canonical_domain="cascadelead.test",
            tier="qualified",
            scores={},
            is_demo=True,
        )
        session.add(lead)
        await session.flush()

        # Create lead evidence & outreach draft
        evidence = LeadEvidenceModel(
            owner_id=user_id,
            lead_id=lead.id,
            url="https://cascadelead.test/about",
            excerpt="High end decor boutique",
            is_demo=True,
        )
        draft = OutreachDraftModel(
            owner_id=user_id,
            lead_id=lead.id,
            product_id=prod_id,
            version=1,
            subject="Hello",
            body="Outreach body",
            facts_used=[],
            warnings=[],
            status="draft",
        )
        session.add_all([evidence, draft])
        await session.commit()

        # Verify child records exist
        assert (await session.execute(select(ResearchRunModel).where(ResearchRunModel.product_id == prod_id))).scalar_one_or_none() is not None
        assert (await session.execute(select(LeadModel).where(LeadModel.product_id == prod_id))).scalar_one_or_none() is not None
        assert (await session.execute(select(OutreachDraftModel).where(OutreachDraftModel.product_id == prod_id))).scalar_one_or_none() is not None

    # 3. Call DELETE /products/{id}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        del_res = await client.delete(f"/api/v1/products/{prod_id}", headers=headers)
        assert del_res.status_code == 200

    # 4. Verify in DB that product and ALL children were deleted
    async with async_session_maker() as session:
        assert (await session.execute(select(ProductModel).where(ProductModel.id == prod_id))).scalar_one_or_none() is None
        assert (await session.execute(select(ResearchRunModel).where(ResearchRunModel.product_id == prod_id))).scalar_one_or_none() is None
        assert (await session.execute(select(LeadModel).where(LeadModel.product_id == prod_id))).scalar_one_or_none() is None
        assert (await session.execute(select(OutreachDraftModel).where(OutreachDraftModel.product_id == prod_id))).scalar_one_or_none() is None
        assert (await session.execute(select(TasteAnchorModel).where(TasteAnchorModel.run_id == run.id))).scalar_one_or_none() is None
        assert (await session.execute(select(MarketHypothesisModel).where(MarketHypothesisModel.run_id == run.id))).scalar_one_or_none() is None
        assert (await session.execute(select(LeadEvidenceModel).where(LeadEvidenceModel.lead_id == lead.id))).scalar_one_or_none() is None


# ==============================================================================
# 6. Product Image Upload Tests (DECISION-D18)
# ==============================================================================

@pytest.mark.asyncio
async def test_product_image_upload_and_validation():
    """Verify POST /products/{id}/images validates MIME type, size, uploads to storage, and updates images."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create product
        prod_res = await client.post(
            "/api/v1/products",
            json={
                "name": "Image Test Runner",
                "category": "Home Textiles",
                "description": "Testing image uploads.",
                "moq": 1,
            },
            headers=headers,
        )
        assert prod_res.status_code == 201
        prod_id = prod_res.json()["id"]

        # 1. Valid JPEG upload
        img1_res = await client.post(
            f"/api/v1/products/{prod_id}/images",
            files={"file": ("runner_front.jpg", b"fake-jpeg-bytes-12345", "image/jpeg")},
            headers=headers,
        )
        assert img1_res.status_code == 200
        urls1 = img1_res.json()
        assert isinstance(urls1, list)
        assert len(urls1) == 1
        assert str(user_id) in urls1[0]
        assert str(prod_id) in urls1[0]
        assert "runner_front.jpg" in urls1[0]

        # 2. Valid PNG upload (appends to list)
        img2_res = await client.post(
            f"/api/v1/products/{prod_id}/images",
            files={"file": ("runner_detail.png", b"fake-png-bytes-67890", "image/png")},
            headers=headers,
        )
        assert img2_res.status_code == 200
        urls2 = img2_res.json()
        assert len(urls2) == 2
        assert urls2[0] == urls1[0]
        assert "runner_detail.png" in urls2[1]

        # 3. Verify GET /products/{id} reflects updated images array
        get_res = await client.get(f"/api/v1/products/{prod_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["images"] == urls2

        # 4. Reject disallowed MIME type (e.g. PDF or text)
        bad_mime = await client.post(
            f"/api/v1/products/{prod_id}/images",
            files={"file": ("document.pdf", b"fake-pdf-content", "application/pdf")},
            headers=headers,
        )
        assert bad_mime.status_code == 422
        assert bad_mime.json()["error"]["code"] == "validation_error"
        assert "file" in bad_mime.json()["error"]["details"]

        # 5. Reject empty file
        empty_file = await client.post(
            f"/api/v1/products/{prod_id}/images",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
            headers=headers,
        )
        assert empty_file.status_code == 422
        assert empty_file.json()["error"]["code"] == "validation_error"

        # 6. Reject file exceeding 5MB
        huge_bytes = b"X" * (5 * 1024 * 1024 + 100)
        huge_file = await client.post(
            f"/api/v1/products/{prod_id}/images",
            files={"file": ("huge.jpg", huge_bytes, "image/jpeg")},
            headers=headers,
        )
        assert huge_file.status_code == 422
        assert huge_file.json()["error"]["code"] == "validation_error"
        assert "5MB" in huge_file.json()["error"]["message"]


# ==============================================================================
# 7. AI Extract Profile Tests (DECISION-D19)
# ==============================================================================

@pytest.mark.asyncio
async def test_extract_profile_returns_attributes_without_saving():
    """Verify POST /products/extract-profile calls structure_product and does NOT save to DB."""
    user_id = uuid4()
    headers = auth_headers(user_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Initial products count for user
        initial_list = await client.get("/api/v1/products", headers=headers)
        assert len(initial_list.json()) == 0

        # Call extract-profile
        extract_res = await client.post(
            "/api/v1/products/extract-profile",
            json={
                "description": (
                    "Hand block printed cotton table runners featuring botanical and floral motifs "
                    "with indigo natural dye. Positioned at mid-premium with MOQ 50 sets."
                ),
            },
            headers=headers,
        )
        assert extract_res.status_code == 200
        attrs = ProductAttributes.model_validate(extract_res.json())
        assert len(attrs.style) > 0
        assert len(attrs.motifs) > 0
        assert len(attrs.colours) > 0
        assert attrs.moq is not None
        assert attrs.moq >= 1

        # Verify nothing was written to the database
        after_list = await client.get("/api/v1/products", headers=headers)
        assert len(after_list.json()) == 0


@pytest.mark.asyncio
async def test_extract_profile_error_mapping(monkeypatch):
    """Verify timeout and invalid output exceptions map to standard ErrorCode values."""
    headers = auth_headers(uuid4())

    class TimeoutAIService:
        async def structure_product(self, desc, known):
            raise asyncio.TimeoutError("Upstream Nebius model timed out")

    class InvalidOutputAIService:
        async def structure_product(self, desc, known):
            raise ValueError("ai_output_invalid: model output JSON failed schema validation")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test Timeout -> upstream_timeout (504)
        monkeypatch.setattr("backend.app.api.products.get_ai_service", lambda: TimeoutAIService())
        timeout_res = await client.post(
            "/api/v1/products/extract-profile",
            json={"description": "Some description"},
            headers=headers,
        )
        assert timeout_res.status_code == 504
        assert timeout_res.json()["error"]["code"] == ErrorCode.UPSTREAM_TIMEOUT.value

        # 2. Test Invalid Output -> ai_output_invalid (502)
        monkeypatch.setattr("backend.app.api.products.get_ai_service", lambda: InvalidOutputAIService())
        invalid_res = await client.post(
            "/api/v1/products/extract-profile",
            json={"description": "Some description"},
            headers=headers,
        )
        assert invalid_res.status_code == 502
        assert invalid_res.json()["error"]["code"] == ErrorCode.AI_OUTPUT_INVALID.value
