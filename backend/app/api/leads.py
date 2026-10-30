"""
Buyer Leads & Evidence API Router (/api/v1/leads).
Handles lead inspection, filtering, pagination (DECISION-D7), review status updates, and evidence lookup.
Enforces strict per-user isolation (owner_id == current_user.id).
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.schemas import (
    CulturalAffinity,
    ErrorCode,
    EvidenceItem,
    EvidenceSourceType,
    ContactScrapeResult,
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
from backend.app.core.errors import AppError
from backend.app.db.models import LeadEvidenceModel, LeadModel
from backend.research.contact_scraper import scrape_contact_email
from backend.app.db.session import get_db_session

logger = logging.getLogger(__name__)

leads_router = APIRouter(prefix="/leads", tags=["Leads"])


def _lead_model_to_schema(model: LeadModel) -> Lead:
    """Convert SQLAlchemy LeadModel to Contract v0.2 Lead schema."""
    location_obj = (
        LeadLocation.model_validate(model.location)
        if model.location and isinstance(model.location, dict)
        else None
    )
    scores_obj = (
        LeadScores.model_validate(model.scores)
        if model.scores and isinstance(model.scores, dict)
        else LeadScores()
    )
    assessment_obj = None
    if model.assessment and isinstance(model.assessment, dict):
        try:
            assessment_obj = LeadAssessment.model_validate(model.assessment)
        except Exception:
            try:
                assessment_obj = LeadAssessment(
                    category_fit=model.assessment.get("category_fit") or {"label": "unknown", "reasons": []},
                    aesthetic_fit=model.assessment.get("aesthetic_fit") or {"label": "unknown", "reasons": []},
                    seller_compat=model.assessment.get("seller_compat") or {"label": "unknown", "reasons": []},
                    summary=model.assessment.get("summary", ""),
                    unknowns=model.assessment.get("unknowns", []),
                )
            except Exception:
                assessment_obj = None
    cultural_obj = (
        CulturalAffinity.model_validate(model.cultural_affinity)
        if model.cultural_affinity and isinstance(model.cultural_affinity, dict)
        else None
    )

    tier_val = (
        LeadTier(model.tier)
        if model.tier in LeadTier._value2member_map_
        else LeadTier.NEEDS_REVIEW
    )
    review_val = (
        LeadReviewStatus(model.review_status)
        if model.review_status in LeadReviewStatus._value2member_map_
        else LeadReviewStatus.NEW
    )

    return Lead(
        id=model.id,
        owner_id=model.owner_id,
        run_id=model.run_id,
        product_id=model.product_id,
        name=model.name,
        website=model.website,
        canonical_domain=model.canonical_domain,
        contact_email=getattr(model, "contact_email", None),
        location=location_obj,
        retailer_type=model.retailer_type,
        website_verified=model.website_verified,
        website_checked_at=model.website_checked_at,
        tier=tier_val,
        scores=scores_obj,
        assessment=assessment_obj,
        cultural_affinity=cultural_obj,
        review_status=review_val,
        notes=model.notes,
        duplicate_of=model.duplicate_of,
        is_demo=model.is_demo,
        created_at=model.created_at,
    )


def _evidence_model_to_schema(model: LeadEvidenceModel) -> EvidenceItem:
    """Convert SQLAlchemy LeadEvidenceModel to Contract v0.2 EvidenceItem schema."""
    st = (
        EvidenceSourceType(model.source_type)
        if model.source_type in EvidenceSourceType._value2member_map_
        else EvidenceSourceType.OFFICIAL_SITE
    )
    prov = (
        ProvenanceTag(model.provenance)
        if model.provenance in ProvenanceTag._value2member_map_
        else ProvenanceTag.VERIFIED_FACT
    )

    return EvidenceItem(
        id=model.id,
        owner_id=model.owner_id,
        lead_id=model.lead_id,
        url=model.url,
        excerpt=model.excerpt,
        source_type=st,
        retrieved_at=model.retrieved_at,
        published_at=model.published_at,
        domain_matches_lead=model.domain_matches_lead,
        provenance=prov,
        is_demo=model.is_demo,
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
    session: AsyncSession = Depends(get_db_session),
) -> LeadPagedResponse:
    """
    List buyer leads with filtering, sorting, and pagination (DECISION-D7).
    Enforces strict user isolation: owner_id == user.id.
    """
    conditions = [LeadModel.owner_id == user.id]

    if run_id is not None:
        conditions.append(LeadModel.run_id == run_id)
    if product_id is not None:
        conditions.append(LeadModel.product_id == product_id)
    if review_status is not None:
        r_val = review_status.value if hasattr(review_status, "value") else str(review_status)
        conditions.append(LeadModel.review_status == r_val)
    if tier is not None:
        t_val = tier.value if hasattr(tier, "value") else str(tier)
        conditions.append(LeadModel.tier == t_val)
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        conditions.append(
            or_(
                LeadModel.name.ilike(search_term),
                LeadModel.canonical_domain.ilike(search_term),
            )
        )
    if location and location.strip():
        loc_term = f"%{location.strip()}%"
        conditions.append(cast(LeadModel.location, String).ilike(loc_term))

    if min_score is not None:
        # DECISION-D7: When min_score is set, leads with overall == null are excluded
        conditions.append(
            and_(
                LeadModel.scores["overall"].as_float().is_not(None),
                LeadModel.scores["overall"].as_float() >= min_score,
            )
        )

    # Count total matching records
    count_stmt = select(func.count(LeadModel.id)).where(*conditions)
    total = (await session.execute(count_stmt)).scalar_one()

    # Determine deterministic sort order
    if sort == "name":
        order_clauses = [LeadModel.name.asc(), LeadModel.id.asc()]
    elif sort == "newest":
        order_clauses = [LeadModel.created_at.desc(), LeadModel.id.asc()]
    else:  # score_desc (default)
        order_clauses = [
            LeadModel.scores["overall"].as_float().desc().nulls_last(),
            LeadModel.id.asc(),
        ]

    offset_val = (page - 1) * page_size
    query_stmt = (
        select(LeadModel)
        .where(*conditions)
        .order_by(*order_clauses)
        .offset(offset_val)
        .limit(page_size)
    )
    models = (await session.execute(query_stmt)).scalars().all()
    items = [_lead_model_to_schema(m) for m in models]

    return LeadPagedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@leads_router.get("/{id}", response_model=Lead)
async def get_lead(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Lead:
    """Retrieve details, scores, and assessment for a single lead owned by the user."""
    stmt = select(LeadModel).where(LeadModel.id == id, LeadModel.owner_id == user.id)
    lead = (await session.execute(stmt)).scalar_one_or_none()
    if not lead:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Lead with id '{id}' not found",
            status_code=404,
        )
    return _lead_model_to_schema(lead)


@leads_router.patch("/{id}", response_model=Lead)
async def update_lead(
    id: UUID,
    payload: UpdateLeadRequest,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Lead:
    """Update lead review status (new/saved/rejected/contacted) and notes."""
    stmt = select(LeadModel).where(LeadModel.id == id, LeadModel.owner_id == user.id)
    lead = (await session.execute(stmt)).scalar_one_or_none()
    if not lead:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Lead with id '{id}' not found",
            status_code=404,
        )

    if payload.review_status is not None:
        lead.review_status = (
            payload.review_status.value
            if hasattr(payload.review_status, "value")
            else str(payload.review_status)
        )
    if payload.notes is not None:
        lead.notes = payload.notes
    if payload.contact_email is not None:
        lead.contact_email = payload.contact_email.strip() or None

    lead.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(lead)
    return _lead_model_to_schema(lead)


@leads_router.post("/{id}/scrape-contact", response_model=ContactScrapeResult)
async def scrape_lead_contact(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ContactScrapeResult:
    """Scrape receiver wholesale/buyer contact email using live Tavily Search & Extract."""
    stmt = select(LeadModel).where(LeadModel.id == id, LeadModel.owner_id == user.id)
    lead = (await session.execute(stmt)).scalar_one_or_none()
    if not lead:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Lead with id '{id}' not found",
            status_code=404,
        )

    result = await scrape_contact_email(
        canonical_domain=lead.canonical_domain,
        website=lead.website,
    )

    scraped_email = result.get("email")
    if scraped_email:
        lead.contact_email = scraped_email
        lead.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(lead)

    return ContactScrapeResult(
        lead_id=lead.id,
        email=scraped_email or f"wholesale@{lead.canonical_domain}",
        source=result.get("source", "tavily_scraped"),
        source_url=result.get("source_url"),
        is_fallback=result.get("is_fallback", False),
        confidence=result.get("confidence", 0.9),
        all_candidates=result.get("all_candidates", []),
    )


@leads_router.get("/{id}/evidence", response_model=list[EvidenceItem])
async def get_lead_evidence(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[EvidenceItem]:
    """Retrieve verified evidence items for a lead owned by the user."""
    lead_stmt = select(LeadModel).where(LeadModel.id == id, LeadModel.owner_id == user.id)
    lead = (await session.execute(lead_stmt)).scalar_one_or_none()
    if not lead:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Lead with id '{id}' not found",
            status_code=404,
        )

    ev_stmt = (
        select(LeadEvidenceModel)
        .where(LeadEvidenceModel.lead_id == id, LeadEvidenceModel.owner_id == user.id)
        .order_by(LeadEvidenceModel.created_at.asc())
    )
    models = (await session.execute(ev_stmt)).scalars().all()
    return [_evidence_model_to_schema(e) for e in models]
