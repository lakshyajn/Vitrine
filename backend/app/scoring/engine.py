"""
Deterministic Lead Scoring and Tiering Engine.

Precedence:
- AGENT.md Section 6 (Scoring & Tiering), Section 7 (Truth Rules), Section 11 (DECISION-D6, DECISION-D14)
- WS2_Spec.md Section 6 (Transparent Lead Ranking)

Guarantees:
- Deterministic arithmetic (no LLM in scoring loops).
- unknown strictly preserves None (never 0, never 20).
- Missing evidence always moves toward needs_review, never unqualified.
- Weights renormalize to 100% when 1-3 dimensions are None.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any
from uuid import UUID

from contracts.schemas import (
    DimensionLabel,
    EvidenceSourceType,
    LeadScores,
    LeadTier,
)
from backend.app.scoring.config import (
    DEFAULT_DIMENSION_WEIGHTS,
    EVIDENCE_RECENCY_MONTHS,
    QUALIFIED_MIN_EVIDENCE_QUALITY,
    RETAIL_ACTIVITY_SOURCE_TYPES,
    map_label_to_score,
)

# Contact info regex & keywords for evidence excerpts
_EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
_CONTACT_KEYWORDS = (
    "contact",
    "email:",
    "phone:",
    "tel:",
    "hello@",
    "info@",
    "reach us",
    "get in touch",
    "store locator",
    "visit us",
)


def _get_item_attr(item: Any, key: str, default: Any = None) -> Any:
    """Safely extract attribute or dictionary key from an evidence item."""
    if item is None:
        return default
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _get_source_type_str(item: Any) -> str:
    """Extract source_type as clean lowercase string."""
    st = _get_item_attr(item, "source_type", "")
    if hasattr(st, "value"):
        st = st.value
    return str(st).strip().lower()


def _is_within_recency(dt_val: Any, months: int = EVIDENCE_RECENCY_MONTHS, now_dt: datetime | None = None) -> bool:
    """
    Check if a published_at or retrieved_at date falls within the last 24 months.
    Missing date adds 0, subtracts 0 (returns False).
    """
    if dt_val is None:
        return False

    if now_dt is None:
        now_dt = datetime.now(timezone.utc)
    elif now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=timezone.utc)

    if isinstance(dt_val, str):
        clean_str = dt_val.strip()
        if not clean_str:
            return False
        try:
            dt = datetime.fromisoformat(clean_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return False
    elif isinstance(dt_val, datetime):
        dt = dt_val
    else:
        return False

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    max_days = months * 30.5  # ~732 days
    diff_days = (now_dt - dt).total_seconds() / 86400.0

    # Allow slight clock skew (-2 days) up to max_days (24 months)
    return -2.0 <= diff_days <= max_days


def _has_verified_location(lead: Any) -> bool:
    """Check if lead.location is non-null with actual location information."""
    if lead is None:
        return False
    loc = _get_item_attr(lead, "location")
    if loc is None:
        return False
    if isinstance(loc, dict):
        return any(bool(v and str(v).strip()) for v in loc.values())
    if hasattr(loc, "city") or hasattr(loc, "region") or hasattr(loc, "country"):
        return any(
            bool(getattr(loc, attr, None) and str(getattr(loc, attr)).strip())
            for attr in ("city", "region", "country")
        )
    if isinstance(loc, str):
        return bool(loc.strip())
    return True


def _has_contact_info_in_excerpts(evidence_items: list[Any] | None) -> bool:
    """Check if contact information is cited in any evidence excerpt (DECISION-D6)."""
    if not evidence_items:
        return False
    for item in evidence_items:
        excerpt = _get_item_attr(item, "excerpt", "")
        if not excerpt:
            continue
        text = str(excerpt)
        lower_text = text.lower()
        if any(kw in lower_text for kw in _CONTACT_KEYWORDS):
            return True
        if _EMAIL_REGEX.search(text):
            return True
        if _PHONE_REGEX.search(text):
            return True
    return False


def _is_retail_activity(item: Any) -> bool:
    """Check if evidence item is official_site or product_page (DECISION-D6)."""
    st = _get_source_type_str(item)
    return st in RETAIL_ACTIVITY_SOURCE_TYPES


def _extract_dimension_assessment(assessment: Any, dim_name: str) -> tuple[str | None, list[str], list[UUID | str]]:
    """Safely extract (label, reasons, evidence_ids) for a dimension from assessment."""
    if assessment is None:
        return None, [], []

    dim = assessment.get(dim_name) if isinstance(assessment, dict) else getattr(assessment, dim_name, None)
    if dim is None:
        return None, [], []

    if isinstance(dim, dict):
        label = dim.get("label")
        reasons = dim.get("reasons", []) or []
        evidence_ids = dim.get("evidence_ids", []) or []
    else:
        label = getattr(dim, "label", None)
        reasons = getattr(dim, "reasons", []) or []
        evidence_ids = getattr(dim, "evidence_ids", []) or []

    if hasattr(label, "value"):
        label = label.value

    return (str(label).strip().lower() if label is not None else None), list(reasons), list(evidence_ids)


# ==============================================================================
# 1. Deterministic Evidence Quality Calculation
# ==============================================================================
def compute_evidence_quality(
    lead: Any,
    evidence_items: list[Any] | None,
    now: datetime | None = None,
) -> int:
    """
    Compute evidence quality score deterministically from evidence metadata.
    Start at 0:
      +40 if any item has source_type == "official_site"
      +20 if >= 2 distinct source URLs
      +20 if any item has source_type == "product_page" with non-empty excerpt
      +10 if any item has published_at or retrieved_at within last 24 months (missing date adds 0, subtracts 0)
      +10 if lead.location is non-null or contact info is present in an excerpt (DECISION-D6)
    Cap at 100.
    """
    score = 0
    items = evidence_items or []

    # 1. +40 if official_site page present
    if any(_get_source_type_str(it) == "official_site" for it in items):
        score += 40

    # 2. +20 if >= 2 distinct source URLs
    clean_urls = set()
    for it in items:
        u = _get_item_attr(it, "url")
        if u and str(u).strip():
            clean_urls.add(str(u).strip().rstrip("/"))
    if len(clean_urls) >= 2:
        score += 20

    # 3. +20 if product_page with non-empty excerpt
    has_product_page_excerpt = False
    for it in items:
        if _get_source_type_str(it) == "product_page":
            excerpt = _get_item_attr(it, "excerpt", "")
            if excerpt and str(excerpt).strip():
                has_product_page_excerpt = True
                break
    if has_product_page_excerpt:
        score += 20

    # 4. +10 if published_at or retrieved_at within last 24 months
    has_recent_date = False
    for it in items:
        pub = _get_item_attr(it, "published_at")
        ret = _get_item_attr(it, "retrieved_at")
        if _is_within_recency(pub, now_dt=now) or _is_within_recency(ret, now_dt=now):
            has_recent_date = True
            break
    if has_recent_date:
        score += 10

    # 5. +10 if lead.location is non-null or contact info is present in excerpt
    if _has_verified_location(lead) or _has_contact_info_in_excerpts(items):
        score += 10

    return min(100, max(0, score))


# ==============================================================================
# 2. Overall Score & Completeness Calculation
# ==============================================================================
def compute_overall_and_completeness(
    category_fit: float | None,
    aesthetic_fit: float | None,
    evidence_quality: float | None,
    seller_compat: float | None,
    weights: dict[str, float] | None = None,
) -> tuple[float | None, float]:
    """
    Compute completeness = non_null_count / 4.0.
    Compute overall = weighted average over non-null dimensions with weights renormalized to 100%.
    If all 4 dimensions are None, overall is None.
    """
    if weights is None:
        weights = DEFAULT_DIMENSION_WEIGHTS

    dims: dict[str, float | None] = {
        "category_fit": category_fit,
        "aesthetic_fit": aesthetic_fit,
        "evidence_quality": evidence_quality,
        "seller_compat": seller_compat,
    }

    non_null_dims = {k: v for k, v in dims.items() if v is not None}
    completeness = len(non_null_dims) / 4.0

    if not non_null_dims:
        return None, completeness

    total_weight = sum(weights[k] for k in non_null_dims)
    if total_weight <= 0:
        return None, completeness

    weighted_sum = sum(weights[k] * non_null_dims[k] for k in non_null_dims)  # type: ignore[operator]
    overall = round(weighted_sum / total_weight, 2)
    return overall, completeness


# ==============================================================================
# 3. Comprehensive Scoring & Tiering Engine
# ==============================================================================
def compute_scores_and_tier(
    lead_candidate: Any,
    evidence_items: list[Any] | None,
    assessment: Any,
    is_excluded_domain: bool = False,
    now: datetime | None = None,
) -> tuple[LeadScores, LeadTier]:
    """
    Compute dimension scores, overall priority score, completeness, tier, and human-readable tier reasons.

    Rules:
    - Map category_fit, aesthetic_fit, seller_compat labels to 100/60/20/None (NEVER turn unknown into 0).
    - Compute completeness = non_null_count / 4.0.
    - Compute overall: weighted average over non-null dimensions with weights renormalized to 100%.
      If all 4 dimensions are None, overall is None.
    - Evaluate Tier Gates (Section 6.3 & DECISION-D6):
      * qualified: website_verified is True AND >= 1 retail-activity evidence (official_site or product_page)
                   AND category_fit in (high, medium) AND evidence_quality >= 40.
      * unqualified: website_verified is False OR (category_fit == "low" with non-empty evidence_ids)
                     OR is_excluded_domain is True.
      * needs_review: all other cases (missing evidence ALWAYS moves toward needs_review, never unqualified).
    - Populate human-readable tier_reasons: list[str] in LeadScores explaining why the tier was assigned.
    """
    # 1. Extract dimension labels & evidence IDs from assessment
    cat_label, cat_reasons, cat_evidence_ids = _extract_dimension_assessment(assessment, "category_fit")
    aes_label, aes_reasons, aes_evidence_ids = _extract_dimension_assessment(assessment, "aesthetic_fit")
    sel_label, sel_reasons, sel_evidence_ids = _extract_dimension_assessment(assessment, "seller_compat")

    # 2. Map labels to deterministic scores (unknown -> None, never 0)
    category_fit_score = map_label_to_score(cat_label)
    aesthetic_fit_score = map_label_to_score(aes_label)
    seller_compat_score = map_label_to_score(sel_label)

    # 3. Compute evidence quality (if evidence_items is None, dimension is None)
    if evidence_items is None:
        evidence_quality_score: float | None = None
    else:
        evidence_quality_score = float(compute_evidence_quality(lead_candidate, evidence_items, now=now))

    # 4. Overall score & completeness
    overall, completeness = compute_overall_and_completeness(
        category_fit=category_fit_score,
        aesthetic_fit=aesthetic_fit_score,
        evidence_quality=evidence_quality_score,
        seller_compat=seller_compat_score,
    )

    # 5. Extract verification & retail activity flags
    website_verified = _get_item_attr(lead_candidate, "website_verified")
    has_retail_activity = any(_is_retail_activity(it) for it in (evidence_items or []))

    # Low category fit condition (score 20.0 or label "low"/"mismatch")
    is_category_low = (category_fit_score == 20.0) or (cat_label in ("low", "mismatch"))
    has_cat_evidence = len(cat_evidence_ids) > 0

    # 6. Evaluate Tier Gates
    # Gate A: unqualified
    # Condition: website_verified is False OR (category_fit == "low" with non-empty evidence_ids) OR is_excluded_domain is True
    is_unqualified = False
    unqualified_reasons: list[str] = []

    if is_excluded_domain:
        is_unqualified = True
        unqualified_reasons.append("Domain is excluded as a marketplace, wholesaler, or retail chain")

    if website_verified is False:
        is_unqualified = True
        unqualified_reasons.append("Website could not be verified (failed HTTP/liveness check)")

    if is_category_low and has_cat_evidence:
        is_unqualified = True
        unqualified_reasons.append("Low category fit confirmed by evidence citations")

    if is_unqualified:
        tier = LeadTier.UNQUALIFIED
        tier_reasons = unqualified_reasons

    # Gate B: qualified
    # Condition: website_verified is True AND >= 1 retail-activity evidence AND category_fit in (high, medium) AND evidence_quality >= 40
    elif (
        website_verified is True
        and has_retail_activity
        and (category_fit_score in (100.0, 60.0))
        and (evidence_quality_score is not None and evidence_quality_score >= QUALIFIED_MIN_EVIDENCE_QUALITY)
    ):
        tier = LeadTier.QUALIFIED
        tier_reasons = [
            "Website verified via active HTTP response",
            "Retail-activity evidence present (official_site or product_page)",
            f"Category fit is {cat_label or 'high/medium'}",
            f"Evidence quality score ({int(evidence_quality_score)}) meets qualification threshold (>= {QUALIFIED_MIN_EVIDENCE_QUALITY})",
        ]

    # Gate C: needs_review
    # All other cases (missing evidence ALWAYS moves toward needs_review, never unqualified)
    else:
        tier = LeadTier.NEEDS_REVIEW
        tier_reasons = []

        if website_verified is None:
            tier_reasons.append("Website verification status is pending or missing")
        elif website_verified is True:
            tier_reasons.append("Website verified via active HTTP response")

        if not has_retail_activity:
            tier_reasons.append("Missing retail-activity evidence (no official site or product page found)")
        else:
            tier_reasons.append("Retail-activity evidence present")

        if category_fit_score is None:
            tier_reasons.append("Category fit is unknown or lacks sufficient evidence")
        elif is_category_low and not has_cat_evidence:
            tier_reasons.append("Low category fit lacks supporting evidence citations (requires manual review)")
        elif category_fit_score not in (100.0, 60.0):
            tier_reasons.append(f"Category fit ({cat_label}) does not meet qualified threshold")

        if evidence_quality_score is None:
            tier_reasons.append("Evidence quality could not be computed (missing evidence items)")
        elif evidence_quality_score < QUALIFIED_MIN_EVIDENCE_QUALITY:
            tier_reasons.append(
                f"Evidence quality score ({int(evidence_quality_score)}) is below qualification threshold (< {QUALIFIED_MIN_EVIDENCE_QUALITY})"
            )

        if assessment is None:
            tier_reasons.append("Lead assessment is missing or incomplete")

        if not tier_reasons:
            tier_reasons.append("Incomplete qualification evidence requires manual review")

    lead_scores = LeadScores(
        category_fit=category_fit_score,
        aesthetic_fit=aesthetic_fit_score,
        evidence_quality=evidence_quality_score,
        seller_compat=seller_compat_score,
        overall=overall,
        completeness=completeness,
        tier_reasons=tier_reasons,
    )

    return lead_scores, tier
