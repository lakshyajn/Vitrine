"""
Unit and integration tests for Tavily Contact Scraper & API endpoint.
"""

from __future__ import annotations

import time
from uuid import UUID, uuid4
import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.core.config import get_settings
from backend.app.db.models import LeadModel, ProductModel, ResearchRunModel
from backend.app.db.session import async_session_maker
from backend.app.main import app
from backend.research.contact_scraper import (
    clean_domain,
    extract_emails_from_text,
    score_and_rank_email,
    scrape_contact_email,
)

JWT_SECRET = "ws2-step7-jwt-secret-testing-key-111222"


@pytest.fixture(autouse=True)
def setup_jwt_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", JWT_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_auth_header(user_id: UUID | None = None) -> dict[str, str]:
    uid = user_id or uuid4()
    payload = {
        "sub": str(uid),
        "email": "test@artisan.test",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    _s = get_settings()
    if _s.supabase_url and "iss" not in payload:
        payload["iss"] = f"{_s.supabase_url.rstrip('/')}/auth/v1"
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_clean_domain():
    assert clean_domain("https://www.colmershill.com/about") == "colmershill.com"
    assert clean_domain("http://atelierlivingdemo.com:8000/") == "atelierlivingdemo.com"
    assert clean_domain("www.thebotanistshopdemo.co.uk") == "thebotanistshopdemo.co.uk"


def test_extract_emails_from_text():
    sample_text = """
    Contact us at wholesale@colmershill.com or info@colmershill.com!
    Ignore test@sentry.io and logo@2x.png or bogus@example.com.
    Also user@schema.org and noreply@colmershill.com should be ignored.
    """
    emails = extract_emails_from_text(sample_text, "colmershill.com")
    assert "wholesale@colmershill.com" in emails
    assert "info@colmershill.com" in emails
    assert "test@sentry.io" not in emails
    assert "logo@2x.png" not in emails
    assert "bogus@example.com" not in emails
    assert "noreply@colmershill.com" not in emails


def test_score_and_rank_email():
    dom = "colmershill.com"
    score_wholesale = score_and_rank_email("wholesale@colmershill.com", dom)
    score_info = score_and_rank_email("info@colmershill.com", dom)
    score_unrelated = score_and_rank_email("hello@externaldomain.com", dom)

    assert score_wholesale > score_info > score_unrelated


def test_placeholder_and_non_retailer_email_rejection():
    """Verify that fake, placeholder, and non-retailer emails are strictly rejected."""
    sample = """
    Contact: yourname@example.com, test@company.com, user@domain.com,
    info@email.com, test@test.com, noreply@myboutique.com,
    image@photo.png, and genuine@myboutique.com.
    """
    extracted = extract_emails_from_text(sample, "myboutique.com")
    assert "genuine@myboutique.com" in extracted
    assert "yourname@example.com" not in extracted
    assert "test@company.com" not in extracted
    assert "user@domain.com" not in extracted
    assert "info@email.com" not in extracted
    assert "test@test.com" not in extracted
    assert "noreply@myboutique.com" not in extracted
    assert "image@photo.png" not in extracted


@pytest.mark.asyncio
async def test_scrape_contact_email_offline_fallback():
    # Test fixture domain in test environment (TAVILY_API_KEY="")
    res = await scrape_contact_email("atelierlivingdemo.com", tavily_client=None)
    assert res["email"] == "contact@atelierlivingdemo.com"
    assert not res["is_fallback"]

    # Test unknown domain fallback: NEVER returns synthetic wholesale@
    res2 = await scrape_contact_email("unknownboutiquexyz.co.uk", tavily_client=None)
    assert res2["email"] == ""
    assert "wholesale@unknownboutiquexyz.co.uk" not in str(res2)
    assert res2["note"] == "No contact email found on public website" 


@pytest.mark.asyncio
async def test_lead_scrape_contact_api_endpoint():
    user_id = uuid4()
    auth_headers = make_auth_header(user_id=user_id)

    async with async_session_maker() as session:
        # Create product
        prod = ProductModel(
            id=uuid4(),
            owner_id=user_id,
            name="Handwoven Table Runner",
            category="Home",
            description="Cotton table runner",
        )
        session.add(prod)

        # Create run
        run = ResearchRunModel(
            id=uuid4(),
            owner_id=user_id,
            product_id=prod.id,
            status="completed",
            stage="done",
        )
        session.add(run)

        # Create lead
        lead = LeadModel(
            id=uuid4(),
            owner_id=user_id,
            run_id=run.id,
            product_id=prod.id,
            name="Atelier Living",
            website="https://atelierlivingdemo.com",
            canonical_domain="atelierlivingdemo.com",
            retailer_type="boutique",
            website_verified=True,
            tier="qualified",
            scores={"overall": 88.0},
            review_status="new",
            is_demo=True,
        )
        session.add(lead)
        await session.commit()
        lead_id = lead.id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Call scrape-contact endpoint
        scrape_resp = await client.post(
            f"/api/v1/leads/{lead_id}/scrape-contact",
            headers=auth_headers,
        )
        assert scrape_resp.status_code == 200
        data = scrape_resp.json()
        assert "email" in data
        assert data["email"] == "contact@atelierlivingdemo.com"
        assert data["lead_id"] == str(lead_id)

        # Verify that Lead record was updated in database
        get_resp = await client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        updated_lead = get_resp.json()
        assert updated_lead["contact_email"] == "contact@atelierlivingdemo.com"
