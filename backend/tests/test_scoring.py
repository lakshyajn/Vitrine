"""
Comprehensive Unit Tests for Lead Scoring and Tiering Engine (Step 6 Deliverable).

Covers:
1. Scoring configuration constants and weights.
2. Label-to-score mappings (high, medium, low, unknown) and defensive aliases (match, adjacent, mismatch).
3. Strict preservation of 'unknown' -> None (never 0, never 20) across objects and serialization.
4. Deterministic evidence quality calculation (+40, +20, +20, +10, +10, capped at 100).
5. Weight renormalization across non-null dimensions: 0 missing, 1 missing, 2 missing, 3 missing, and all 4 missing (overall=None).
6. Completeness calculation and preliminary flag threshold (< 0.75).
7. Every Tier Gate:
   - qualified (verified + retail-activity + high/medium category fit + evidence_quality >= 40)
   - unqualified (unverified website OR category_fit low with evidence OR excluded domain)
   - needs_review (missing evidence always moves to needs_review, never unqualified)
8. Golden-set test with 10 realistic retailer leads validating expected tiers, scores, and tier reasons.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
import pytest

from contracts.schemas import (
    DimensionAssessment,
    DimensionLabel,
    EvidenceItem,
    EvidenceSourceType,
    LeadCandidate,
    LeadLocation,
    LeadScores,
    LeadTier,
    ProvenanceTag,
)
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
    SELLER_COMPAT_WEIGHT,
    is_domain_excluded,
    map_label_to_score,
)
from backend.app.scoring.engine import (
    compute_evidence_quality,
    compute_overall_and_completeness,
    compute_scores_and_tier,
)


# ==============================================================================
# Helper Factories
# ==============================================================================

def _make_candidate(
    name: str = "Test Retailer",
    website: str = "https://example.com",
    canonical_domain: str = "example.com",
    website_verified: bool | None = True,
    city: str | None = "Amsterdam",
    region: str | None = "North Holland",
    country: str | None = "Netherlands",
) -> LeadCandidate:
    loc = LeadLocation(city=city, region=region, country=country) if (city or region or country) else None
    return LeadCandidate(
        name=name,
        website=website,
        canonical_domain=canonical_domain,
        location=loc,
        retailer_type="boutique",
        website_verified=bool(website_verified) if website_verified is not None else False,
    )


def _make_evidence_item(
    source_type: EvidenceSourceType = EvidenceSourceType.OFFICIAL_SITE,
    url: str = "https://example.com/about",
    excerpt: str = "Artisanal home goods and table linens.",
    published_at: datetime | None = None,
    retrieved_at: datetime | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        id=uuid4(),
        lead_id=uuid4(),
        url=url,
        excerpt=excerpt,
        source_type=source_type,
        published_at=published_at,
        retrieved_at=retrieved_at if retrieved_at is not None else datetime.now(timezone.utc),
        domain_matches_lead=True,
        provenance=ProvenanceTag.VERIFIED_FACT,
    )


def _make_assessment_dict(
    category_label: str = "high",
    category_evidence_ids: list | None = None,
    aesthetic_label: str = "high",
    aesthetic_evidence_ids: list | None = None,
    seller_label: str = "high",
    seller_evidence_ids: list | None = None,
) -> dict:
    return {
        "category_fit": {
            "label": category_label,
            "reasons": ["Sells curated artisanal table linens and home decor."],
            "evidence_ids": category_evidence_ids if category_evidence_ids is not None else [uuid4()],
        },
        "aesthetic_fit": {
            "label": aesthetic_label,
            "reasons": ["Earthy palette and block-printed motifs align with catalogue."],
            "evidence_ids": aesthetic_evidence_ids if aesthetic_evidence_ids is not None else [uuid4()],
        },
        "seller_compat": {
            "label": seller_label,
            "reasons": ["Independent boutique price segment matches mid-premium tier."],
            "evidence_ids": seller_evidence_ids if seller_evidence_ids is not None else [uuid4()],
        },
        "summary": "Strong alignment across all dimensions.",
        "unknowns": [],
    }


# ==============================================================================
# 1. Scoring Config & Constants Tests
# ==============================================================================

def test_scoring_config_weights_and_constants() -> None:
    """Verify weights sum to 100.0 and all required constants match spec."""
    assert CATEGORY_FIT_WEIGHT == 35.0
    assert AESTHETIC_FIT_WEIGHT == 25.0
    assert EVIDENCE_QUALITY_WEIGHT == 20.0
    assert SELLER_COMPAT_WEIGHT == 20.0

    total_weight = (
        CATEGORY_FIT_WEIGHT + AESTHETIC_FIT_WEIGHT + EVIDENCE_QUALITY_WEIGHT + SELLER_COMPAT_WEIGHT
    )
    assert total_weight == 100.0

    assert DEFAULT_DIMENSION_WEIGHTS["category_fit"] == 35.0
    assert DEFAULT_DIMENSION_WEIGHTS["aesthetic_fit"] == 25.0
    assert DEFAULT_DIMENSION_WEIGHTS["evidence_quality"] == 20.0
    assert DEFAULT_DIMENSION_WEIGHTS["seller_compat"] == 20.0

    assert QUALIFIED_MIN_EVIDENCE_QUALITY == 40
    assert PRELIMINARY_COMPLETENESS_THRESHOLD == 0.75
    assert EVIDENCE_RECENCY_MONTHS == 24


def test_domain_exclusion_logic() -> None:
    """Verify default excluded marketplaces and custom domain handling."""
    assert is_domain_excluded("amazon.com") is True
    assert is_domain_excluded("shop.etsy.com") is True
    assert is_domain_excluded("wayfair.com") is True
    assert is_domain_excluded("independentboutique.com") is False
    assert is_domain_excluded(None) is False
    assert is_domain_excluded("") is False


# ==============================================================================
# 2. Label to Score Mappings & Defensive Aliases (D14)
# ==============================================================================

def test_label_to_score_mapping_canonical_and_defensive() -> None:
    """Verify high=100, medium=60, low=20, unknown=None, and defensive aliases."""
    # Canonical string mappings
    assert map_label_to_score("high") == 100.0
    assert map_label_to_score("medium") == 60.0
    assert map_label_to_score("low") == 20.0
    assert map_label_to_score("unknown") is None

    # Defensive aliases (DECISION-D14)
    assert map_label_to_score("match") == 100.0
    assert map_label_to_score("adjacent") == 60.0
    assert map_label_to_score("mismatch") == 20.0

    # DimensionLabel enum instances
    assert map_label_to_score(DimensionLabel.HIGH) == 100.0
    assert map_label_to_score(DimensionLabel.MEDIUM) == 60.0
    assert map_label_to_score(DimensionLabel.LOW) == 20.0
    assert map_label_to_score(DimensionLabel.UNKNOWN) is None

    # Case & whitespace resilience
    assert map_label_to_score("  HIGH  ") == 100.0
    assert map_label_to_score("Medium") == 60.0
    assert map_label_to_score("LOW") == 20.0
    assert map_label_to_score("Unknown") is None

    # Null, empty, and invalid strings strictly return None (NEVER 0)
    assert map_label_to_score(None) is None
    assert map_label_to_score("") is None
    assert map_label_to_score("not_a_valid_label") is None


# ==============================================================================
# 3. Truth Rule: unknown -> None Preservation
# ==============================================================================

def test_unknown_to_none_preservation_in_lead_scores() -> None:
    """
    CRITICAL TRUTH RULE (AGENT.md Section 7):
    unknown MUST strictly map to None in LeadScores and never coerce to 0.
    """
    candidate = _make_candidate()
    ev_item = _make_evidence_item(source_type=EvidenceSourceType.OFFICIAL_SITE)
    assessment = _make_assessment_dict(
        category_label="unknown",
        aesthetic_label="unknown",
        seller_label="unknown",
    )

    scores, tier = compute_scores_and_tier(candidate, [ev_item], assessment)

    # Dimension scores must be None, NOT 0.0
    assert scores.category_fit is None
    assert scores.category_fit != 0.0
    assert scores.aesthetic_fit is None
    assert scores.aesthetic_fit != 0.0
    assert scores.seller_compat is None
    assert scores.seller_compat != 0.0

    # Serialization test: model_dump preserves None
    dumped = scores.model_dump()
    assert dumped["category_fit"] is None
    assert dumped["aesthetic_fit"] is None
    assert dumped["seller_compat"] is None
    assert "0" not in str(dumped["category_fit"])


# ==============================================================================
# 4. Evidence Quality Calculation Tests
# ==============================================================================

def test_compute_evidence_quality_all_bonuses_capped_at_100() -> None:
    """
    Test individual bonuses:
      +40 official_site
      +20 >= 2 distinct URLs
      +20 product_page with non-empty excerpt
      +10 published/retrieved within 24 months
      +10 location non-null or contact in excerpt
    Cap at 100.
    """
    candidate = _make_candidate(city="London", country="UK")
    now_dt = datetime(2026, 10, 21, 12, 0, 0, tzinfo=timezone.utc)
    old_date = datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)  # > 24m ago
    recent_date = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)  # ~4m ago

    # 1. Base 0 when no evidence and no location
    cand_no_loc = _make_candidate(city=None, region=None, country=None)
    assert compute_evidence_quality(cand_no_loc, [], now=now_dt) == 0

    # 2. Only location gives +10
    assert compute_evidence_quality(candidate, [], now=now_dt) == 10

    # 3. Add official_site page with old date (no recency) -> +40
    ev1_old = _make_evidence_item(
        source_type=EvidenceSourceType.OFFICIAL_SITE,
        url="https://shop.com/about",
        published_at=old_date,
        retrieved_at=old_date,
    )
    assert compute_evidence_quality(cand_no_loc, [ev1_old], now=now_dt) == 40

    # 4. Add product_page with non-empty excerpt (old date) -> +20
    ev2_old = _make_evidence_item(
        source_type=EvidenceSourceType.PRODUCT_PAGE,
        url="https://shop.com/products/linen-runner",
        excerpt="Curated block-printed runner in earthy ochre.",
        published_at=old_date,
        retrieved_at=old_date,
    )
    # 2 distinct URLs (+20) + official_site (+40) + product_page excerpt (+20) = 80
    assert compute_evidence_quality(cand_no_loc, [ev1_old, ev2_old], now=now_dt) == 80

    # 5. Product page with EMPTY excerpt gives +0 for product page bonus
    ev2_empty_excerpt = ev2_old.model_copy(update={"excerpt": "   "})
    # Official (+40) + 2 URLs (+20) = 60
    assert compute_evidence_quality(cand_no_loc, [ev1_old, ev2_empty_excerpt], now=now_dt) == 60

    # 6. Recency check (+10) within 24 months
    ev_recent = ev1_old.model_copy(update={"published_at": recent_date})
    # Recent date adds +10 (40 + 10 = 50)
    assert compute_evidence_quality(cand_no_loc, [ev_recent], now=now_dt) == 50
    # Old date adds +0
    assert compute_evidence_quality(cand_no_loc, [ev1_old], now=now_dt) == 40

    # Missing dates via dict (published_at and retrieved_at None) adds +0
    ev_missing_dates = {
        "url": "https://shop.com/about",
        "source_type": "official_site",
        "excerpt": "About us",
        "published_at": None,
        "retrieved_at": None,
    }
    assert compute_evidence_quality(cand_no_loc, [ev_missing_dates], now=now_dt) == 40

    # 7. Contact info in excerpt when location is null (+10)
    ev_contact = _make_evidence_item(
        source_type=EvidenceSourceType.DIRECTORY,
        url="https://directory.com/listing",
        excerpt="Contact wholesale department at wholesale@boutique.co.uk or tel: +44 20 7946 0991",
        published_at=old_date,
        retrieved_at=old_date,
    )
    assert compute_evidence_quality(cand_no_loc, [ev_contact], now=now_dt) == 10

    # 8. All bonuses active capped at 100
    all_items = [ev_recent, ev2_old]
    # Official (40) + Distinct URLs (20) + Product page (20) + Recency (10) + Location (10) = 100
    assert compute_evidence_quality(candidate, all_items, now=now_dt) == 100


# ==============================================================================
# 5. Weight Renormalization & Completeness Tests
# ==============================================================================

def test_weight_renormalization_all_combinations() -> None:
    """
    Test overall score computation across all missing dimension states:
    - 0 missing: weights (35, 25, 20, 20) / 100
    - 1 missing: renormalized over remaining 3
    - 2 missing: renormalized over remaining 2
    - 3 missing: renormalized over remaining 1 (overall equals that score)
    - 4 missing: overall is None, completeness is 0.0
    """
    # 0 missing: all 4 present
    # category=100 (35), aesthetic=100 (25), evidence=80 (20), seller=60 (20)
    # Expected: (3500 + 2500 + 1600 + 1200) / 100 = 88.0
    ov, comp = compute_overall_and_completeness(100.0, 100.0, 80.0, 60.0)
    assert ov == 88.0
    assert comp == 1.0

    # 1 missing: seller_compat is None
    # Remaining weights: category 35, aesthetic 25, evidence 20 (Sum = 80)
    # Expected: (35*100 + 25*100 + 20*80) / 80 = (3500 + 2500 + 1600) / 80 = 7600 / 80 = 95.0
    ov, comp = compute_overall_and_completeness(100.0, 100.0, 80.0, None)
    assert ov == 95.0
    assert comp == 0.75

    # 1 missing: category_fit is None -> DECISION-D21: overall is None (priority not computable without relevance)
    ov, comp = compute_overall_and_completeness(None, 60.0, 80.0, 60.0)
    assert ov is None
    assert comp == 0.75

    # 2 missing: aesthetic_fit and seller_compat are None
    # Remaining weights: category 35, evidence 20 (Sum = 55)
    # Expected: (35*100 + 20*50) / 55 = 4500 / 55 = 81.82
    ov, comp = compute_overall_and_completeness(100.0, None, 50.0, None)
    assert ov == 81.82
    assert comp == 0.50

    # 3 missing: only category_fit is present (100.0)
    # Remaining weight: 35. Expected: (35 * 100.0) / 35 = 100.0
    ov, comp = compute_overall_and_completeness(100.0, None, None, None)
    assert ov == 100.0
    assert comp == 0.25

    # 3 missing: only evidence_quality is present (category_fit is None -> DECISION-D21: overall is None)
    ov, comp = compute_overall_and_completeness(None, None, 40.0, None)
    assert ov is None
    assert comp == 0.25

    # All 4 missing: all dimensions None
    # Expected: overall is None, completeness is 0.0
    ov, comp = compute_overall_and_completeness(None, None, None, None)
    assert ov is None
    assert comp == 0.0


def test_completeness_threshold_and_preliminary_badge() -> None:
    """Verify completeness is non_null_count / 4.0 and < 0.75 triggers preliminary."""
    _, comp_4 = compute_overall_and_completeness(100.0, 60.0, 80.0, 60.0)
    assert comp_4 == 1.0
    assert comp_4 >= PRELIMINARY_COMPLETENESS_THRESHOLD

    _, comp_3 = compute_overall_and_completeness(100.0, 60.0, 80.0, None)
    assert comp_3 == 0.75
    assert comp_3 >= PRELIMINARY_COMPLETENESS_THRESHOLD

    _, comp_2 = compute_overall_and_completeness(100.0, None, 80.0, None)
    assert comp_2 == 0.50
    assert comp_2 < PRELIMINARY_COMPLETENESS_THRESHOLD  # Preliminary badge in UI

    _, comp_1 = compute_overall_and_completeness(100.0, None, None, None)
    assert comp_1 == 0.25
    assert comp_1 < PRELIMINARY_COMPLETENESS_THRESHOLD

    _, comp_0 = compute_overall_and_completeness(None, None, None, None)
    assert comp_0 == 0.0
    assert comp_0 < PRELIMINARY_COMPLETENESS_THRESHOLD


# ==============================================================================
# 6. Tier Gate Tests (Qualified, Unqualified, Needs Review)
# ==============================================================================

def test_tier_gate_qualified() -> None:
    """
    Gate: qualified
    Condition: website_verified is True AND >= 1 retail-activity evidence AND category_fit in (high, medium) AND evidence_quality >= 40.
    """
    candidate = _make_candidate(website_verified=True, city="Berlin", country="Germany")
    ev1 = _make_evidence_item(source_type=EvidenceSourceType.OFFICIAL_SITE)
    ev2 = _make_evidence_item(
        source_type=EvidenceSourceType.PRODUCT_PAGE,
        url="https://example.com/shop/cushions",
        excerpt="Artisanal block-printed cushion collection.",
    )
    evidence = [ev1, ev2]

    # Test high category fit
    assessment_high = _make_assessment_dict(category_label="high")
    scores_high, tier_high = compute_scores_and_tier(candidate, evidence, assessment_high)
    assert tier_high == LeadTier.QUALIFIED
    assert any("Website verified" in r for r in scores_high.tier_reasons)
    assert any("Category fit is high" in r for r in scores_high.tier_reasons)
    assert scores_high.overall is not None and scores_high.overall >= 80.0

    # Test medium category fit
    assessment_med = _make_assessment_dict(category_label="medium")
    scores_med, tier_med = compute_scores_and_tier(candidate, evidence, assessment_med)
    assert tier_med == LeadTier.QUALIFIED
    assert any("Category fit is medium" in r for r in scores_med.tier_reasons)

    # Test defensive "match" alias
    assessment_match = _make_assessment_dict(category_label="match")
    _, tier_match = compute_scores_and_tier(candidate, evidence, assessment_match)
    assert tier_match == LeadTier.QUALIFIED

    # Test defensive "adjacent" alias
    assessment_adj = _make_assessment_dict(category_label="adjacent")
    _, tier_adj = compute_scores_and_tier(candidate, evidence, assessment_adj)
    assert tier_adj == LeadTier.QUALIFIED


def test_tier_gate_unqualified() -> None:
    """
    Gate: unqualified
    Condition: website_verified is False OR (category_fit == "low" with non-empty evidence_ids) OR is_excluded_domain is True.
    """
    ev = _make_evidence_item(source_type=EvidenceSourceType.OFFICIAL_SITE)

    # 1. website_verified is False
    candidate_unverified = _make_candidate(website_verified=False)
    assessment = _make_assessment_dict(category_label="high")
    scores_unv, tier_unv = compute_scores_and_tier(candidate_unverified, [ev], assessment)
    assert tier_unv == LeadTier.UNQUALIFIED
    assert any("could not be verified" in r for r in scores_unv.tier_reasons)

    # 2. category_fit == "low" with non-empty evidence_ids
    candidate_verified = _make_candidate(website_verified=True)
    ev_id = uuid4()
    assessment_low_with_evidence = _make_assessment_dict(
        category_label="low",
        category_evidence_ids=[ev_id],
    )
    scores_low, tier_low = compute_scores_and_tier(candidate_verified, [ev], assessment_low_with_evidence)
    assert tier_low == LeadTier.UNQUALIFIED
    assert any("Low category fit confirmed by evidence" in r for r in scores_low.tier_reasons)

    # 3. is_excluded_domain is True
    scores_excl, tier_excl = compute_scores_and_tier(
        candidate_verified, [ev], assessment, is_excluded_domain=True
    )
    assert tier_excl == LeadTier.UNQUALIFIED
    assert any("Domain is excluded" in r for r in scores_excl.tier_reasons)


def test_tier_gate_needs_review_missing_evidence_rule() -> None:
    """
    CRITICAL RULE: Missing evidence ALWAYS moves toward needs_review, NEVER unqualified.
    """
    candidate_verified = _make_candidate(website_verified=True)
    ev_official = _make_evidence_item(source_type=EvidenceSourceType.OFFICIAL_SITE)

    # 1. category_fit == "low" BUT with EMPTY evidence_ids (unsubstantiated/hallucinated low claim)
    # Must NOT become unqualified! Moves to needs_review.
    assessment_low_empty_evidence = _make_assessment_dict(
        category_label="low",
        category_evidence_ids=[],
    )
    scores_empty_ev, tier_empty_ev = compute_scores_and_tier(
        candidate_verified, [ev_official], assessment_low_empty_evidence
    )
    assert tier_empty_ev == LeadTier.NEEDS_REVIEW
    assert any("Low category fit lacks supporting evidence" in r for r in scores_empty_ev.tier_reasons)

    # 2. category_fit is "unknown" (no evidence either way) -> DECISION-D21: overall is None
    assessment_unknown = _make_assessment_dict(category_label="unknown")
    scores_unk, tier_unk = compute_scores_and_tier(candidate_verified, [ev_official], assessment_unknown)
    assert tier_unk == LeadTier.NEEDS_REVIEW
    assert scores_unk.overall is None
    assert any("Category fit unknown" in r for r in scores_unk.tier_reasons)

    # 3. Evidence quality below threshold (< 40)
    # Candidate with no location, single directory link (quality = 0)
    cand_no_loc = _make_candidate(city=None, region=None, country=None, website_verified=True)
    ev_directory = _make_evidence_item(
        source_type=EvidenceSourceType.DIRECTORY,
        url="https://directory.com/shop",
        published_at=None,
        retrieved_at=None,
    )
    assessment_high = _make_assessment_dict(category_label="high")
    scores_low_eq, tier_low_eq = compute_scores_and_tier(cand_no_loc, [ev_directory], assessment_high)
    assert tier_low_eq == LeadTier.NEEDS_REVIEW
    assert scores_low_eq.evidence_quality is not None and scores_low_eq.evidence_quality < 40
    assert any("below qualification threshold" in r for r in scores_low_eq.tier_reasons)

    # 4. Missing retail-activity evidence (only directory or press, no official_site or product_page)
    assert any("Missing retail-activity evidence" in r for r in scores_low_eq.tier_reasons)

    # 5. website_verified is None (verification pending)
    candidate_pending = _make_candidate(website_verified=None)
    # Set explicitly to None
    candidate_pending_dict = candidate_pending.model_dump()
    candidate_pending_dict["website_verified"] = None
    scores_pend, tier_pend = compute_scores_and_tier(candidate_pending_dict, [ev_official], assessment_high)
    assert tier_pend == LeadTier.NEEDS_REVIEW
    assert any("Website verification status is pending" in r for r in scores_pend.tier_reasons)

    # 6. assessment is None (AI task failure)
    scores_no_ass, tier_no_ass = compute_scores_and_tier(candidate_verified, [ev_official], None)
    assert tier_no_ass == LeadTier.NEEDS_REVIEW
    assert any("Lead assessment is missing" in r for r in scores_no_ass.tier_reasons)


# ==============================================================================
# 7. 10-Lead Golden Set Evaluation Test
# ==============================================================================

def test_golden_set_10_leads_ranking_and_tiering() -> None:
    """
    10-Lead Golden Set evaluating diverse realistic retailer profiles:
    - 3 Qualified leads (ideal boutique, medium-fit retailer, high-fit with missing seller_compat)
    - 3 Unqualified leads (unverified domain, low category fit with evidence, excluded marketplace)
    - 4 Needs Review leads (low fit lacking evidence, unknown category fit, weak evidence quality < 40, AI assessment failure)
    """
    fixed_now = datetime(2026, 10, 21, 12, 0, 0, tzinfo=timezone.utc)

    # --- Lead 1: Ideal Qualified Home & Design Boutique ---
    lead_1_cand = _make_candidate(
        name="The Conran Design Shop",
        website="https://conranshop.com",
        canonical_domain="conranshop.com",
        website_verified=True,
        city="London",
        country="UK",
    )
    lead_1_ev = [
        _make_evidence_item(
            source_type=EvidenceSourceType.OFFICIAL_SITE,
            url="https://conranshop.com/about",
            excerpt="High-end design emporium offering hand block-printed textiles and tableware.",
            published_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        ),
        _make_evidence_item(
            source_type=EvidenceSourceType.PRODUCT_PAGE,
            url="https://conranshop.com/products/linen-runners",
            excerpt="Artisanal cotton table runners in terracotta and indigo botanical prints.",
            published_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        ),
    ]
    lead_1_ass = _make_assessment_dict(category_label="high", aesthetic_label="high", seller_label="high")
    scores_1, tier_1 = compute_scores_and_tier(lead_1_cand, lead_1_ev, lead_1_ass, now=fixed_now)
    assert tier_1 == LeadTier.QUALIFIED
    assert scores_1.evidence_quality == 100.0
    assert scores_1.overall == 100.0
    assert scores_1.completeness == 1.0

    # --- Lead 2: Qualified Medium-Fit Lifestyle Boutique ---
    lead_2_cand = _make_candidate(
        name="Atelier Living",
        website="https://atelierliving.nl",
        canonical_domain="atelierliving.nl",
        website_verified=True,
        city="Amsterdam",
        country="Netherlands",
    )
    lead_2_ev = [
        _make_evidence_item(
            source_type=EvidenceSourceType.OFFICIAL_SITE,
            url="https://atelierliving.nl/about",
            published_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        ),
        _make_evidence_item(
            source_type=EvidenceSourceType.PRODUCT_PAGE,
            url="https://atelierliving.nl/collections/dining",
            excerpt="Curated lifestyle products and occasional textile collections.",
            published_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        ),
    ]
    lead_2_ass = _make_assessment_dict(category_label="medium", aesthetic_label="medium", seller_label="medium")
    scores_2, tier_2 = compute_scores_and_tier(lead_2_cand, lead_2_ev, lead_2_ass, now=fixed_now)
    assert tier_2 == LeadTier.QUALIFIED
    assert scores_2.evidence_quality == 100.0
    assert scores_2.overall == 68.0  # (35*60 + 25*60 + 20*100 + 20*60) / 100
    assert scores_2.completeness == 1.0

    # --- Lead 3: Qualified Boutique with Unknown Seller Compat & Missing Dates ---
    lead_3_cand = _make_candidate(
        name="Margot Maison",
        website="https://margotmaison.fr",
        canonical_domain="margotmaison.fr",
        website_verified=True,
        city="Paris",
        country="France",
    )
    lead_3_ev = [
        {
            "url": "https://margotmaison.fr/notre-histoire",
            "source_type": "official_site",
            "excerpt": "Notre atelier de textiles artisanaux.",
            "published_at": None,
            "retrieved_at": None,
        }
    ]
    # Official (40) + Location (10) = 50 evidence quality (>= 40)
    lead_3_ass = _make_assessment_dict(category_label="high", aesthetic_label="medium", seller_label="unknown")
    scores_3, tier_3 = compute_scores_and_tier(lead_3_cand, lead_3_ev, lead_3_ass, now=fixed_now)
    assert tier_3 == LeadTier.QUALIFIED
    assert scores_3.evidence_quality == 50.0
    assert scores_3.seller_compat is None
    # Weights: category(35)*100 + aesthetic(25)*60 + evidence(20)*50 = 3500 + 1500 + 1000 = 6000 / 80 = 75.0
    assert scores_3.overall == 75.0
    assert scores_3.completeness == 0.75

    # --- Lead 4: Unqualified - Website Offline / NXDOMAIN ---
    lead_4_cand = _make_candidate(
        name="Defunct Shop",
        website="https://defuncttextilesdemo.com",
        canonical_domain="defuncttextilesdemo.com",
        website_verified=False,
    )
    lead_4_ev = [_make_evidence_item(source_type=EvidenceSourceType.DIRECTORY)]
    lead_4_ass = _make_assessment_dict(category_label="high")
    scores_4, tier_4 = compute_scores_and_tier(lead_4_cand, lead_4_ev, lead_4_ass, now=fixed_now)
    assert tier_4 == LeadTier.UNQUALIFIED
    assert any("could not be verified" in r for r in scores_4.tier_reasons)

    # --- Lead 5: Unqualified - Low Category Fit Confirmed by Evidence ---
    lead_5_cand = _make_candidate(
        name="Metals & Industrial Hardware Ltd",
        website="https://industrialhardware.co.uk",
        canonical_domain="industrialhardware.co.uk",
        website_verified=True,
    )
    lead_5_ev_item = _make_evidence_item(source_type=EvidenceSourceType.OFFICIAL_SITE)
    lead_5_ass = _make_assessment_dict(
        category_label="low",
        category_evidence_ids=[lead_5_ev_item.id],
    )
    scores_5, tier_5 = compute_scores_and_tier(lead_5_cand, [lead_5_ev_item], lead_5_ass, now=fixed_now)
    assert tier_5 == LeadTier.UNQUALIFIED
    assert any("Low category fit confirmed by evidence" in r for r in scores_5.tier_reasons)

    # --- Lead 6: Unqualified - Excluded Marketplace / Global Chain ---
    lead_6_cand = _make_candidate(
        name="Amazon Global Storefront",
        website="https://amazon.com/shops/textiles",
        canonical_domain="amazon.com",
        website_verified=True,
    )
    lead_6_ev = [_make_evidence_item(source_type=EvidenceSourceType.OFFICIAL_SITE)]
    lead_6_ass = _make_assessment_dict(category_label="high")
    scores_6, tier_6 = compute_scores_and_tier(lead_6_cand, lead_6_ev, lead_6_ass, is_excluded_domain=True, now=fixed_now)
    assert tier_6 == LeadTier.UNQUALIFIED
    assert any("Domain is excluded" in r for r in scores_6.tier_reasons)

    # --- Lead 7: Needs Review - Low Category Fit but EMPTY Evidence IDs ---
    lead_7_cand = _make_candidate(
        name="Curio Antiques",
        website="https://curioantiques.com",
        canonical_domain="curioantiques.com",
        website_verified=True,
    )
    lead_7_ev = [_make_evidence_item(source_type=EvidenceSourceType.OFFICIAL_SITE)]
    lead_7_ass = _make_assessment_dict(
        category_label="low",
        category_evidence_ids=[],  # Hallucinated / missing evidence citations!
    )
    scores_7, tier_7 = compute_scores_and_tier(lead_7_cand, lead_7_ev, lead_7_ass, now=fixed_now)
    assert tier_7 == LeadTier.NEEDS_REVIEW
    assert any("Low category fit lacks supporting evidence" in r for r in scores_7.tier_reasons)

    # --- Lead 8: Needs Review - Category Fit Unknown ---
    lead_8_cand = _make_candidate(
        name="Nordic Living Concept",
        website="https://nordicliving.se",
        canonical_domain="nordicliving.se",
        website_verified=True,
    )
    lead_8_ev = [
        _make_evidence_item(source_type=EvidenceSourceType.OFFICIAL_SITE),
        _make_evidence_item(source_type=EvidenceSourceType.PRODUCT_PAGE, excerpt="Modern living."),
    ]
    lead_8_ass = _make_assessment_dict(category_label="unknown", aesthetic_label="high")
    scores_8, tier_8 = compute_scores_and_tier(lead_8_cand, lead_8_ev, lead_8_ass, now=fixed_now)
    assert tier_8 == LeadTier.NEEDS_REVIEW
    assert scores_8.overall is None
    assert any("Category fit unknown" in r for r in scores_8.tier_reasons)

    # --- Lead 9: Needs Review - Weak Evidence Quality (< 40) ---
    lead_9_cand = _make_candidate(
        name="Artisan Social Page",
        website="https://socialpage.example.com",
        canonical_domain="socialpage.example.com",
        website_verified=True,
        city=None,
        region=None,
        country=None,
    )
    old_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
    lead_9_ev = [
        _make_evidence_item(
            source_type=EvidenceSourceType.SOCIAL,
            url="https://socialpage.example.com/post/1",
            published_at=old_date,
            retrieved_at=old_date,
        )
    ]
    lead_9_ass = _make_assessment_dict(category_label="high")
    scores_9, tier_9 = compute_scores_and_tier(lead_9_cand, lead_9_ev, lead_9_ass, now=fixed_now)
    assert tier_9 == LeadTier.NEEDS_REVIEW
    assert scores_9.evidence_quality == 0.0
    assert any("below qualification threshold" in r for r in scores_9.tier_reasons)

    # --- Lead 10: Needs Review - AI Assessment Failure (None) ---
    lead_10_cand = _make_candidate(
        name="Unassessed Store",
        website="https://unassessedstore.com",
        canonical_domain="unassessedstore.com",
        website_verified=True,
    )
    lead_10_ev = [_make_evidence_item(source_type=EvidenceSourceType.OFFICIAL_SITE)]
    scores_10, tier_10 = compute_scores_and_tier(lead_10_cand, lead_10_ev, None, now=fixed_now)
    assert tier_10 == LeadTier.NEEDS_REVIEW
    assert scores_10.category_fit is None
    assert scores_10.aesthetic_fit is None
    assert scores_10.seller_compat is None
    assert any("Lead assessment is missing" in r for r in scores_10.tier_reasons)
