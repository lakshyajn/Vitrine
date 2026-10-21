"""Scoring and Tiering Engine."""

from backend.app.scoring.config import (
    AESTHETIC_FIT_WEIGHT,
    CATEGORY_FIT_WEIGHT,
    DEFAULT_DIMENSION_WEIGHTS,
    DEFAULT_EXCLUDED_DOMAINS,
    EVIDENCE_QUALITY_WEIGHT,
    EVIDENCE_RECENCY_MONTHS,
    LABEL_TO_SCORE_MAP,
    PRELIMINARY_COMPLETENESS_THRESHOLD,
    QUALIFIED_MIN_EVIDENCE_QUALITY,
    RETAIL_ACTIVITY_SOURCE_TYPES,
    SELLER_COMPAT_WEIGHT,
    is_domain_excluded,
    map_label_to_score,
)
from backend.app.scoring.engine import (
    compute_evidence_quality,
    compute_overall_and_completeness,
    compute_scores_and_tier,
)

__all__ = [
    "AESTHETIC_FIT_WEIGHT",
    "CATEGORY_FIT_WEIGHT",
    "DEFAULT_DIMENSION_WEIGHTS",
    "DEFAULT_EXCLUDED_DOMAINS",
    "EVIDENCE_QUALITY_WEIGHT",
    "EVIDENCE_RECENCY_MONTHS",
    "LABEL_TO_SCORE_MAP",
    "PRELIMINARY_COMPLETENESS_THRESHOLD",
    "QUALIFIED_MIN_EVIDENCE_QUALITY",
    "RETAIL_ACTIVITY_SOURCE_TYPES",
    "SELLER_COMPAT_WEIGHT",
    "compute_evidence_quality",
    "compute_overall_and_completeness",
    "compute_scores_and_tier",
    "is_domain_excluded",
    "map_label_to_score",
]
