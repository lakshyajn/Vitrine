"""
AI Service Interface and Fixture-backed Implementation (WS3 stub for WS2).
Matching WS2_Spec.md Appendix A.6.
"""

from __future__ import annotations

from typing import Protocol
from uuid import uuid4

from contracts.schemas import (
    DimensionAssessment,
    DimensionLabel,
    FactUsed,
    Lead,
    LeadAssessment,
    LeadCandidate,
    EvidenceItem,
    OutreachDraft,
    OutreachDraftStatus,
    PriceSegment,
    Product,
    ProductAttributes,
    ProductInput,
    ResearchPlan,
)


class AIService(Protocol):
    async def structure_product(self, description: str, known: ProductInput) -> ProductAttributes:
        ...

    async def plan_research(self, product: Product) -> ResearchPlan:
        ...

    async def assess_lead(
        self, product: Product, lead: LeadCandidate, evidence: list[EvidenceItem]
    ) -> LeadAssessment:
        ...

    async def draft_outreach(
        self,
        product: Product,
        lead: Lead,
        evidence: list[EvidenceItem],
        previous: OutreachDraft | None = None,
    ) -> OutreachDraft:
        ...


class FixtureAIService:
    """Minimal fixture-backed AIService returning valid Contract v0.2 data with 0 API keys."""

    async def structure_product(self, description: str, known: ProductInput) -> ProductAttributes:
        return ProductAttributes(
            style=known.style or ["handcrafted", "botanical", "artisanal"],
            materials=known.materials or ["cotton", "natural linen"],
            motifs=known.motifs or ["floral", "botanical"],
            colours=known.colours or ["terracotta", "indigo", "ochre"],
            price_segment=known.price_segment or PriceSegment.MID_PREMIUM,
            target_retailer_types=known.target_retailer_types or ["boutique", "concept store", "home decor"],
            uncertain_fields=[],
            assumptions=["Inferred botanical style from text description"],
            category=known.category or "Home Textiles",
            price_min=known.price_min or 30.0,
            price_max=known.price_max or 120.0,
            currency=known.currency or "USD",
            moq=known.moq or 50,
            monthly_capacity=known.monthly_capacity or 1500,
        )

    async def plan_research(self, product: Product) -> ResearchPlan:
        return ResearchPlan(
            target_regions=["Western Europe", "North America"],
            target_retailer_types=product.target_retailer_types or ["independent home boutique", "concept store"],
            aesthetic_candidates=["Block Print Aesthetic", "Artisanal Home Textiles", "Botanical Living"],
            search_queries=[
                f"independent home decor boutique {product.name}",
                "artisan textile boutique stockists",
            ],
            hypotheses_rationale="Small independent design shops value provenance and artisan stories.",
            notes="Fixture-backed initial research plan",
        )

    async def assess_lead(
        self, product: Product, lead: LeadCandidate, evidence: list[EvidenceItem]
    ) -> LeadAssessment:
        evidence_ids = [item.id for item in evidence] if evidence else [uuid4()]
        return LeadAssessment(
            category_fit=DimensionAssessment(
                label=DimensionLabel.HIGH,
                reasons=["Carries curated table linens and home textiles."],
                evidence_ids=evidence_ids[:1],
            ),
            aesthetic_fit=DimensionAssessment(
                label=DimensionLabel.HIGH,
                reasons=["Visual identity emphasizes warm earth tones and botanical motifs."],
                evidence_ids=evidence_ids[:1],
            ),
            seller_compat=DimensionAssessment(
                label=DimensionLabel.MEDIUM,
                reasons=["Stockist price point matches mid-premium range."],
                evidence_ids=evidence_ids[:1],
            ),
            summary=f"Strong potential boutique partner for {product.name}.",
            unknowns=["Specific MOQ requirements not stated on public website"],
            model_id="fixture-nemotron-stub",
        )

    async def draft_outreach(
        self,
        product: Product,
        lead: Lead,
        evidence: list[EvidenceItem],
        previous: OutreachDraft | None = None,
    ) -> OutreachDraft:
        first_evidence = evidence[0] if evidence else None
        facts = [
            FactUsed(
                fact_id="fact-1",
                text=f"Workshop specializes in {product.name} with {', '.join(product.motifs)} motifs",
                source_url=None,
            )
        ]
        if first_evidence:
            facts.append(
                FactUsed(
                    fact_id=f"evidence-{first_evidence.id}",
                    text=first_evidence.excerpt[:120],
                    source_url=first_evidence.url,
                )
            )

        subject = f"Wholesale inquiry: Handcrafted textiles for {lead.name}"
        body = (
            f"Dear {lead.name} team,\n\n"
            f"We noticed your beautifully curated collection. We are an artisan workshop creating "
            f"{product.name.lower()} in botanical motifs and natural dyes, positioned at {product.price_segment}.\n\n"
            f"We would love to share our wholesale line sheet with you.\n\nWarm regards,\nSample Seller"
        )

        return OutreachDraft(
            lead_id=lead.id,
            product_id=product.id,
            version=(previous.version + 1) if previous else 1,
            subject=subject,
            body=body,
            facts_used=facts,
            warnings=[],
            status=OutreachDraftStatus.DRAFT,
            parent_draft_id=previous.id if previous else None,
            is_demo=True,
        )


def get_ai_service() -> AIService:
    """Factory returning AIService instance (fixture-backed when no API key configured)."""
    return FixtureAIService()
