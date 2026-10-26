"""
Unit tests for Contract v0.2 schemas, enums, null chains, and serialization.
Precedence: Rank 1 in AGENT.md Section 0.
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from contracts.schemas import (
    CulturalAffinity,
    DimensionAssessment,
    DimensionLabel,
    ErrorCode,
    ErrorDetail,
    ErrorEnvelope,
    EvidenceItem,
    EvidenceSourceType,
    Lead,
    LeadAssessment,
    LeadCandidate,
    LeadReviewStatus,
    LeadScores,
    LeadTier,
    OutreachDraft,
    OutreachDraftStatus,
    PriceSegment,
    Product,
    ProductAttributes,
    ProductInput,
    ProvenanceTag,
    ResearchPlan,
    ResearchRun,
    ResearchRunStage,
    ResearchRunStatus,
    TasteAnchor,
    TasteAnchorSource,
    TasteAnchorStatus,
)
from backend.ai.service import get_ai_service
from backend.research.pipeline import get_research_pipeline
from backend.integrations.qloo.provider import get_taste_provider


class TestNullChainAndDimensionLabels:
    """Tests guaranteeing that 'unknown' -> None (never 0) survives across all dimensions."""

    def test_dimension_label_to_score_mapping(self):
        # Truth rule #1: unknown must map strictly to None, never 0 or 20
        assert DimensionLabel.UNKNOWN.to_score() is None
        assert DimensionLabel.UNKNOWN.to_score() is not 0

        assert DimensionLabel.HIGH.to_score() == 100.0
        assert DimensionLabel.MEDIUM.to_score() == 60.0
        assert DimensionLabel.LOW.to_score() == 20.0

    def test_defensive_alias_parsing(self):
        # DECISION-D14: wire enum is high/medium/low/unknown, but aliases match/adjacent/mismatch accepted defensively
        assert DimensionLabel.from_str_defensive("high") == DimensionLabel.HIGH
        assert DimensionLabel.from_str_defensive("match") == DimensionLabel.HIGH
        assert DimensionLabel.from_str_defensive("medium") == DimensionLabel.MEDIUM
        assert DimensionLabel.from_str_defensive("adjacent") == DimensionLabel.MEDIUM
        assert DimensionLabel.from_str_defensive("low") == DimensionLabel.LOW
        assert DimensionLabel.from_str_defensive("mismatch") == DimensionLabel.LOW
        assert DimensionLabel.from_str_defensive("unknown") == DimensionLabel.UNKNOWN
        assert DimensionLabel.from_str_defensive(None) == DimensionLabel.UNKNOWN

    def test_lead_scores_null_preservation_in_json(self):
        # Guarantee that None does not turn into 0 during JSON serialization
        scores = LeadScores(
            category_fit=None,
            aesthetic_fit=DimensionLabel.HIGH.to_score(),
            evidence_quality=40.0,
            seller_compat=None,
            overall=None,
            completeness=0.5,
            tier_reasons=["Category fit is unknown; aesthetic fit is high."],
        )

        data = json.loads(scores.model_dump_json())
        assert data["category_fit"] is None
        assert data["seller_compat"] is None
        assert data["overall"] is None
        assert data["aesthetic_fit"] == 100.0
        assert data["evidence_quality"] == 40.0
        assert data["completeness"] == 0.5
        assert "tier_reasons" in data


class TestIsDemoLineageAndSerialization:
    """Tests guaranteeing that is_demo propagates properly on all core models."""

    def test_is_demo_on_lead_and_evidence(self):
        lead_id = uuid4()
        run_id = uuid4()
        product_id = uuid4()

        lead = Lead(
            id=lead_id,
            run_id=run_id,
            product_id=product_id,
            name="Demo Home Boutique",
            website="https://demohomeboutique.com",
            canonical_domain="demohomeboutique.com",
            tier=LeadTier.QUALIFIED,
            is_demo=True,
        )

        lead_json = json.loads(lead.model_dump_json())
        assert lead_json["is_demo"] is True
        assert lead_json["id"] == str(lead_id)

        evidence = EvidenceItem(
            lead_id=lead_id,
            url="https://demohomeboutique.com/about",
            excerpt="We curate independent artisan homewares.",
            is_demo=True,
        )

        evidence_json = json.loads(evidence.model_dump_json())
        assert evidence_json["is_demo"] is True

    def test_is_demo_on_draft_and_cultural_affinity(self):
        lead_id = uuid4()
        product_id = uuid4()

        draft = OutreachDraft(
            lead_id=lead_id,
            product_id=product_id,
            version=1,
            subject="Wholesale proposal",
            body="Hello team...",
            warnings=["Please verify phone number before sending."],
            is_demo=True,
        )

        draft_json = json.loads(draft.model_dump_json())
        assert draft_json["is_demo"] is True
        assert draft_json["warnings"] == ["Please verify phone number before sending."]

        affinity = CulturalAffinity(
            provider="mock",
            is_demo=True,
            signals=[{"type": "aesthetic_match", "text": "High botanical lifestyle overlap"}],
        )

        affinity_json = json.loads(affinity.model_dump_json())
        assert affinity_json["is_demo"] is True
        assert affinity_json["provider"] == "mock"


class TestProductValidation:
    """Tests for Product passport constraints (price_min <= price_max, moq >= 1)."""

    def test_valid_product(self):
        prod = Product(
            owner_id=uuid4(),
            name="Block Printed Cushion Cover",
            category="Home Textiles",
            description="Handcrafted block printed cushion cover set.",
            materials=["cotton"],
            price_segment=PriceSegment.MID_PREMIUM,
            price_min=25.0,
            price_max=50.0,
            moq=50,
        )
        assert prod.price_min == 25.0
        assert prod.price_max == 50.0
        assert prod.moq == 50

    def test_invalid_price_range_raises(self):
        with pytest.raises(ValueError, match="price_min must be <= price_max"):
            Product(
                owner_id=uuid4(),
                name="Invalid Product",
                category="Textiles",
                description="Invalid pricing",
                price_min=100.0,
                price_max=50.0,
            )

    def test_invalid_moq_raises(self):
        with pytest.raises(ValueError):
            Product(
                owner_id=uuid4(),
                name="Invalid Product",
                category="Textiles",
                description="Invalid MOQ",
                moq=0,  # ge=1 violated
            )


class TestErrorEnvelope:
    """Tests verifying ErrorEnvelope structure matches Appendix A.5."""

    def test_error_envelope_structure(self):
        env = ErrorEnvelope(
            error=ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR,
                message="Invalid request body",
                details={"field": "moq", "reason": "must be >= 1"},
            )
        )
        data = json.loads(env.model_dump_json())
        assert "error" in data
        assert data["error"]["code"] == "validation_error"
        assert data["error"]["message"] == "Invalid request body"
        assert data["error"]["details"]["field"] == "moq"
        assert "request_id" in data["error"]


@pytest.mark.asyncio
class TestWS3FactoryStubs:
    """Tests verifying WS3 factory stubs can be called asynchronously without API keys."""

    async def test_get_ai_service_stub(self, monkeypatch):
        monkeypatch.setenv("NEBIUS_API_KEY", "")
        service = get_ai_service()
        product = Product(
            owner_id=uuid4(),
            name="Block-printed Runner",
            category="Table Linen",
            description="Cotton table runner",
            motifs=["botanical"],
        )

        plan = await service.plan_research(product)
        assert isinstance(plan, ResearchPlan)
        assert len(plan.aesthetic_candidates) > 0

        attrs = await service.structure_product(
            "Natural hand block printed textiles", ProductInput(name="Table Runner")
        )
        assert isinstance(attrs, ProductAttributes)
        assert attrs.category == "Home Textiles"

    async def test_get_research_pipeline_stub(self, monkeypatch):
        monkeypatch.setenv("TAVILY_API_KEY", "")
        monkeypatch.setenv("NEBIUS_API_KEY", "")
        pipeline = get_research_pipeline()
        product = Product(
            owner_id=uuid4(),
            name="Block-printed Runner",
            category="Table Linen",
            description="Cotton table runner",
        )
        plan = ResearchPlan()
        anchors = [
            TasteAnchor(
                run_id=uuid4(),
                label="Artisan Textiles",
                source=TasteAnchorSource.AI_PROPOSED,
                status=TasteAnchorStatus.CONFIRMED,
            )
        ]

        candidates = await pipeline.run(product, plan, anchors)
        assert len(candidates) >= 1
        assert all(isinstance(c, LeadCandidate) for c in candidates)
        assert candidates[0].evidence[0].is_demo is True

    async def test_get_taste_provider_stub(self, monkeypatch):
        monkeypatch.setenv("QLOO_API_KEY", "")
        provider = get_taste_provider()
        assert provider.name == "mock"
        assert provider.is_demo is True

        entities = await provider.search_entities("Textiles")
        assert len(entities) >= 1
        assert entities[0].id.startswith("demo-entity-")
