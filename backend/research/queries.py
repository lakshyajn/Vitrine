# backend/research/queries.py
"""
Search Query Templates, Validator, and Planner (WS3 Section 4.1).
Category-aware query generation and strict product-grounded validation.
"""

from __future__ import annotations

import re
from typing import Any
from contracts.schemas import Product, ResearchPlan, TasteAnchor

# Universal retail-intent templates that work for ANY product category
UNIVERSAL_RETAIL_TEMPLATES = (
    "{category} shop {region}",
    "independent {category} retailer {region}",
    "{category} stockist OR supplier to shops {region}",
    "buy {name} online store {region}",
)

# Small retail-intent allowlist of terms permitted in queries
RETAIL_INTENT_ALLOWLIST = {
    "shop", "shops", "store", "stores", "retailer", "retailers",
    "stockist", "stockists", "boutique", "boutiques", "buy", "wholesale",
    "independent", "online", "supplier", "suppliers", "selling", "curated",
    "collection", "collections", "studio", "goods", "design", "curation",
    "or", "and", "to", "for", "in", "of", "with", "the", "a", "an", "by", "at",
}

STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "to", "for", "of", "with", "by", "at",
    "from", "on", "into", "all", "is", "it", "near", "best", "top", "our",
}


def _stem(token: str) -> str:
    """Simple defensive English stemmer for category and keyword matching."""
    t = token.lower().strip()
    for suffix in ("ing", "ers", "er", "es", "s", "ed"):
        if t.endswith(suffix) and len(t) > len(suffix) + 2:
            return t[:-len(suffix)]
    return t


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in re.sub(r"[^\w\s]", " ", text).split() if w.strip()]


def _normalize_query(q: str) -> str:
    tokens = re.sub(r"[^\w\s]", " ", q.lower()).split()
    return " ".join(sorted(set(tokens)))


def get_product_token_set(product: Product, plan: ResearchPlan | None = None) -> tuple[set[str], set[str]]:
    """
    Returns (category_tokens, all_product_allowed_tokens) with stemmed variants.
    """
    category_raw = _tokenize(f"{product.category} {product.name}")
    category_stems = {_stem(t) for t in category_raw if t not in STOP_WORDS}
    category_stems.update(category_raw)

    all_raw = list(category_raw)
    for lst in (product.materials, product.style, product.motifs, product.colours, product.target_retailer_types):
        for item in (lst or []):
            all_raw.extend(_tokenize(str(item)))

    if plan:
        for r in (plan.target_regions or []):
            all_raw.extend(_tokenize(str(r)))
        for rt in (plan.target_retailer_types or []):
            all_raw.extend(_tokenize(str(rt)))

    all_stems = {_stem(t) for t in all_raw if t not in STOP_WORDS}
    all_stems.update(all_raw)

    return category_stems, all_stems


def validate_search_query(query: str, product: Product, plan: ResearchPlan | None = None) -> tuple[bool, str | None]:
    """
    Validates a search query:
    1. Must contain at least one product-category or name token (stemmed).
    2. Must not contain terms that appear nowhere in product record, regions, or retail-intent allowlist.
    """
    clean_q = " ".join(query.strip().split())
    if not clean_q:
        return False, "Empty query"

    q_tokens = _tokenize(clean_q)
    category_tokens, allowed_tokens = get_product_token_set(product, plan)

    # 1. Check for product category or name token presence
    has_category_token = False
    for tok in q_tokens:
        if tok in category_tokens or _stem(tok) in category_tokens:
            has_category_token = True
            break

    if not has_category_token:
        return False, f"Query '{clean_q}' lacks product-category or name tokens for '{product.category}'"

    # 2. Check each token against allowlist + product record
    for tok in q_tokens:
        if tok in STOP_WORDS or tok in RETAIL_INTENT_ALLOWLIST:
            continue
        stemmed = _stem(tok)
        if (
            tok in allowed_tokens
            or stemmed in allowed_tokens
            or tok in RETAIL_INTENT_ALLOWLIST
            or stemmed in RETAIL_INTENT_ALLOWLIST
        ):
            continue
        # Unrecognized term that appears nowhere in product, plan, or allowlist
        return False, f"Query '{clean_q}' contains foreign token '{tok}' not in product record or retail allowlist"

    return True, None


def build_research_queries(
    product: Product,
    plan: ResearchPlan,
    anchors: list[TasteAnchor],
    max_queries: int = 8,
) -> list[str]:
    """
    Builds category-aware, retail-intent search queries from actual product fields.
    Validates and deduplicates queries, keeping up to max_queries (default 8).
    """
    regions = [r.strip() for r in (plan.target_regions or [""]) if r.strip()] or [""]
    raw_queries: list[str] = []

    # 1. Confirmed taste anchors prioritized at top
    confirmed_labels = [
        a.label.strip() for a in anchors if str(a.status) == "confirmed" and a.label and a.label.strip()
    ]
    if confirmed_labels:
        for label in confirmed_labels:
            raw_queries.append(f"independent {product.category} boutique stockist {label}")
            raw_queries.append(f"lifestyle boutique stockist {product.category} similar to {label}")

    # 2. Add and validate plan.search_queries
    dropped_count = 0
    for q in (plan.search_queries or []):
        is_valid, reason = validate_search_query(q, product, plan)
        if is_valid:
            raw_queries.append(q)
        else:
            dropped_count += 1

    if dropped_count > 0:
        drop_note = f"[{dropped_count} search queries dropped: irrelevant or ungrounded]"
        plan.notes = f"{plan.notes} {drop_note}".strip() if plan.notes else drop_note

    # 3. Parameterized retailer-intent templates
    retailer_types = (
        product.target_retailer_types
        or plan.target_retailer_types
        or []
    )
    style_spec = f"{product.style[0]} " if product.style else ""
    materials_spec = f"{product.materials[0]} " if product.materials else ""

    for region in regions[:3]:
        reg_clean = region.strip()
        reg_str = f" {reg_clean}" if reg_clean else ""

        for tmpl in UNIVERSAL_RETAIL_TEMPLATES:
            formatted = tmpl.format(
                category=product.category,
                name=product.name,
                region=reg_clean,
            ).strip()
            raw_queries.append(" ".join(formatted.split()))

        # Retailer type template if retailer type is specified
        if retailer_types:
            rt = retailer_types[0]
            raw_queries.append(f"{rt} selling {product.category}{reg_str}".strip())

        # Material / Style enriched template if present
        if style_spec or materials_spec:
            spec = (style_spec + materials_spec).strip()
            raw_queries.append(f"independent {spec} {product.category} boutique{reg_str}".strip())

    # Deduplicate and cap
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
