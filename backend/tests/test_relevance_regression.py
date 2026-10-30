"""
backend/tests/test_relevance_regression.py
Milestone A Regression Test Suite:
Validates category-aware query planning, junk-page gating, and fixture purity.
These tests describe the desired behavior across pencil and textile fixture sets.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.ai.service import FixtureAIService
from backend.app.scoring.engine import compute_scores_and_tier
from backend.research.pipeline import LiveResearchPipeline
from backend.research.queries import build_research_queries
from contracts.schemas import (
    DimensionAssessment,
    DimensionLabel,
    EvidenceItem,
    EvidenceSourceType,
    LeadAssessment,
    LeadCandidate,
    LeadTier,
    PriceSegment,
    Product,
    ProvenanceTag,
    ResearchPlan,
)

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture
def pencil_product() -> Product:
    return Product(
        owner_id=uuid4(),
        name="Cedar Wood Drawing Pencil",
        category="stationery",
        description="Premium cedar-wood graphite drawing pencils for artists and architects.",
        materials=["cedar wood", "graphite"],
        style=["minimalist"],
        motifs=[],
        colours=["natural wood", "graphite black"],
        price_segment=PriceSegment.MID_PREMIUM,
        price_min=12.0,
        price_max=35.0,
        currency="USD",
        moq=10,
        monthly_capacity=5000,
        target_retailer_types=["stationery boutique", "art supply shop"],
    )


@pytest.fixture
def textile_product() -> Product:
    return Product(
        owner_id=uuid4(),
        name="Hand Block-Printed Cushion Cover",
        category="home textiles",
        description="Artisanal hand block-printed cotton cushion covers with geometric motifs.",
        materials=["cotton", "linen"],
        style=["artisanal", "heritage"],
        motifs=["geometric", "botanical"],
        colours=["terracotta", "indigo"],
        price_segment=PriceSegment.MID_PREMIUM,
        price_min=25.0,
        price_max=60.0,
        currency="USD",
        moq=25,
        monthly_capacity=1000,
        target_retailer_types=["independent boutique", "concept store"],
    )


# -----------------------------------------------------------------------------
# 1. Query Planning Tests (Desired Behavior)
# -----------------------------------------------------------------------------

def test_pencil_queries_contain_no_textile_or_decor_defaults(pencil_product: Product):
    """
    Desired behavior: Query builder for pencil must NOT inject hardcoded textile terms
    (cotton, botanical, earthy, artisanal, textile, decor) unless present on the product.
    """
    plan = ResearchPlan(
        target_regions=["United Kingdom", "North America"],
        target_retailer_types=["stationery shop", "independent bookshop"],
        search_queries=[
            "independent stationery store United Kingdom",
            "curated design stationery stockists North America",
        ],
    )
    queries = build_research_queries(pencil_product, plan, anchors=[], max_queries=8)

    forbidden_terms = {"cotton", "botanical", "earthy", "artisanal", "textile", "decor"}
    for q in queries:
        q_lower = q.lower()
        for term in forbidden_terms:
            assert term not in q_lower, (
                f"Pencil query '{q}' illegally contains hardcoded textile term '{term}'"
            )


# -----------------------------------------------------------------------------
# 2. Pencil Fixture Pipeline Tests (Desired Behavior)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pencil_fixture_filters_junk_and_preserves_retailers(pencil_product: Product):
    """
    Desired behavior on fixtures/search_hits_pencil.json:
    - 4 junk pages (reddit, nationalmuseum.gov.in, tripadvisor, fandom wiki)
      MUST NOT become candidates (or if any candidate is created, it must be gated to UNQUALIFIED).
    - 3 genuine retailers (grafandquill-shop-demo.com, thepapeteriestudio-demo.co.uk, nordicdeskgoods-fixture.store)
      MUST survive as candidate leads.
    """
    hits_path = FIXTURES_DIR / "search_hits_pencil.json"
    with open(hits_path, "r", encoding="utf-8") as f:
        recorded_hits = json.load(f)

    mock_client = MagicMock()
    mock_client.search = AsyncMock(return_value=recorded_hits)

    pipeline = LiveResearchPipeline(client=mock_client, lead_cap=10)
    plan = ResearchPlan(target_regions=["UK", "US"])

    candidates = await pipeline.run(product=pencil_product, plan=plan, anchors=[])

    surviving_domains = {c.canonical_domain for c in candidates}

    # Junk domains that must NEVER survive as valid leads
    forbidden_junk_domains = {
        "reddit.com",
        "nationalmuseum.gov.in",
        "tripadvisor.com",
        "pencil-chronicles.fandom.com",
        "fandom.com",
    }
    for junk in forbidden_junk_domains:
        assert junk not in surviving_domains, f"Junk domain '{junk}' was not filtered from pencil candidates"

    # The 3 genuine retailers must survive
    expected_retailers = {
        "grafandquill-shop-demo.com",
        "thepapeteriestudio-demo.co.uk",
        "nordicdeskgoods-fixture.store",
    }
    for retailer in expected_retailers:
        assert retailer in surviving_domains, f"Genuine retailer '{retailer}' failed to survive relevance gate"


# -----------------------------------------------------------------------------
# 3. Textile Fixture Pipeline Tests (Desired Behavior)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_textile_fixture_filters_junk_and_preserves_boutiques(textile_product: Product):
    """
    Desired behavior on fixtures/search_hits_textile.json:
    - 2 junk pages (wikipedia, pinterest) must be filtered.
    - 2 genuine boutiques (atelierloomandthread-demo.com, marigoldlivingdecor-demo.co.uk) must survive.
    """
    hits_path = FIXTURES_DIR / "search_hits_textile.json"
    with open(hits_path, "r", encoding="utf-8") as f:
        recorded_hits = json.load(f)

    mock_client = MagicMock()
    mock_client.search = AsyncMock(return_value=recorded_hits)

    pipeline = LiveResearchPipeline(client=mock_client, lead_cap=10)
    plan = ResearchPlan(target_regions=["Western Europe"])

    candidates = await pipeline.run(product=textile_product, plan=plan, anchors=[])
    surviving_domains = {c.canonical_domain for c in candidates}

    forbidden_junk = {"en.wikipedia.org", "wikipedia.org", "pinterest.com"}
    for junk in forbidden_junk:
        assert junk not in surviving_domains, f"Junk domain '{junk}' leaked into textile candidates"

    expected_boutiques = {
        "atelierloomandthread-demo.com",
        "marigoldlivingdecor-demo.co.uk",
    }
    for b in expected_boutiques:
        assert b in surviving_domains, f"Textile boutique '{b}' failed to survive relevance gate"


# -----------------------------------------------------------------------------
# 4. FixtureAIService Category Purity Tests (Desired Behavior)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fixture_ai_service_derives_from_product_record(pencil_product: Product):
    """
    Desired behavior: FixtureAIService outputs must derive from the product record
    rather than hardcoding botanical/cotton/Home Textiles for every product.
    """
    ai_service = FixtureAIService()
    plan = await ai_service.plan_research(pencil_product)

    for q in plan.search_queries:
        assert "textile" not in q.lower(), f"Fixture plan query '{q}' contains 'textile' for pencil product"
        assert "cotton" not in q.lower(), f"Fixture plan query '{q}' contains 'cotton' for pencil product"

    for candidate in plan.aesthetic_candidates:
        assert "textile" not in candidate.lower(), f"Fixture candidate '{candidate}' contains 'textile' for pencil"

    assessment = await ai_service.assess_lead(
        product=pencil_product,
        lead=LeadCandidate(
            name="Graf & Quill",
            website="https://www.grafandquill-shop-demo.com",
            canonical_domain="grafandquill-shop-demo.com",
            evidence=[],
        ),
        evidence=[
            EvidenceItem(
                id=uuid4(),
                lead_id=uuid4(),
                url="https://www.grafandquill-shop-demo.com/products/pencil",
                excerpt="Curated drawing pencils and stationery.",
                source_type=EvidenceSourceType.PRODUCT_PAGE,
                domain_matches_lead=True,
                provenance=ProvenanceTag.VERIFIED_FACT,
                is_demo=True,
            )
        ],
    )
    for reason in assessment.category_fit.reasons:
        assert "textile" not in reason.lower(), f"Assessment reason '{reason}' mentions textile for pencil"
        assert "linens" not in reason.lower(), f"Assessment reason '{reason}' mentions linens for pencil"
