"""
Research Pipeline Interface and Fixture-backed Implementation (WS3 stub for WS2).
Matching WS2_Spec.md Appendix A.6.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol
from uuid import uuid4

from contracts.schemas import (
    EvidenceItem,
    EvidenceSourceType,
    LeadCandidate,
    LeadLocation,
    Product,
    ProvenanceTag,
    ResearchPlan,
    TasteAnchor,
)


class ResearchPipeline(Protocol):
    async def run(
        self,
        product: Product,
        plan: ResearchPlan,
        anchors: list[TasteAnchor],
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> list[LeadCandidate]:
        ...


class FixtureResearchPipeline:
    """Minimal fixture-backed ResearchPipeline returning realistic candidates with 0 API keys."""

    async def run(
        self,
        product: Product,
        plan: ResearchPlan,
        anchors: list[TasteAnchor],
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> list[LeadCandidate]:
        if on_progress:
            on_progress("discovery", {"discovered_count": 2, "message": "Discovered candidate retailers"})

        lead1_id = uuid4()
        lead2_id = uuid4()

        candidate1 = LeadCandidate(
            name="Atelier Living & Design",
            website="https://www.atelierlivingdemo.com",
            canonical_domain="atelierlivingdemo.com",
            location=LeadLocation(city="Amsterdam", region="North Holland", country="Netherlands"),
            retailer_type="Independent Home Decor Boutique",
            website_verified=True,
            possible_duplicate_of_domain=None,
            evidence=[
                EvidenceItem(
                    id=uuid4(),
                    lead_id=lead1_id,
                    url="https://www.atelierlivingdemo.com/about",
                    excerpt="We stock independent artisanal textiles, block-printed table linens, and ceramics from ethical makers.",
                    source_type=EvidenceSourceType.OFFICIAL_SITE,
                    domain_matches_lead=True,
                    provenance=ProvenanceTag.VERIFIED_FACT,
                    is_demo=True,
                ),
                EvidenceItem(
                    id=uuid4(),
                    lead_id=lead1_id,
                    url="https://www.atelierlivingdemo.com/collections/table-linens",
                    excerpt="Handmade cotton table runners and cushion covers in botanical motifs.",
                    source_type=EvidenceSourceType.PRODUCT_PAGE,
                    domain_matches_lead=True,
                    provenance=ProvenanceTag.VERIFIED_FACT,
                    is_demo=True,
                ),
            ],
        )

        candidate2 = LeadCandidate(
            name="The Botanist Shop",
            website="https://www.thebotanistshopdemo.co.uk",
            canonical_domain="thebotanistshopdemo.co.uk",
            location=LeadLocation(city="Bath", region="Somerset", country="United Kingdom"),
            retailer_type="Lifestyle & Botanical Boutique",
            website_verified=True,
            possible_duplicate_of_domain=None,
            evidence=[
                EvidenceItem(
                    id=uuid4(),
                    lead_id=lead2_id,
                    url="https://www.thebotanistshopdemo.co.uk",
                    excerpt="Curated botanical living goods, natural dyes, and handcrafted throws.",
                    source_type=EvidenceSourceType.OFFICIAL_SITE,
                    domain_matches_lead=True,
                    provenance=ProvenanceTag.VERIFIED_FACT,
                    is_demo=True,
                )
            ],
        )

        return [candidate1, candidate2]


def get_research_pipeline() -> ResearchPipeline:
    """Factory returning ResearchPipeline instance (fixture-backed when Tavily key is absent)."""
    return FixtureResearchPipeline()
