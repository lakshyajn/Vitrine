"""
Outreach Studio API Router (/api/v1/outreach-drafts & /api/v1/leads/{id}/outreach-drafts).
Handles grounded B2B draft generation (Task D), editing, versioning, manual status tracking,
and atomic lead review_status updates (DECISION-D11).
Enforces strict per-user isolation (owner_id == current_user.id) with 404 on unowned records.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.schemas import (
    ErrorCode,
    FactUsed,
    OutreachDraft,
    OutreachDraftStatus,
    UpdateOutreachDraftRequest,
)
from backend.ai.service import get_ai_service
from backend.app.api.leads import _evidence_model_to_schema, _lead_model_to_schema
from backend.app.api.products import _product_model_to_schema
from backend.app.auth.deps import CurrentUser, current_user
from backend.app.core.errors import AppError
from backend.app.core.rate_limit import outreach_drafts_rate_limiter
from backend.app.db.models import (
    LeadEvidenceModel,
    LeadModel,
    OutreachDraftModel,
    ProductModel,
)
from backend.app.db.session import get_db_session

logger = logging.getLogger(__name__)

outreach_router = APIRouter(prefix="/outreach-drafts", tags=["Outreach"])
lead_outreach_router = APIRouter(prefix="/leads", tags=["Outreach"])


def _draft_model_to_schema(model: OutreachDraftModel) -> OutreachDraft:
    """Convert SQLAlchemy OutreachDraftModel to Contract v0.2 OutreachDraft schema."""
    facts = [
        FactUsed(
            fact_id=f.get("fact_id", ""),
            text=f.get("text", ""),
            source_url=f.get("source_url"),
        )
        for f in (model.facts_used or [])
        if isinstance(f, dict)
    ]
    status_val = (
        OutreachDraftStatus(model.status)
        if model.status in OutreachDraftStatus._value2member_map_
        else OutreachDraftStatus.DRAFT
    )
    return OutreachDraft(
        id=model.id,
        owner_id=model.owner_id,
        lead_id=model.lead_id,
        product_id=model.product_id,
        version=model.version,
        subject=model.subject,
        body=model.body,
        facts_used=facts,
        warnings=list(model.warnings or []),
        status=status_val,
        followup_notes=model.followup_notes,
        parent_draft_id=model.parent_draft_id,
        is_demo=model.is_demo,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@outreach_router.get("", response_model=list[OutreachDraft])
async def list_outreach_drafts(
    status: OutreachDraftStatus | None = None,
    product_id: UUID | None = None,
    lead_id: UUID | None = None,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[OutreachDraft]:
    """List outreach drafts across leads with optional filters (DECISION-D17)."""
    conditions = [OutreachDraftModel.owner_id == user.id]
    if status is not None:
        status_str = status.value if hasattr(status, "value") else str(status)
        conditions.append(OutreachDraftModel.status == status_str)
    if product_id is not None:
        conditions.append(OutreachDraftModel.product_id == product_id)
    if lead_id is not None:
        conditions.append(OutreachDraftModel.lead_id == lead_id)

    stmt = (
        select(OutreachDraftModel)
        .where(*conditions)
        .order_by(OutreachDraftModel.updated_at.desc(), OutreachDraftModel.id.desc())
    )
    drafts = (await session.execute(stmt)).scalars().all()
    return [_draft_model_to_schema(d) for d in drafts]


@lead_outreach_router.post("/{id}/outreach-drafts", response_model=OutreachDraft, status_code=201)
async def generate_outreach_draft(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(outreach_drafts_rate_limiter),
) -> OutreachDraft:
    """Generate a new grounded outreach draft for a lead (AI Task D)."""
    # 1. Fetch lead
    lead_stmt = select(LeadModel).where(
        LeadModel.id == id,
        LeadModel.owner_id == user.id,
    )
    lead_model = (await session.execute(lead_stmt)).scalar_one_or_none()
    if not lead_model:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Lead with id '{id}' not found",
            status_code=404,
        )

    # 2. Fetch associated product
    prod_stmt = select(ProductModel).where(
        ProductModel.id == lead_model.product_id,
        ProductModel.owner_id == user.id,
    )
    product_model = (await session.execute(prod_stmt)).scalar_one_or_none()
    if not product_model:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Associated product with id '{lead_model.product_id}' not found",
            status_code=404,
        )

    # 3. Fetch evidence
    ev_stmt = select(LeadEvidenceModel).where(
        LeadEvidenceModel.lead_id == id,
        LeadEvidenceModel.owner_id == user.id,
    )
    evidence_models = (await session.execute(ev_stmt)).scalars().all()

    # 4. Fetch existing drafts for latest draft and version number
    drafts_stmt = (
        select(OutreachDraftModel)
        .where(
            OutreachDraftModel.lead_id == id,
            OutreachDraftModel.owner_id == user.id,
        )
        .order_by(OutreachDraftModel.version.desc())
    )
    existing_drafts = (await session.execute(drafts_stmt)).scalars().all()
    latest_draft_model = existing_drafts[0] if existing_drafts else None
    next_version = (latest_draft_model.version + 1) if latest_draft_model else 1

    # 5. Convert to schemas
    product_schema = _product_model_to_schema(product_model)
    lead_schema = _lead_model_to_schema(lead_model)
    evidence_schemas = [_evidence_model_to_schema(em) for em in evidence_models]
    latest_draft_schema = _draft_model_to_schema(latest_draft_model) if latest_draft_model else None

    # 6. Call AI service
    ai_service = get_ai_service()
    generated = await ai_service.draft_outreach(
        product=product_schema,
        lead=lead_schema,
        evidence=evidence_schemas,
        previous=latest_draft_schema,
    )

    # 7. Persist new row
    facts_data = [
        f.model_dump(mode="json") if hasattr(f, "model_dump") else dict(f)
        for f in (generated.facts_used or [])
    ]
    now = datetime.now(timezone.utc)
    new_draft = OutreachDraftModel(
        id=uuid4(),
        owner_id=user.id,
        lead_id=lead_model.id,
        product_id=product_model.id,
        version=next_version,
        subject=generated.subject,
        body=generated.body,
        facts_used=facts_data,
        warnings=list(generated.warnings or []),
        status="draft",
        followup_notes=None,
        parent_draft_id=latest_draft_model.id if latest_draft_model else None,
        is_demo=getattr(generated, "is_demo", False),
        created_at=now,
        updated_at=now,
    )
    session.add(new_draft)
    await session.commit()
    await session.refresh(new_draft)
    return _draft_model_to_schema(new_draft)


@lead_outreach_router.get("/{id}/outreach-drafts", response_model=list[OutreachDraft])
async def get_lead_outreach_drafts(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[OutreachDraft]:
    """Retrieve all versioned drafts for a lead ordered by version desc."""
    lead_stmt = select(LeadModel).where(
        LeadModel.id == id,
        LeadModel.owner_id == user.id,
    )
    lead_model = (await session.execute(lead_stmt)).scalar_one_or_none()
    if not lead_model:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Lead with id '{id}' not found",
            status_code=404,
        )

    stmt = (
        select(OutreachDraftModel)
        .where(
            OutreachDraftModel.lead_id == id,
            OutreachDraftModel.owner_id == user.id,
        )
        .order_by(OutreachDraftModel.version.desc())
    )
    drafts = (await session.execute(stmt)).scalars().all()
    return [_draft_model_to_schema(d) for d in drafts]


@outreach_router.patch("/{id}", response_model=OutreachDraft)
async def update_outreach_draft(
    id: UUID,
    payload: UpdateOutreachDraftRequest,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    """
    Update subject, body, manual status, or followup notes of an outreach draft.
    Atomic rule (DECISION-D11): when status is set to contacted, atomically update parent lead review_status.
    """
    draft_stmt = select(OutreachDraftModel).where(
        OutreachDraftModel.id == id,
        OutreachDraftModel.owner_id == user.id,
    )
    draft = (await session.execute(draft_stmt)).scalar_one_or_none()
    if not draft:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Outreach draft with id '{id}' not found",
            status_code=404,
        )

    if payload.subject is not None:
        draft.subject = payload.subject
    if payload.body is not None:
        draft.body = payload.body
    if payload.followup_notes is not None:
        draft.followup_notes = payload.followup_notes
    if payload.status is not None:
        status_str = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
        draft.status = status_str

        # DECISION-D11: Atomically update parent lead.review_status to contacted
        if status_str == "contacted":
            lead_stmt = select(LeadModel).where(
                LeadModel.id == draft.lead_id,
                LeadModel.owner_id == user.id,
            )
            lead = (await session.execute(lead_stmt)).scalar_one_or_none()
            if lead:
                lead.review_status = "contacted"

    draft.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(draft)
    return _draft_model_to_schema(draft)


@outreach_router.post("/{id}/regenerate", response_model=OutreachDraft, status_code=201)
async def regenerate_outreach_draft(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> OutreachDraft:
    """
    Regenerate a new draft version from an existing draft.
    Inserts a new row with version = max_version + 1 and parent_draft_id = id (never overwrites).
    """
    # 1. Fetch parent draft
    draft_stmt = select(OutreachDraftModel).where(
        OutreachDraftModel.id == id,
        OutreachDraftModel.owner_id == user.id,
    )
    parent_draft = (await session.execute(draft_stmt)).scalar_one_or_none()
    if not parent_draft:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Outreach draft with id '{id}' not found",
            status_code=404,
        )

    # 2. Fetch associated lead
    lead_stmt = select(LeadModel).where(
        LeadModel.id == parent_draft.lead_id,
        LeadModel.owner_id == user.id,
    )
    lead_model = (await session.execute(lead_stmt)).scalar_one_or_none()
    if not lead_model:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Lead with id '{parent_draft.lead_id}' not found",
            status_code=404,
        )

    # 3. Fetch associated product
    prod_stmt = select(ProductModel).where(
        ProductModel.id == parent_draft.product_id,
        ProductModel.owner_id == user.id,
    )
    product_model = (await session.execute(prod_stmt)).scalar_one_or_none()
    if not product_model:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Associated product with id '{parent_draft.product_id}' not found",
            status_code=404,
        )

    # 4. Fetch evidence
    ev_stmt = select(LeadEvidenceModel).where(
        LeadEvidenceModel.lead_id == parent_draft.lead_id,
        LeadEvidenceModel.owner_id == user.id,
    )
    evidence_models = (await session.execute(ev_stmt)).scalars().all()

    # 5. Determine next version number (max(version) + 1 for this lead)
    version_stmt = select(func.coalesce(func.max(OutreachDraftModel.version), 0)).where(
        OutreachDraftModel.lead_id == parent_draft.lead_id,
        OutreachDraftModel.owner_id == user.id,
    )
    max_ver = (await session.execute(version_stmt)).scalar_one()
    next_version = max_ver + 1

    # 6. Convert to schemas
    product_schema = _product_model_to_schema(product_model)
    lead_schema = _lead_model_to_schema(lead_model)
    evidence_schemas = [_evidence_model_to_schema(em) for em in evidence_models]
    parent_draft_schema = _draft_model_to_schema(parent_draft)

    # 7. Call AI service
    ai_service = get_ai_service()
    generated = await ai_service.draft_outreach(
        product=product_schema,
        lead=lead_schema,
        evidence=evidence_schemas,
        previous=parent_draft_schema,
    )

    # 8. Insert new version row
    facts_data = [
        f.model_dump(mode="json") if hasattr(f, "model_dump") else dict(f)
        for f in (generated.facts_used or [])
    ]
    now = datetime.now(timezone.utc)
    new_draft = OutreachDraftModel(
        id=uuid4(),
        owner_id=user.id,
        lead_id=parent_draft.lead_id,
        product_id=parent_draft.product_id,
        version=next_version,
        subject=generated.subject,
        body=generated.body,
        facts_used=facts_data,
        warnings=list(generated.warnings or []),
        status="draft",
        followup_notes=None,
        parent_draft_id=parent_draft.id,
        is_demo=getattr(generated, "is_demo", False),
        created_at=now,
        updated_at=now,
    )
    session.add(new_draft)
    await session.commit()
    await session.refresh(new_draft)
    return _draft_model_to_schema(new_draft)
