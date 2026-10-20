"""
Buyer Leads & Evidence API Router (/api/v1/leads).
Handles lead inspection, pagination (D7), review status updates, and evidence lookup.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Query

from contracts.schemas import (
    CulturalAffinity,
    DimensionAssessment,
    DimensionLabel,
    EvidenceItem,
    EvidenceSourceType,
    Lead,
    LeadAssessment,
    LeadLocation,
    LeadPagedResponse,
    LeadReviewStatus,
    LeadScores,
    LeadTier,
    ProvenanceTag,
    UpdateLeadRequest,
)
from backend.app.auth.deps import CurrentUser, current_user

leads_router = APIRouter(prefix="/leads", tags=["Leads"])


def _stub_evidence(lead_id: UUID, user_id: UUID) -> list[EvidenceItem]:
    return [
        EvidenceItem(
            id=uuid4(),
            owner_id=user_id,
            lead_id=lead_id,
            url="https://atelierlivingdemo.com/about",
            excerpt="Independent design store featuring handcrafted botanical textiles, table linens, and artisan ceramics.",
            source_type=EvidenceSourceType.OFFICIAL_SITE,
            domain_matches_lead=True,
            provenance=ProvenanceTag.VERIFIED_FACT,
            is_demo=True,
        ),
        EvidenceItem(
            id=uuid4(),
            owner_id=user_id,
            lead_id=lead_id,
            url="https://atelierlivingdemo.com/collections/table-linens",
            excerpt="Hand block-printed cotton table runners with natural terracotta and indigo botanical motifs.",
            source_type=EvidenceSourceType.PRODUCT_PAGE,
            domain_matches_lead=True,
            provenance=ProvenanceTag.VERIFIED_FACT,
            is_demo=True,
        ),
    ]


def _stub_lead(user_id: UUID, lead_id: UUID | None = None) -> Lead:
    lid = lead_id or uuid4()
    run_id = uuid4()
    product_id = uuid4()
    evidence_items = _stub_evidence(lid, user_id)
    ev_ids = [e.id for e in evidence_items]

    return Lead(
        id=lid,
        owner_id=user_id,
        run_id=run_id,
        product_id=product_id,
        name="Atelier Living & Design",
        website="https://atelierlivingdemo.com",
        canonical_domain="atelierlivingdemo.com",
        location=LeadLocation(city="Amsterdam", region="North Holland", country="Netherlands"),
        retailer_type="Independent Home Decor Boutique",
        website_verified=True,
        tier=LeadTier.QUALIFIED,
        scores=LeadScores(
            category_fit=100.0,
            aesthetic_fit=100.0,
            evidence_quality=80.0,
            seller_compat=60.0,
            overall=88.0,
            completeness=1.0,
            tier_reasons=[
                "Website verified via HTTP 200",
                "Official site and product page evidence items present",
                "Category fit is high",
                "Evidence quality score >= 40",
            ],
        ),
        assessment=LeadAssessment(
            category_fit=DimensionAssessment(
                label=DimensionLabel.HIGH,
                reasons=["Carries curated table linens and handcrafted home decor."],
                evidence_ids=ev_ids[:1],
            ),
            aesthetic_fit=DimensionAssessment(
                label=DimensionLabel.HIGH,
                reasons=["Visual identity matches botanical motifs and natural dyes."],
                evidence_ids=ev_ids[1:],
            ),
            seller_compat=DimensionAssessment(
                label=DimensionLabel.MEDIUM,
                reasons=["Price points align with mid-premium wholesale pricing."],
                evidence_ids=ev_ids[:1],
            ),
            summary="Exceptional fit for block-printed table runners.",
            unknowns=["Direct buyer contact email not listed publicly"],
            model_id="fixture-stub",
        ),
        cultural_affinity=CulturalAffinity(
            provider="mock",
            is_demo=True,
            signals=[{"type": "aesthetic_overlap", "text": "High alignment with European artisan textile trends"}],
        ),
        review_status=LeadReviewStatus.NEW,
        notes="High priority target for initial outreach.",
        is_demo=True,
    )


@leads_router.get("", response_model=LeadPagedResponse)
async def list_leads(
    run_id: UUID | None = None,
    product_id: UUID | None = None,
    review_status: LeadReviewStatus | None = None,
    tier: LeadTier | None = None,
    q: str | None = None,
    location: str | None = None,
    min_score: float | None = None,
    sort: Literal["score_desc", "name", "newest"] = "score_desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(current_user),
) -> LeadPagedResponse:
    """List buyer leads with filtering, sorting, and pagination (DECISION-D7)."""
    lead = _stub_lead(user.id)
    if run_id:
        lead.run_id = run_id
    if product_id:
        lead.product_id = product_id
    if review_status:
        lead.review_status = review_status
    if tier:
        lead.tier = tier

    return LeadPagedResponse(
        items=[lead],
        total=1,
        page=page,
        page_size=page_size,
    )


@leads_router.get("/{id}", response_model=Lead)
async def get_lead(
    id: UUID,
    user: CurrentUser = Depends(current_user),
) -> Lead:
    """Retrieve details, scores, and assessment for a single lead."""
    return _stub_lead(user.id, lead_id=id)


@leads_router.patch("/{id}", response_model=Lead)
async def update_lead(
    id: UUID,
    payload: UpdateLeadRequest,
    user: CurrentUser = Depends(current_user),
) -> Lead:
    """Update lead review status (new/saved/rejected/contacted) and notes."""
    lead = _stub_lead(user.id, lead_id=id)
    if payload.review_status is not None:
        lead.review_status = payload.review_status
    if payload.notes is not None:
        lead.notes = payload.notes
    return lead


@leads_router.get("/{id}/evidence", response_model=list[EvidenceItem])
async def get_lead_evidence(
    id: UUID,
    user: CurrentUser = Depends(current_user),
) -> list[EvidenceItem]:
    """Retrieve verified evidence items for a lead."""
    return _stub_evidence(id, user.id)
