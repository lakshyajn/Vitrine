# backend/research/queries.py
"""
Search Query Templates and Planner (WS3 Section 4.1).
Merges parameterized templates with plan.search_queries and deduplicates near-identical queries.
"""

from __future__ import annotations

import re
from contracts.schemas import Product, ResearchPlan, TasteAnchor

QUERY_TEMPLATES = (
    "independent home decor boutique {category} {style} {region}",
    "independent home textile retailer {materials} {motifs} stockist {region}",
    "interior and lifestyle shop curated {category} {colours} {region}",
)


def _normalize_query(q: str) -> str:
    tokens = re.sub(r"[^\w\s]", " ", q.lower()).split()
    return " ".join(sorted(set(tokens)))


def build_research_queries(
    product: Product,
    plan: ResearchPlan,
    anchors: list[TasteAnchor],
    max_queries: int = 4,
) -> list[str]:
    regions = plan.target_regions or [""]
    style_word = product.style[0] if product.style else "artisanal"
    material_word = product.materials[0] if product.materials else "cotton"
    motif_word = product.motifs[0] if product.motifs else "botanical"
    colour_word = product.colours[0] if product.colours else "earthy"

    raw_queries: list[str] = []

    # 1. Prioritize confirmed taste anchors at the very top of search
    confirmed_labels = [
        a.label for a in anchors if str(a.status) == "confirmed"
    ]
    if confirmed_labels:
        for label in confirmed_labels:
            raw_queries.append(f"independent boutique stockist {product.category} {label}")
            raw_queries.append(f"lifestyle boutique home decor similar to {label}")
    else:
        # 2. Add plan search queries if no anchors confirmed
        for q in (plan.search_queries or []):
            raw_queries.append(q)

        # 3. Add regional template queries
        for region in regions[:2]:
            for tmpl in QUERY_TEMPLATES:
                q = tmpl.format(
                    category=product.category,
                    style=style_word,
                    materials=material_word,
                    motifs=motif_word,
                    colours=colour_word,
                    region=region,
                ).strip()
                raw_queries.append(" ".join(q.split()))

    deduped: list[str] = []
    seen_signatures: set[str] = set()
    for q in raw_queries:
        clean = " ".join(q.split())
        if not clean:
            continue
        sig = _normalize_query(clean)
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            deduped.append(clean)
        if len(deduped) >= max_queries:
            break

    return deduped