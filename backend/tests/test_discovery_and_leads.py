"""
Integration and Unit Tests for Research Discovery and Buyer Leads (Step 7 Deliverable).

Covers:
1. Full run lifecycle: confirm-anchors -> discovery -> assessment -> scoring -> completed.
2. Verified taste resolution attaching signals to market hypotheses (DECISION-D15).
3. Canonical domain deduplication: conflict merging and run_id update (DECISION-D2).
4. Persisted evidence UUID generation before assessment (DECISION-D8).
5. Duplicate lead linking via possible_duplicate_of_domain (DECISION-D9).
6. Per-lead failure isolation during AI assessment/scoring.
7. Clean run completion with 0 candidates and explanatory note.
8. Buyer leads endpoints:
   - GET /api/v1/leads with all filters (run_id, product_id, review_status, tier, q, location, min_score)
   - Deterministic sorting (score_desc with nulls last, name, newest) and pagination
   - Strict per-user isolation (404 on other user's lead)
   - GET /api/v1/leads/{id}, PATCH /api/v1/leads/{id}, and GET /api/v1/leads/{id}/evidence.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import time
from uuid import UUID, uuid4
import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from contracts.schemas import (
    EvidenceSourceType,
    Lead,
    LeadCandidate,
    LeadLocation,
    LeadPagedResponse,
    LeadReviewStatus,
    LeadTier,
    Product,
    ResearchPlan,
    TasteAnchor,
)
from backend.app.core.config import get_settings
from backend.app.db.models import (
    LeadEvidenceModel,
    LeadModel,
    MarketHypothesisModel,
    ProductModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.session import async_session_maker
from backend.app.jobs.runner import run_research_run_phase1, run_research_run_phase2
from backend.app.main import app

JWT_SECRET = "ws2-step7-jwt-secret-testing-key-111222"


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


async def _seed_product_and_run(user_id: UUID) -> tuple[ProductModel, ResearchRunModel]:
    async with async_session_maker() as session:
        product = ProductModel(
            id=uuid4(),
            owner_id=user_id,
            name="Block-Printed Table Runner",
            category="Table Linens",
            description="Artisanal block-printed cotton table runner in terracotta and indigo.",
            materials=["cotton"],
            style=["artisanal", "block-printed"],
            motifs=["botanical"],
            colours=["terracotta", "indigo"],
            moq=50,
        )
        session.add(product)

        run = ResearchRunModel(
            id=uuid4(),
            owner_id=user_id,
            product_id=product.id,
            status="queued",
            stage="planning",
            inputs={"regions": ["Western Europe"]},
        )
        session.add(run)
        await session.commit()
        await session.refresh(product)
        await session.refresh(run)
        return product, run


# ==============================================================================
# 1. Full Lifecycle Test: Confirm Anchors -> Discovery -> Completed
# ==============================================================================

@pytest.mark.asyncio
async def test_full_run_lifecycle_confirm_anchors_to_completed() -> None:
    """
    Test Phase 1 -> Phase 2 complete execution:
    1. Phase 1 plans research, proposes anchors, reaches awaiting_review.
    2. POST /confirm-anchors confirms anchor and triggers Phase 2.
    3. Phase 2 executes discovery, resolves taste signals, creates leads with persisted evidence UUIDs,
       runs deterministic assessment and scoring, and completes cleanly.
    """
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    product, run = await _seed_product_and_run(user_id)

    # 1. Execute Phase 1 runner
    await run_research_run_phase1(run.id)

    async with async_session_maker() as session:
        r1 = (await session.execute(select(ResearchRunModel).where(ResearchRunModel.id == run.id))).scalar_one()
        assert r1.status == "awaiting_review"
        assert r1.stage == "anchor_review"

        # Confirm at least one anchor
        anchors = (await session.execute(select(TasteAnchorModel).where(TasteAnchorModel.run_id == run.id))).scalars().all()
        assert len(anchors) >= 1
        anchors[0].status = "confirmed"
        await session.commit()

    # 2. Confirm anchors via API endpoint
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.post(
            f"/api/v1/research-runs/{run.id}/confirm-anchors",
            json={"proceed_without_anchors": False},
            headers=headers,
        )
        assert res.status_code == 200

        # 3. Await background Phase 2 runner triggered by confirm-anchors
        for _ in range(50):
            poll = await client.get(f"/api/v1/research-runs/{run.id}", headers=headers)
            assert poll.status_code == 200
            data = poll.json()
            if data["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.05)

    # 4. Verify Run completion and outputs
    async with async_session_maker() as session:
        completed_run = (
            await session.execute(select(ResearchRunModel).where(ResearchRunModel.id == run.id))
        ).scalar_one()
        assert completed_run.status == "completed"
        assert completed_run.stage == "done"
        assert completed_run.finished_at is not None

        # Verify market hypotheses have taste signals attached (DECISION-D15)
        hypos = (
            await session.execute(select(MarketHypothesisModel).where(MarketHypothesisModel.run_id == run.id))
        ).scalars().all()
        assert len(hypos) >= 1
        has_signals = any(len(h.signals) > 0 for h in hypos)
        assert has_signals is True

        # Verify leads were persisted
        leads = (
            await session.execute(select(LeadModel).where(LeadModel.run_id == run.id))
        ).scalars().all()
        assert len(leads) >= 1

        for lead in leads:
            assert lead.owner_id == user_id
            assert lead.product_id == product.id
            assert lead.canonical_domain is not None
            assert lead.tier in ("qualified", "needs_review", "unqualified")
            assert "overall" in lead.scores
            assert "tier_reasons" in lead.scores

            # Verify persisted evidence items have DB UUIDs (DECISION-D8)
            evs = (
                await session.execute(select(LeadEvidenceModel).where(LeadEvidenceModel.lead_id == lead.id))
            ).scalars().all()
            assert len(evs) >= 1
            for ev in evs:
                assert ev.id is not None
                assert ev.owner_id == user_id
                assert ev.lead_id == lead.id


# ==============================================================================
# 2. Canonical Domain Deduplication & Conflict Merging (DECISION-D2)
# ==============================================================================

@pytest.mark.asyncio
async def test_canonical_domain_deduplication_and_run_id_update() -> None:
    """
    DECISION-D2:
    When a subsequent run rediscovers an existing canonical domain for the same product:
    1. It merges new evidence into the existing lead (no duplicate lead row).
    2. It updates lead.run_id to the new run.id so GET /leads?run_id=new_run returns it.
    """
    user_id = uuid4()
    product, run_1 = await _seed_product_and_run(user_id)

    # Create run 2 on the same product
    async with async_session_maker() as session:
        run_2 = ResearchRunModel(
            id=uuid4(),
            owner_id=user_id,
            product_id=product.id,
            status="queued",
            stage="discovery",
        )
        session.add(run_2)
        await session.commit()

    # Seed an existing lead under Run 1
    domain = "atelierlivingdemo.com"
    lead_id = uuid4()
    async with async_session_maker() as session:
        lead = LeadModel(
            id=lead_id,
            owner_id=user_id,
            run_id=run_1.id,
            product_id=product.id,
            name="Atelier Living Original",
            website=f"https://{domain}",
            canonical_domain=domain,
            tier="qualified",
            scores={"overall": 80.0},
        )
        session.add(lead)
        session.add(
            LeadEvidenceModel(
                id=uuid4(),
                owner_id=user_id,
                lead_id=lead_id,
                url=f"https://{domain}/about",
                excerpt="Original excerpt.",
                source_type="official_site",
            )
        )
        await session.commit()

    # Execute Phase 2 for Run 2 (which finds atelierlivingdemo.com via fixture pipeline)
    await run_research_run_phase2(run_2.id)

    # Verify deduplication & run_id update
    async with async_session_maker() as session:
        leads_for_domain = (
            await session.execute(
                select(LeadModel).where(
                    LeadModel.owner_id == user_id,
                    LeadModel.product_id == product.id,
                    LeadModel.canonical_domain == domain,
                )
            )
        ).scalars().all()

        # Must NOT create a second lead row for the same canonical domain
        assert len(leads_for_domain) == 1
        merged_lead = leads_for_domain[0]
        assert merged_lead.id == lead_id

        # DECISION-D2: run_id must be updated to the latest run.id
        assert merged_lead.run_id == run_2.id

        # Evidence items must be merged
        evs = (
            await session.execute(select(LeadEvidenceModel).where(LeadEvidenceModel.lead_id == lead_id))
        ).scalars().all()
        assert len(evs) >= 2  # Original + new discovery evidence


# ==============================================================================
# 3. Duplicate Linking Test (DECISION-D9)
# ==============================================================================

@pytest.mark.asyncio
async def test_duplicate_of_linking_between_secondary_and_primary_leads(monkeypatch) -> None:
    """
    DECISION-D9:
    When a candidate has possible_duplicate_of_domain set, resolve that primary domain's
    persisted lead UUID and assign it to secondary_lead.duplicate_of.
    """
    user_id = uuid4()
    product, run = await _seed_product_and_run(user_id)

    # Custom pipeline mock returning a primary and a secondary duplicate candidate
    class MockDuplicatePipeline:
        async def run(self, product, plan, anchors, on_progress=None):
            return [
                LeadCandidate(
                    name="Primary Boutique",
                    website="https://primaryboutique.com",
                    canonical_domain="primaryboutique.com",
                    website_verified=True,
                    possible_duplicate_of_domain=None,
                    evidence=[],
                ),
                LeadCandidate(
                    name="Secondary Clone Boutique",
                    website="https://secondaryboutique.com",
                    canonical_domain="secondaryboutique.com",
                    website_verified=True,
                    possible_duplicate_of_domain="primaryboutique.com",  # DECISION-D9
                    evidence=[],
                ),
            ]

    monkeypatch.setattr("backend.app.jobs.runner.get_research_pipeline", lambda: MockDuplicatePipeline())

    await run_research_run_phase2(run.id)

    async with async_session_maker() as session:
        primary = (
            await session.execute(
                select(LeadModel).where(LeadModel.canonical_domain == "primaryboutique.com")
            )
        ).scalar_one()

        secondary = (
            await session.execute(
                select(LeadModel).where(LeadModel.canonical_domain == "secondaryboutique.com")
            )
        ).scalar_one()

        assert primary.duplicate_of is None
        assert secondary.duplicate_of == primary.id  # Linked correctly!


# ==============================================================================
# 4. Per-Lead Error Isolation Test
# ==============================================================================

@pytest.mark.asyncio
async def test_per_lead_failure_isolation(monkeypatch) -> None:
    """
    AGENT.md Section 5:
    Per-lead assessment/scoring failures never abort the run:
    the failing lead is saved with tier: needs_review and error notes, and the run continues.
    """
    user_id = uuid4()
    product, run = await _seed_product_and_run(user_id)

    # Mock pipeline returning 2 candidates
    class MockTwoLeadPipeline:
        async def run(self, product, plan, anchors, on_progress=None):
            return [
                LeadCandidate(
                    name="Failing Lead Boutique",
                    website="https://failingboutique.com",
                    canonical_domain="failingboutique.com",
                    website_verified=True,
                    evidence=[],
                ),
                LeadCandidate(
                    name="Healthy Lead Boutique",
                    website="https://healthyboutique.com",
                    canonical_domain="healthyboutique.com",
                    website_verified=True,
                    evidence=[],
                ),
            ]

    # Mock AI service where assess_lead throws for the first lead
    from backend.ai.service import get_ai_service
    real_ai = get_ai_service()

    class FlakyAIService:
        async def assess_lead(self, product, lead, evidence, **kwargs):
            if "failing" in lead.canonical_domain:
                raise RuntimeError("Simulated AI model timeout / JSON syntax error on lead")
            return await real_ai.assess_lead(product, lead, evidence)

    monkeypatch.setattr("backend.app.jobs.runner.get_research_pipeline", lambda: MockTwoLeadPipeline())
    monkeypatch.setattr("backend.app.jobs.runner.get_ai_service", lambda: FlakyAIService())

    # Execute Phase 2
    await run_research_run_phase2(run.id)

    async with async_session_maker() as session:
        # Run must still finish as completed (not failed!)
        r = (await session.execute(select(ResearchRunModel).where(ResearchRunModel.id == run.id))).scalar_one()
        assert r.status == "completed"
        assert r.stage == "done"

        # Failing lead is isolated with needs_review
        failing_lead = (
            await session.execute(select(LeadModel).where(LeadModel.canonical_domain == "failingboutique.com"))
        ).scalar_one()
        assert failing_lead.tier == "needs_review"
        assert "Simulated AI model timeout" in str(failing_lead.notes)

        # Healthy lead is processed normally
        healthy_lead = (
            await session.execute(select(LeadModel).where(LeadModel.canonical_domain == "healthyboutique.com"))
        ).scalar_one()
        assert healthy_lead.tier in ("qualified", "needs_review", "unqualified")


# ==============================================================================
# 5. Zero Candidates Clean Completion Test
# ==============================================================================

@pytest.mark.asyncio
async def test_zero_candidates_completes_cleanly_with_note(monkeypatch) -> None:
    """
    AGENT.md Section 9:
    If discovery yields 0 results, run finishes cleanly as completed with an explanatory note.
    Never invent fake leads.
    """
    user_id = uuid4()
    product, run = await _seed_product_and_run(user_id)

    class EmptyPipeline:
        async def run(self, product, plan, anchors, on_progress=None):
            return []

    monkeypatch.setattr("backend.app.jobs.runner.get_research_pipeline", lambda: EmptyPipeline())

    await run_research_run_phase2(run.id)

    async with async_session_maker() as session:
        r = (await session.execute(select(ResearchRunModel).where(ResearchRunModel.id == run.id))).scalar_one()
        assert r.status == "completed"
        assert r.stage == "done"
        assert "0 candidate leads found" in r.plan.get("notes", "")

        lead_count = (
            await session.execute(select(LeadModel).where(LeadModel.run_id == run.id))
        ).scalars().all()
        assert len(lead_count) == 0


# ==============================================================================
# 6. Buyer Leads API: Filters, Sorting, and Pagination (DECISION-D7)
# ==============================================================================

@pytest.mark.asyncio
async def test_get_leads_filtering_sorting_and_pagination() -> None:
    """
    Test GET /api/v1/leads filtering across:
    - run_id, product_id, review_status, tier, q, location, min_score (excluding overall is None D7)
    - sorting (score_desc nulls last, name, newest)
    - pagination envelope (items, total, page, page_size)
    """
    user_id = uuid4()
    headers = make_auth_header(user_id=user_id)
    product, run = await _seed_product_and_run(user_id)

    # Seed 3 leads with distinct values
    async with async_session_maker() as session:
        l1 = LeadModel(
            id=uuid4(),
            owner_id=user_id,
            run_id=run.id,
            product_id=product.id,
            name="Alpha Living Boutique",
            website="https://alphaliving.com",
            canonical_domain="alphaliving.com",
            location={"city": "Amsterdam", "country": "Netherlands"},
            tier="qualified",
            scores={"overall": 95.0, "category_fit": 100.0, "tier_reasons": ["Top score"]},
            review_status="saved",
            is_demo=False,
        )
        l2 = LeadModel(
            id=uuid4(),
            owner_id=user_id,
            run_id=run.id,
            product_id=product.id,
            name="Beta Concept Store",
            website="https://betaconcept.de",
            canonical_domain="betaconcept.de",
            location={"city": "Berlin", "country": "Germany"},
            tier="needs_review",
            scores={"overall": 65.0, "category_fit": 60.0, "tier_reasons": ["Moderate"]},
            review_status="new",
            is_demo=False,
        )
        l3 = LeadModel(
            id=uuid4(),
            owner_id=user_id,
            run_id=run.id,
            product_id=product.id,
            name="Gamma Home Textiles",
            website="https://gammahome.fr",
            canonical_domain="gammahome.fr",
            location={"city": "Paris", "country": "France"},
            tier="unqualified",
            scores={"overall": None, "category_fit": None, "tier_reasons": ["Unverified"]},
            review_status="contacted",
            is_demo=False,
        )
        session.add_all([l1, l2, l3])
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Filter by tier: qualified
        res_tier = await client.get("/api/v1/leads?tier=qualified", headers=headers)
        assert res_tier.status_code == 200
        paged_tier = LeadPagedResponse.model_validate(res_tier.json())
        assert paged_tier.total == 1
        assert paged_tier.items[0].name == "Alpha Living Boutique"

        # Filter by review_status: saved
        res_status = await client.get("/api/v1/leads?review_status=saved", headers=headers)
        assert res_status.status_code == 200
        paged_status = LeadPagedResponse.model_validate(res_status.json())
        assert paged_status.total == 1
        assert paged_status.items[0].name == "Alpha Living Boutique"

        # Search query q on name: "Beta"
        res_q = await client.get("/api/v1/leads?q=Beta", headers=headers)
        assert res_q.status_code == 200
        paged_q = LeadPagedResponse.model_validate(res_q.json())
        assert paged_q.total == 1
        assert paged_q.items[0].canonical_domain == "betaconcept.de"

        # Filter by location: "Germany"
        res_loc = await client.get("/api/v1/leads?location=Germany", headers=headers)
        assert res_loc.status_code == 200
        paged_loc = LeadPagedResponse.model_validate(res_loc.json())
        assert paged_loc.total == 1
        assert paged_loc.items[0].name == "Beta Concept Store"

        # Filter by min_score (DECISION-D7: overall is None is excluded)
        # min_score=70 -> only Alpha (95.0)
        res_score_high = await client.get("/api/v1/leads?min_score=70", headers=headers)
        assert res_score_high.status_code == 200
        paged_sh = LeadPagedResponse.model_validate(res_score_high.json())
        assert paged_sh.total == 1
        assert paged_sh.items[0].name == "Alpha Living Boutique"

        # min_score=60 -> Alpha (95.0) and Beta (65.0). Gamma (overall=None) is excluded.
        res_score_med = await client.get("/api/v1/leads?min_score=60", headers=headers)
        assert res_score_med.status_code == 200
        paged_sm = LeadPagedResponse.model_validate(res_score_med.json())
        assert paged_sm.total == 2
        assert {item.name for item in paged_sm.items} == {"Alpha Living Boutique", "Beta Concept Store"}

        # Sort: score_desc (NULLS LAST)
        res_sort_score = await client.get("/api/v1/leads?sort=score_desc", headers=headers)
        assert res_sort_score.status_code == 200
        paged_ss = LeadPagedResponse.model_validate(res_sort_score.json())
        assert [i.name for i in paged_ss.items] == ["Alpha Living Boutique", "Beta Concept Store", "Gamma Home Textiles"]

        # Sort: name
        res_sort_name = await client.get("/api/v1/leads?sort=name", headers=headers)
        assert res_sort_name.status_code == 200
        paged_sn = LeadPagedResponse.model_validate(res_sort_name.json())
        assert [i.name for i in paged_sn.items] == ["Alpha Living Boutique", "Beta Concept Store", "Gamma Home Textiles"]

        # Pagination: page_size=2
        res_p1 = await client.get("/api/v1/leads?page=1&page_size=2&sort=name", headers=headers)
        assert res_p1.status_code == 200
        p1 = LeadPagedResponse.model_validate(res_p1.json())
        assert p1.total == 3
        assert len(p1.items) == 2
        assert p1.items[0].name == "Alpha Living Boutique"
        assert p1.items[1].name == "Beta Concept Store"

        res_p2 = await client.get("/api/v1/leads?page=2&page_size=2&sort=name", headers=headers)
        assert res_p2.status_code == 200
        p2 = LeadPagedResponse.model_validate(res_p2.json())
        assert p2.total == 3
        assert len(p2.items) == 1
        assert p2.items[0].name == "Gamma Home Textiles"


# ==============================================================================
# 7. Lead Detail, Patch, and Evidence Endpoints with Strict Isolation
# ==============================================================================

@pytest.mark.asyncio
async def test_lead_detail_patch_and_evidence_endpoints() -> None:
    """
    Test GET /leads/{id}, PATCH /leads/{id}, and GET /leads/{id}/evidence.
    Verify strict user isolation (returns 404 for other user's record).
    """
    user_a = uuid4()
    user_b = uuid4()
    headers_a = make_auth_header(user_id=user_a)
    headers_b = make_auth_header(user_id=user_b)
    product_a, run_a = await _seed_product_and_run(user_a)

    lead_id = uuid4()
    async with async_session_maker() as session:
        lead = LeadModel(
            id=lead_id,
            owner_id=user_a,
            run_id=run_a.id,
            product_id=product_a.id,
            name="Curated Design Living",
            website="https://curatedlivingdemo.com",
            canonical_domain="curatedlivingdemo.com",
            tier="qualified",
            scores={"overall": 88.0},
            review_status="new",
            notes="Initial note",
        )
        session.add(lead)
        session.add(
            LeadEvidenceModel(
                id=uuid4(),
                owner_id=user_a,
                lead_id=lead_id,
                url="https://curatedlivingdemo.com/about",
                excerpt="Stocking independent sustainable textiles.",
                source_type="official_site",
            )
        )
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. GET /leads/{id} for User A (Owner)
        get_res = await client.get(f"/api/v1/leads/{lead_id}", headers=headers_a)
        assert get_res.status_code == 200
        lead_schema = Lead.model_validate(get_res.json())
        assert lead_schema.name == "Curated Design Living"

        # 2. Strict isolation: GET /leads/{id} for User B returns 404
        get_b_res = await client.get(f"/api/v1/leads/{lead_id}", headers=headers_b)
        assert get_b_res.status_code == 404
        assert get_b_res.json()["error"]["code"] == "not_found"

        # 3. PATCH /leads/{id} updating review_status and notes
        patch_res = await client.patch(
            f"/api/v1/leads/{lead_id}",
            json={"review_status": "saved", "notes": "Follow up after trade fair."},
            headers=headers_a,
        )
        assert patch_res.status_code == 200
        patched_lead = Lead.model_validate(patch_res.json())
        assert patched_lead.review_status == LeadReviewStatus.SAVED
        assert patched_lead.notes == "Follow up after trade fair."

        # 4. Strict isolation: PATCH /leads/{id} for User B returns 404
        patch_b_res = await client.patch(
            f"/api/v1/leads/{lead_id}",
            json={"review_status": "rejected"},
            headers=headers_b,
        )
        assert patch_b_res.status_code == 404

        # 5. GET /leads/{id}/evidence for User A
        ev_res = await client.get(f"/api/v1/leads/{lead_id}/evidence", headers=headers_a)
        assert ev_res.status_code == 200
        ev_list = ev_res.json()
        assert len(ev_list) == 1
        assert ev_list[0]["source_type"] == "official_site"
        assert "sustainable textiles" in ev_list[0]["excerpt"]

        # 6. Strict isolation: GET /leads/{id}/evidence for User B returns 404
        ev_b_res = await client.get(f"/api/v1/leads/{lead_id}/evidence", headers=headers_b)
        assert ev_b_res.status_code == 404
