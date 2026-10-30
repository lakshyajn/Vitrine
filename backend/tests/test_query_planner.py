"""
backend/tests/test_query_planner.py
Unit tests for category-aware query generation, validation, and template rendering (Milestone B).
Tests across four distinct product types:
1. Pencil (Stationery / commodity)
2. Ceramic Mugs (Ceramics / tabletop)
3. Leather Notebooks (Stationery / leather goods)
4. Block-Printed Cushion Covers (Home textiles / artisan decor)
"""

from __future__ import annotations

from uuid import uuid4
import pytest

from backend.ai.prompts import build_task_b_prompt
from backend.ai.service import FixtureAIService
from backend.ai.validation import validate_research_plan_claims
from backend.app.core.errors import AppError
from backend.research.queries import (
    build_research_queries,
    validate_search_query,
)
from contracts.schemas import (
    PriceSegment,
    Product,
    ResearchPlan,
)


@pytest.fixture
def product_pencil() -> Product:
    return Product(
        owner_id=uuid4(),
        name="Cedar Wood Graphite Pencil",
        category="stationery",
        description="Architectural drawing pencils crafted with California cedar and graphite core.",
        materials=["cedar wood", "graphite"],
        style=["minimalist"],
        motifs=[],
        colours=["natural wood", "black"],
        price_segment=PriceSegment.MID_PREMIUM,
        target_retailer_types=["stationery shop", "art supply boutique"],
    )


@pytest.fixture
def product_ceramic_mugs() -> Product:
    return Product(
        owner_id=uuid4(),
        name="Wheel-Thrown Stoneware Mug",
        category="ceramics",
        description="Handcrafted ceramic coffee mugs with matte speckled glaze.",
        materials=["stoneware clay", "ceramic glaze"],
        style=["wabi-sabi", "artisanal"],
        motifs=[],
        colours=["sand", "oatmeal"],
        price_segment=PriceSegment.MID_PREMIUM,
        target_retailer_types=["pottery studio", "kitchen lifestyle boutique"],
    )


@pytest.fixture
def product_leather_notebooks() -> Product:
    return Product(
        owner_id=uuid4(),
        name="Full-Grain Leather Journal",
        category="stationery",
        description="Refillable full-grain leather bound notebooks with archival paper.",
        materials=["vegetable-tanned leather", "cotton paper"],
        style=["heritage", "rustic"],
        motifs=["embossed"],
        colours=["tan", "espresso"],
        price_segment=PriceSegment.PREMIUM,
        target_retailer_types=["leather goods boutique", "luxury bookshop"],
    )


@pytest.fixture
def product_cushion_covers() -> Product:
    return Product(
        owner_id=uuid4(),
        name="Hand Block-Printed Cushion Cover",
        category="home textiles",
        description="Artisanal hand block-printed cushion covers in geometric Mughal patterns.",
        materials=["organic cotton", "natural linen"],
        style=["artisanal", "heritage"],
        motifs=["geometric", "botanical"],
        colours=["indigo", "terracotta"],
        price_segment=PriceSegment.MID_PREMIUM,
        target_retailer_types=["home decor boutique", "concept store"],
    )


# -----------------------------------------------------------------------------
# 1. Validator Tests Across Four Products
# -----------------------------------------------------------------------------

def test_query_validator_accepts_grounded_queries(
    product_pencil: Product,
    product_ceramic_mugs: Product,
    product_leather_notebooks: Product,
    product_cushion_covers: Product,
):
    plan = ResearchPlan(target_regions=["UK", "London", "Germany", "Berlin"])

    # Pencil: valid retail queries
    assert validate_search_query("stationery shop UK", product_pencil, plan)[0]
    assert validate_search_query("independent pencil retailer London", product_pencil, plan)[0]
    assert validate_search_query("buy cedar wood graphite pencil online store", product_pencil, plan)[0]

    # Ceramic Mugs: valid retail queries
    assert validate_search_query("ceramics boutique Germany", product_ceramic_mugs, plan)[0]
    assert validate_search_query("stoneware mug stockist Berlin", product_ceramic_mugs, plan)[0]
    assert validate_search_query("independent pottery studio selling ceramics", product_ceramic_mugs, plan)[0]

    # Leather Notebooks: valid retail queries
    assert validate_search_query("luxury stationery boutique London", product_leather_notebooks, plan)[0]
    assert validate_search_query("leather journal stockist UK", product_leather_notebooks, plan)[0]

    # Cushion Covers: valid retail queries
    assert validate_search_query("home textiles boutique UK", product_cushion_covers, plan)[0]
    assert validate_search_query("block printed cushion cover stockist", product_cushion_covers, plan)[0]


def test_query_validator_rejects_foreign_and_ungrounded_terms(
    product_pencil: Product,
    product_ceramic_mugs: Product,
):
    plan = ResearchPlan(target_regions=["UK"])

    # Pencil product rejected for textile/botanical terms
    ok, reason = validate_search_query("botanical cotton cushion shop UK", product_pencil, plan)
    assert not ok
    assert "lacks product-category" in reason or "foreign token" in reason

    ok, reason = validate_search_query("stationery shop cotton bedsheets", product_pencil, plan)
    assert not ok
    assert "foreign token 'bedsheets'" in reason or "foreign token 'cotton'" in reason

    # Ceramic mugs product rejected for random automotive or apparel terms
    ok, reason = validate_search_query("automotive spare parts store", product_ceramic_mugs, plan)
    assert not ok

    ok, reason = validate_search_query("ceramics shop silk dresses", product_ceramic_mugs, plan)
    assert not ok
    assert "foreign token 'silk'" in reason or "foreign token 'dresses'" in reason


