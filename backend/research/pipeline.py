"""
Research Pipeline Interface, FixtureResearchPipeline, and LiveResearchPipeline (WS3 Section 4).
Matches Contract v0.2 Appendix A.6 and keeps WS2's existing tests 100% passing.
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any, Callable, Protocol
from uuid import uuid4

from backend.research.dedupe import deduplicate_lead_candidates, extract_canonical_domain
from backend.research.evidence import (
    classify_evidence_source_type,
    is_domain_excluded_detailed,
    is_excluded_retailer_domain,
    verify_website_http,
)
from backend.research.queries import (
    STOP_WORDS,
    _stem,
    _tokenize,
    build_research_queries,
    get_product_token_set,
)
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
    RetailerKind,
    TasteAnchor,
)

RETAIL_INTENT_PATTERN = re.compile(
    r"(?:[$€£₹]\s*\d+|\b\d+(?:\.\d{2})?\s*(?:usd|eur|gbp|inr)\b|"
    r"\b(?:add\s+to\s+(?:cart|basket)|in\s+stock|out\s+of\s+stock|checkout|view\s+cart|"
    r"buy\s+online|shop\s+now|store|stockist|stockists|boutique|wholesale|supplier\s+to\s+shops|"
    r"collection|collections|catalogue|free\s+shipping|order\s+online)\b)",
    re.IGNORECASE,
)


def prettify_domain_name(domain: str) -> str:
    """Prettify domain name into a clean readable store name."""
    clean = (domain or "").lower().strip()
    if clean.startswith("www."):
        clean = clean[4:]
    clean = clean.split(":")[0]
    for sfx in (".co.uk", ".com.au", ".co.in", ".gov.in", ".org.uk", ".co.nz", ".store", ".shop"):
        if clean.endswith(sfx):
            clean = clean[:-len(sfx)]
            break
    else:
        clean = clean.rsplit(".", 1)[0]
    words = [w for w in re.split(r"[-_.]", clean) if w]
    return " ".join(w.capitalize() for w in words) if words else domain


def derive_retailer_name(hit: dict[str, Any], canonical_domain: str) -> str:
    """
    Derive the retailer name from site-level information, never raw page title.
    1. site_name in hit metadata (if extracted)
    2. Brand token in title matching the domain base
    3. Prettified domain label
    """
    site_name = str(hit.get("site_name") or hit.get("siteName") or "").strip()
    if site_name and 1 < len(site_name) < 60:
        return site_name

    prettified = prettify_domain_name(canonical_domain)
    clean_base = re.sub(r"[^a-z0-9]", "", prettified.lower())

    title = str(hit.get("title") or "").strip()
    if title:
        parts = [p.strip() for p in re.split(r"[|–—:•]", title) if p.strip()]
        if len(parts) > 1:
            for part in parts:
                clean_p = re.sub(r"[^a-z0-9]", "", part.lower())
                if clean_p and (clean_p in clean_base or clean_base in clean_p):
                    return part

    return prettified


def evaluate_hit_relevance(
    hit: dict[str, Any],
    product: Product,
    plan: ResearchPlan | None = None,
) -> tuple[bool, list[str]]:
    """
    Deterministic pre-lead relevance check.
    Returns (keep: bool, relevance_hints: list[str]).
    A hit is dropped only if it has NEITHER category-term match NOR retail-intent signals.
    """
    category_tokens, _ = get_product_token_set(product, plan)
    title = str(hit.get("title") or "").strip()
    content = str(hit.get("content") or "").strip()
    text = f"{title} {content}".lower()

    hit_words = set(_tokenize(text))
    hit_stems = {_stem(w) for w in hit_words if w not in STOP_WORDS}
    all_hit_tokens = hit_words | hit_stems

    has_category = bool(category_tokens.intersection(all_hit_tokens))
    has_retail = bool(RETAIL_INTENT_PATTERN.search(text))

    if not has_category and not has_retail:
        return False, []

    hints: list[str] = []
    if has_category and not has_retail:
        hints.append("category_match_only")
    elif has_retail and not has_category:
        hints.append("retail_intent_only")
    else:
        hints.append("category_and_retail_intent")

    return True, hints


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

        cat = (product.category or "curated goods").strip()
        nm = (product.name or "handcrafted goods").strip()

        candidate1 = LeadCandidate(
            name=f"Atelier Living & Design",
            website="https://www.atelierlivingdemo.com",
            canonical_domain="atelierlivingdemo.com",
            location=LeadLocation(city="Amsterdam", region="North Holland", country="Netherlands"),
            retailer_kind=RetailerKind.RETAILER,
            retailer_type=None,
            website_verified=True,
            possible_duplicate_of_domain=None,
            contact_email="contact@atelierlivingdemo.com",
            evidence=[
                EvidenceItem(
                    id=uuid4(),
                    lead_id=lead1_id,
                    url="https://www.atelierlivingdemo.com/about",
                    excerpt=f"We stock independent artisanal goods, {cat.lower()}, and design collections from ethical makers.",
                    source_type=EvidenceSourceType.OFFICIAL_SITE,
                    domain_matches_lead=True,
                    provenance=ProvenanceTag.VERIFIED_FACT,
                    is_demo=True,
                ),
                EvidenceItem(
                    id=uuid4(),
                    lead_id=lead1_id,
                    url=f"https://www.atelierlivingdemo.com/collections/{cat.lower().replace(' ', '-')}",
                    excerpt=f"Handcrafted {nm.lower()} and curated {cat.lower()} collections.",
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
            retailer_kind=RetailerKind.RETAILER,
            retailer_type=None,
            website_verified=True,
            possible_duplicate_of_domain=None,
            contact_email="hello@thebotanistshopdemo.co.uk",
            evidence=[
                EvidenceItem(
                    id=uuid4(),
                    lead_id=lead2_id,
                    url="https://www.thebotanistshopdemo.co.uk",
                    excerpt=f"Curated living goods, design objects, and independent {cat.lower()}.",
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

        total_hits = len(hits)
        if not hits:
            plan.notes = "Tavily search returned zero matching retailer pages; no candidates generated."
            if on_progress:
                on_progress("discovery", {"discovered_count": 0, "message": plan.notes})
            return []

        raw_candidates: list[LeadCandidate] = []
        filtered_count = 0

        for hit in hits[:16]:  # Cap at top 16 search extractions per run
            url = str(hit.get("url") or "").strip()
            if not url:
                filtered_count += 1
                continue

            excluded, excl_reason = is_domain_excluded_detailed(url)
            if excluded:
                filtered_count += 1
                continue

            dom = extract_canonical_domain(url)
            if not dom:
                filtered_count += 1
                continue

            excluded_dom, _ = is_domain_excluded_detailed(dom)
            if excluded_dom:
                filtered_count += 1
                continue

            keep, relevance_hints = evaluate_hit_relevance(hit, product, plan)
            if not keep:
                filtered_count += 1
                continue

            lead_id = uuid4()
            excerpt = str(hit.get("content") or "").strip()[:500]
            title = str(hit.get("title") or "").strip()
            source_type = classify_evidence_source_type(url, excerpt, lead_domain=dom)
            retailer_name = derive_retailer_name(hit, dom)

            cand_email = None
            found_emails = extract_emails_from_text(f"{excerpt} {title}", dom)
            if found_emails:
                scored = sorted([(e, score_and_rank_email(e, dom)) for e in found_emails], key=lambda x: x[1], reverse=True)
                if scored and scored[0][1] > 20:
                    cand_email = scored[0][0]

            evidence_text = f"{title}. {excerpt}" if title and not excerpt.startswith(title[:30]) else excerpt

            raw_candidates.append(
                LeadCandidate(
                    name=retailer_name,
                    website=f"https://{dom.split('/')[0]}",
                    canonical_domain=dom,
                    location=None,
                    retailer_kind=None,
                    retailer_type=None,
                    website_verified=False,
                    contact_email=cand_email,
                    evidence=[
                        EvidenceItem(
                            id=uuid4(),
                            lead_id=lead_id,
                            url=url,
                            excerpt=evidence_text[:500],
                            source_type=source_type,
                            domain_matches_lead=(extract_canonical_domain(url) == dom),
                            provenance=ProvenanceTag.VERIFIED_FACT,
                            is_demo=False,
                        )
                    ],
                )
            )

        if filtered_count > 0:
            filter_note = f"{filtered_count} of {total_hits} results filtered: not retail or not relevant"
            if plan.notes:
                plan.notes = f"{plan.notes} | {filter_note}"
            else:
                plan.notes = filter_note
            if on_progress:
                on_progress("discovery", {
                    "filtered_count": filtered_count,
                    "total_hits": total_hits,
                    "message": filter_note,
                })

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
                    except Exception:
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
        lead_cap = getattr(settings, "max_leads_per_run", 6) or 6
        app_env = getattr(settings, "app_env", "dev") or "dev"
    except Exception:
        pass

    if api_key:
        client = TavilyClient(api_key=api_key)
        return LiveResearchPipeline(client=client, lead_cap=lead_cap)

    if str(app_env).strip().lower() in ("production", "prod"):
        from backend.app.core.errors import AppError
        raise AppError("upstream_unavailable", "Tavily search provider is unconfigured or unavailable in production.")

    return FixtureResearchPipeline()
