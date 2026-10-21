"""
Lead Scoring & Prioritization Configuration.
Defines deterministic weights, dimension thresholds, and label-to-score mappings.

Precedence:
- AGENT.md Section 6 (Scoring & Tiering), Section 7 (Truth Rules), Section 11 (DECISION-D6, DECISION-D14)
- WS2_Spec.md Section 6 (Transparent Lead Ranking)
"""

from __future__ import annotations

from typing import Final

from contracts.schemas import DimensionLabel

# ==============================================================================
# 1. Dimension Weights (AGENT.md Section 6 & WS2_Spec Section 6.2)
# ==============================================================================
# Sum of weights must equal 100.0 across the 4 core retail dimensions.
CATEGORY_FIT_WEIGHT: Final[float] = 35.0
AESTHETIC_FIT_WEIGHT: Final[float] = 25.0
EVIDENCE_QUALITY_WEIGHT: Final[float] = 20.0
SELLER_COMPAT_WEIGHT: Final[float] = 20.0

DEFAULT_DIMENSION_WEIGHTS: Final[dict[str, float]] = {
    "category_fit": CATEGORY_FIT_WEIGHT,
    "aesthetic_fit": AESTHETIC_FIT_WEIGHT,
    "evidence_quality": EVIDENCE_QUALITY_WEIGHT,
    "seller_compat": SELLER_COMPAT_WEIGHT,
}

# ==============================================================================
# 2. Label to Score Mappings (DECISION-D14 & AGENT.md Section 6 & 7)
# ==============================================================================
# Wire format is strictly high | medium | low | unknown across all 3 dimensions.
# Mappings:
#   high -> 100
#   medium -> 60
#   low -> 20
#   unknown -> None (NEVER 0, NEVER 20)
# Defensive aliases:
#   match -> 100
#   adjacent -> 60
#   mismatch -> 20
LABEL_TO_SCORE_MAP: Final[dict[str, float | None]] = {
    "high": 100.0,
    "match": 100.0,
    "medium": 60.0,
    "adjacent": 60.0,
    "low": 20.0,
    "mismatch": 20.0,
    "unknown": None,
}

# ==============================================================================
# 3. Tiering & Quality Gate Thresholds (Section 6.3 & DECISION-D6)
# ==============================================================================
QUALIFIED_MIN_EVIDENCE_QUALITY: Final[int] = 40
PRELIMINARY_COMPLETENESS_THRESHOLD: Final[float] = 0.75
EVIDENCE_RECENCY_MONTHS: Final[int] = 24

# Retail-activity source types (DECISION-D6):
RETAIL_ACTIVITY_SOURCE_TYPES: Final[set[str]] = {
    "official_site",
    "product_page",
}

# Domains excluded by rule (marketplaces, global chains, wholesalers)
DEFAULT_EXCLUDED_DOMAINS: Final[set[str]] = {
    "amazon.com",
    "etsy.com",
    "ebay.com",
    "aliexpress.com",
    "alibaba.com",
    "walmart.com",
    "target.com",
    "wayfair.com",
    "faire.com",
}


def map_label_to_score(label: str | DimensionLabel | None) -> float | None:
    """
    Map dimension label to deterministic numeric score (0-100) or None.
    Preserves the critical truth rule: 'unknown' strictly maps to None, NEVER to 0.
    """
    if label is None:
        return None
    if isinstance(label, DimensionLabel):
        val = label.value
    else:
        val = str(label).strip().lower()

    if not val:
        return None

    return LABEL_TO_SCORE_MAP.get(val, None)


def is_domain_excluded(domain: str | None, excluded_domains: set[str] | None = None) -> bool:
    """
    Check if a canonical domain is an excluded marketplace or retail chain.
    """
    if not domain:
        return False
    clean = domain.strip().lower()
    target_set = excluded_domains if excluded_domains is not None else DEFAULT_EXCLUDED_DOMAINS
    return clean in target_set or any(clean.endswith("." + d) for d in target_set)