# -----------------------------------------------------------------------------
# 2. Template Generation & Query Building
# -----------------------------------------------------------------------------

def test_build_research_queries_across_all_four_products(
    product_pencil: Product,
    product_ceramic_mugs: Product,
    product_leather_notebooks: Product,
    product_cushion_covers: Product,
):
    plan = ResearchPlan(
        target_regions=["UK", "Scandinavia"],
        search_queries=["curated artisan goods retailer"],  # lacks category -> should be dropped
    )

    # 1. Pencil queries
    pencil_queries = build_research_queries(product_pencil, plan, anchors=[], max_queries=8)
    assert len(pencil_queries) <= 8
    assert any("stationery" in q.lower() or "pencil" in q.lower() for q in pencil_queries)
    for q in pencil_queries:
        assert "cotton" not in q.lower()
        assert "textile" not in q.lower()

    # 2. Ceramics queries
    ceramic_queries = build_research_queries(product_ceramic_mugs, plan, anchors=[], max_queries=8)
    assert len(ceramic_queries) <= 8
    assert any("ceramics" in q.lower() or "mug" in q.lower() for q in ceramic_queries)
    for q in ceramic_queries:
        assert "textile" not in q.lower()

    # 3. Notebooks queries
    notebook_queries = build_research_queries(product_leather_notebooks, plan, anchors=[], max_queries=8)
    assert len(notebook_queries) <= 8
    assert any("stationery" in q.lower() or "journal" in q.lower() or "notebook" in q.lower() for q in notebook_queries)

    # 4. Cushion covers queries
    textile_queries = build_research_queries(product_cushion_covers, plan, anchors=[], max_queries=8)
    assert len(textile_queries) <= 8
    assert any("home textiles" in q.lower() or "cushion" in q.lower() for q in textile_queries)


def test_build_research_queries_records_dropped_count(product_pencil: Product):
    plan = ResearchPlan(
        target_regions=["UK"],
        search_queries=[
            "stationery shop UK",  # valid
            "irrelevant keyword query",  # invalid
            "cotton linen bedsheet store",  # invalid for pencil
        ],
    )
    queries = build_research_queries(product_pencil, plan, anchors=[], max_queries=8)
    assert "stationery shop UK" in queries
    assert "irrelevant keyword query" not in queries
    assert "cotton linen bedsheet store" not in queries
    assert plan.notes and "dropped" in plan.notes


# -----------------------------------------------------------------------------
# 3. Task B Prompt & Taste Relevance Contract
# -----------------------------------------------------------------------------

def test_task_b_prompt_instructs_category_gating_and_taste_relevance(product_pencil: Product):
    messages = build_task_b_prompt(product_pencil)
    system_content = messages[0]["content"]
    user_content = messages[1]["content"]

    assert "specific product category" in system_content
    assert "taste_relevance" in system_content
    assert "'applicable', 'limited', or 'not_applicable'" in system_content
    assert "empty list `[]` when taste does not meaningfully apply" in system_content
    assert "taste_relevance" in user_content


def test_validate_research_plan_claims_enforces_taste_relevance():
    valid_plan = ResearchPlan(
        taste_relevance="applicable",
        taste_relevance_reason="Design focused home textiles",
    )
    validate_research_plan_claims(valid_plan)  # should not raise

    commodity_plan = ResearchPlan(
        taste_relevance="not_applicable",
        taste_relevance_reason="Functional utility good",
        aesthetic_candidates=[],
    )
    validate_research_plan_claims(commodity_plan)  # should not raise

    invalid_plan = ResearchPlan(
        taste_relevance="super_high",  # invalid enum
    )
    with pytest.raises(AppError) as exc_info:
        validate_research_plan_claims(invalid_plan)
    assert "Invalid taste_relevance" in str(exc_info.value.message)


# -----------------------------------------------------------------------------
# 4. FixtureAIService Derives From Product Record
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fixture_ai_service_across_products(
    product_pencil: Product,
    product_ceramic_mugs: Product,
):
    ai = FixtureAIService()

    # Commodity item (pencil): taste_relevance should be not_applicable, aesthetic_candidates empty
    pencil_plan = await ai.plan_research(product_pencil)
    assert pencil_plan.taste_relevance == "not_applicable"
    assert pencil_plan.aesthetic_candidates == []
    assert any("stationery" in q for q in pencil_plan.search_queries)

    # Design item (mugs): taste_relevance applicable
    mug_plan = await ai.plan_research(product_ceramic_mugs)
    assert mug_plan.taste_relevance == "applicable"
    assert any("ceramics" in q.lower() for q in mug_plan.search_queries)
    for c in mug_plan.aesthetic_candidates:
        assert "textile" not in c.lower()
