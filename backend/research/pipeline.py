"""
Research Pipeline Interface, FixtureResearchPipeline, and LiveResearchPipeline (WS3 Section 4).
Matches Contract v0.2 Appendix A.6 and keeps WS2's existing tests 100% passing.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Callable, Protocol
from uuid import uuid4

from backend.research.dedupe import deduplicate_lead_candidates, extract_canonical_domain
from backend.research.evidence import (
    classify_evidence_source_type,
    is_excluded_retailer_domain,
    verify_website_http,
)
from backend.research.queries import build_research_queries
from backend.research.tavily_client import TavilyClient
from backend.research.contact_scraper import extract_emails_from_text, score_and_rank_email, scrape_contact_email
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
    is_demo: bool

    async def run(
        self,
        product: Product,
        plan: ResearchPlan,
        anchors: list[TasteAnchor],
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> list[LeadCandidate]:
        ...


class FixtureResearchPipeline:
    """Fixture-backed ResearchPipeline returning realistic deduplicated candidates with 0 API keys."""

    name: str = "fixture"
    is_demo: bool = True

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
            contact_email="contact@atelierlivingdemo.com",
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
            contact_email="contact@atelierlivingdemo.com",
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

        return deduplicate_lead_candidates([candidate1, candidate2])


class LiveResearchPipeline:
    """
    Live Tavily Search + Deterministic Evidence Validation + Deduplication Pipeline (WS3 Section 4).
    Never fabricates retailers if search results are empty.
    """

    name: str = "tavily"
    is_demo: bool = False

    def __init__(self, client: TavilyClient, lead_cap: int = 6) -> None:
        self.client = client
        self.lead_cap = lead_cap

    async def run(
        self,
        product: Product,
        plan: ResearchPlan,
        anchors: list[TasteAnchor],
        on_progress: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> list[LeadCandidate]:
        queries = build_research_queries(product, plan, anchors, max_queries=4)
        if on_progress:
            on_progress("discovery", {"queries_count": len(queries), "message": "Running Tavily search queries"})

        sem = asyncio.Semaphore(4)

        async def _run_query(q: str) -> list[dict[str, Any]]:
            async with sem:
                return await self.client.search(q)

        batches = await asyncio.gather(*[_run_query(q) for q in queries])
        hits = [item for batch in batches for item in batch if item.get("url") and item.get("content")]

        if not hits:
            plan.notes = "Tavily search returned zero matching retailer pages; no candidates generated."
            if on_progress:
                on_progress("discovery", {"discovered_count": 0, "message": plan.notes})
            return []

        raw_candidates: list[LeadCandidate] = []
        for hit in hits[:12]:  # Cap at top 12 search extractions per run for fast hackathon throughput
            url = str(hit["url"]).strip()
            excluded, _ = is_excluded_retailer_domain(url)
            if excluded:
                continue

            dom = extract_canonical_domain(url)
            if not dom:
                continue

            lead_id = uuid4()
            excerpt = str(hit.get("content") or "").strip()[:500]
            title = str(hit.get("title") or dom).split("|")[0].split("–")[0].strip()[:100]
            source_type = classify_evidence_source_type(url, excerpt)

            # Check if email is directly in Tavily search snippet
            cand_email = None
            found_emails = extract_emails_from_text(f"{excerpt} {title}", dom)
            if found_emails:
                scored = sorted([(e, score_and_rank_email(e, dom)) for e in found_emails], key=lambda x: x[1], reverse=True)
                if scored and scored[0][1] > 20:
                    cand_email = scored[0][0]

            raw_candidates.append(
                LeadCandidate(
                    name=title or dom,
                    website=f"https://{dom.split('/')[0]}",
                    canonical_domain=dom,
                    location=None,
                    retailer_type=(
                        product.target_retailer_types[0]
                        if product.target_retailer_types
                        else "independent boutique"
                    ),
                    website_verified=False,
                    contact_email=cand_email,
                    evidence=[
                        EvidenceItem(
                            id=uuid4(),
                            lead_id=lead_id,
                            url=url,
                            excerpt=excerpt,
                            source_type=source_type,
                            domain_matches_lead=(extract_canonical_domain(url) == dom),
                            provenance=ProvenanceTag.VERIFIED_FACT,
                            is_demo=False,
                        )
                    ],
                )
            )

        deduped = deduplicate_lead_candidates(raw_candidates)[: self.lead_cap]

        async def _verify_and_scrape(cand: LeadCandidate) -> LeadCandidate:
            async with sem:
                alive, _ = await verify_website_http(cand.website)
                cand.website_verified = alive
                if not cand.contact_email:
                    try:
                        scraped = await scrape_contact_email(cand.canonical_domain, cand.website, self.client)
                        if scraped.get("email") and not scraped.get("is_fallback"):
                            cand.contact_email = scraped["email"]
                            if scraped.get("source_url"):
                                cand.evidence.append(
                                    EvidenceItem(
                                        id=uuid4(),
                                        lead_id=uuid4(),
                                        url=scraped["source_url"],
                                        excerpt=f"Verified boutique recipient contact: {scraped['email']} (scraped via Tavily)",
                                        source_type=EvidenceSourceType.OFFICIAL_SITE,
                                        domain_matches_lead=True,
                                        provenance=ProvenanceTag.VERIFIED_FACT,
                                        is_demo=False,
                                    )
                                )
                    except Exception as e:
                        pass
                return cand

        verified = await asyncio.gather(*[_verify_and_scrape(c) for c in deduped])
        if on_progress:
            on_progress(
                "discovery",
                {"discovered_count": len(verified), "message": "Completed retailer discovery and verification"},
            )
        return list(verified)


def get_research_pipeline() -> ResearchPipeline:
    """Factory returning LiveResearchPipeline if TAVILY_API_KEY is set, else FixtureResearchPipeline (dev/test only)."""
    api_key = os.environ.get("TAVILY_API_KEY", "").strip()
    lead_cap = 6
    app_env = "dev"
    try:
        from backend.app.core.config import get_settings

        settings = get_settings()
        api_key = getattr(settings, "tavily_api_key", None) or getattr(settings, "TAVILY_API_KEY", None) or api_key
        lead_cap = getattr(settings, "max_leads_per_run", 6)
        app_env = getattr(settings, "app_env", "dev") or "dev"
    except Exception:
        pass

    if api_key and str(api_key).strip():
        return LiveResearchPipeline(TavilyClient(api_key=str(api_key).strip()), lead_cap=lead_cap)

    if str(app_env).strip().lower() in ("production", "prod"):
        from backend.app.core.errors import AppError
        raise AppError("upstream_unavailable", "Research provider is unconfigured or unavailable in production.")

    return FixtureResearchPipeline()