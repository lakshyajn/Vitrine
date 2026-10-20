"""
Outreach Studio API Router (/api/v1/outreach-drafts & /api/v1/leads/{id}/outreach-drafts).
Handles grounded B2B draft generation (Task D), editing, versioning, and manual status tracking.
"""

from __future__ import annotations

from uuid import UUID, uuid4
from fastapi import APIRouter, Depends

from contracts.schemas import (
    FactUsed,
    OutreachDraft,
    OutreachDraftStatus,
    UpdateOutreachDraftRequest,
)
from backend.app.auth.deps import CurrentUser, current_user

outreach_router = APIRouter(prefix="/outreach-drafts", tags=["Outreach"])
lead_outreach_router = APIRouter(prefix="/leads", tags=["Outreach"])


def _stub_draft(
    user_id: UUID,
    draft_id: UUID | None = None,
    lead_id: UUID | None = None,
    version: int = 1,
) -> OutreachDraft:
    lid = lead_id or uuid4()
    did = draft_id or uuid4()
    pid = uuid4()

    return OutreachDraft(
        id=did,
        owner_id=user_id,
        lead_id=lid,
        product_id=pid,
        version=version,
        subject="Wholesale inquiry: Hand block-printed botanical table runners for Atelier Living",
        body=(
            "Dear Atelier Living team,\n\n"
            "We admire your thoughtfully curated homeware collection in Amsterdam, particularly your appreciation for "
            "independent artisan makers. We are a small block-printing workshop crafting 100% cotton table runners and cushion "
            "covers using natural botanical motifs and traditional earthy vegetable dyes.\n\n"
            "Given your focus on artisanal table linens, we would love to share our wholesale line sheet and sample swatches with you.\n\n"
            "Warm regards,\n"
            "Sample Seller Team"
        ),
        facts_used=[
            FactUsed(
                fact_id="fact-1",
                text="Artisan workshop crafting 100% cotton table runners using natural botanical motifs",
                source_url=None,
            ),
            FactUsed(
                fact_id="fact-2",
                text="Atelier Living stocks independent artisanal textiles and ceramics in Amsterdam",
                source_url="https://atelierlivingdemo.com/about",
            ),
        ],
        warnings=[],
        status=OutreachDraftStatus.DRAFT,
        followup_notes="Check seasonal line sheet availability before following up.",
        is_demo=True,
    )


@outreach_router.get("", response_model=list[OutreachDraft])
async def list_outreach_drafts(
    status: OutreachDraftStatus | None = None,
    product_id: UUID | None = None,
    lead_id: UUID | None = None,
    user: CurrentUser = Depends(current_user),
) -> list[OutreachDraft]:
    """List outreach drafts across leads (DECISION-D17)."""
    draft = _stub_draft(user.id, lead_id=lead_id)
    if status:
        draft.status = status
    if product_id:
        draft.product_id = product_id
    return [draft]


@lead_outreach_router.post("/{id}/outreach-drafts", response_model=OutreachDraft, status_code=201)
async def generate_outreach_draft(
    id: UUID,
    user: CurrentUser = Depends(current_user),
) -> OutreachDraft:
    """Generate a new grounded outreach draft for a lead (AI Task D)."""
    return _stub_draft(user.id, lead_id=id, version=1)


@lead_outreach_router.get("/{id}/outreach-drafts", response_model=list[OutreachDraft])
async def get_lead_outreach_drafts(
    id: UUID,
    user: CurrentUser = Depends(current_user),
) -> list[OutreachDraft]:
    """Retrieve all versioned drafts for a lead."""
    return [_stub_draft(user.id, lead_id=id, version=1)]


@outreach_router.patch("/{id}", response_model=OutreachDraft)
async def update_outreach_draft(
    id: UUID,
    payload: UpdateOutreachDraftRequest,
    user: CurrentUser = Depends(current_user),
) -> OutreachDraft:
    """Update subject, body, manual status, or followup notes of an outreach draft."""
    draft = _stub_draft(user.id, draft_id=id)
    if payload.subject is not None:
        draft.subject = payload.subject
    if payload.body is not None:
        draft.body = payload.body
    if payload.status is not None:
        draft.status = payload.status
    if payload.followup_notes is not None:
        draft.followup_notes = payload.followup_notes
    return draft


@outreach_router.post("/{id}/regenerate", response_model=OutreachDraft, status_code=201)
async def regenerate_outreach_draft(
    id: UUID,
    user: CurrentUser = Depends(current_user),
) -> OutreachDraft:
    """Regenerate a new draft version from an existing draft (inserts new version row)."""
    parent = _stub_draft(user.id, draft_id=id)
    new_version = parent.version + 1
    new_draft = _stub_draft(user.id, lead_id=parent.lead_id, version=new_version)
    new_draft.parent_draft_id = parent.id
    return new_draft
