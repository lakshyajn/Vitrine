"""
Research Runs & Anchors API Router (/api/v1/research-runs & /api/v1/taste-anchors).
Handles run state machine, anchor proposals, custom anchors (D3), and confirmation (D4).
Strict per-user isolation with real DB persistence.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.schemas import (
    ConfirmAnchorsRequest,
    CreateAnchorRequest,
    CreateResearchRunRequest,
    ErrorCode,
    HypothesisSignal,
    MarketHypothesis,
    MarketHypothesisStatus,
    ProviderModes,
    ResearchPlan,
    ResearchRun,
    ResearchRunActionResponse,
    ResearchRunInputs,
    ResearchRunStage,
    ResearchRunStatus,
    RunError,
    TasteAnchor,
    TasteAnchorSource,
    TasteAnchorStatus,
    UpdateAnchorRequest,
)
from backend.app.auth.deps import CurrentUser, current_user
from backend.app.core.config import get_settings
from backend.app.core.errors import AppError
from backend.app.core.rate_limit import research_runs_rate_limiter
from backend.app.db.models import (
    MarketHypothesisModel,
    ProductModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.session import get_db_session
from backend.app.jobs.runner import run_research_run_phase1, run_research_run_phase2

logger = logging.getLogger(__name__)

runs_router = APIRouter(prefix="/research-runs", tags=["Research Runs"])
taste_anchors_router = APIRouter(prefix="/taste-anchors", tags=["Taste Anchors"])


def snapshot_provider_modes() -> dict[str, str]:
    """Snapshot provider modes (ai, search, taste as live or mock per DECISION-D1)."""
    settings = get_settings()
    return {
        "ai": "live" if settings.is_ai_live else "mock",
        "search": "live" if settings.is_search_live else "mock",
        "taste": "live" if settings.is_taste_live else "mock",
    }


def _run_model_to_schema(model: ResearchRunModel) -> ResearchRun:
    inputs_obj = (
        ResearchRunInputs.model_validate(model.inputs)
        if model.inputs
        else ResearchRunInputs()
    )
    plan_obj = (
        ResearchPlan.model_validate(model.plan)
        if model.plan
        else None
    )
    error_obj = (
        RunError.model_validate(model.error)
        if model.error
        else None
    )
    modes_obj = (
        ProviderModes.model_validate(model.provider_modes)
        if model.provider_modes
        else ProviderModes()
    )
    return ResearchRun(
        id=model.id,
        owner_id=model.owner_id,
        product_id=model.product_id,
        status=ResearchRunStatus(model.status),
        stage=ResearchRunStage(model.stage),
        inputs=inputs_obj,
        plan=plan_obj,
        error=error_obj,
        provider_modes=modes_obj,
        started_at=model.started_at,
        finished_at=model.finished_at,
        heartbeat_at=model.heartbeat_at,
        created_at=model.created_at,
    )


def _anchor_model_to_schema(model: TasteAnchorModel) -> TasteAnchor:
    return TasteAnchor(
        id=model.id,
        owner_id=model.owner_id,
        run_id=model.run_id,
        label=model.label,
        entity_type=model.entity_type,
        external_id=model.external_id,
        source=TasteAnchorSource(model.source),
        status=TasteAnchorStatus(model.status),
        rationale=model.rationale,
        metadata=dict(model.metadata_json or {}),
        is_demo=model.is_demo,
    )


def _hypothesis_model_to_schema(model: MarketHypothesisModel) -> MarketHypothesis:
    signals_list = [
        HypothesisSignal.model_validate(s)
        for s in (model.signals or [])
    ]
    return MarketHypothesis(
        id=model.id,
        owner_id=model.owner_id,
        run_id=model.run_id,
        title=model.title,
        rationale=model.rationale,
        region_hint=model.region_hint,
        signals=signals_list,
        status=MarketHypothesisStatus(model.status),
    )


@runs_router.post("", response_model=ResearchRunActionResponse, status_code=201)
async def create_research_run(
    payload: CreateResearchRunRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
    _rate_limit: None = Depends(research_runs_rate_limiter),
) -> ResearchRunActionResponse:
    """
    Create and queue a new research run.
    Verifies product_id belongs to caller.
    Supports optional Idempotency-Key header to prevent duplicate runs.
    Snapshots provider_modes (ai, search, taste as live or mock).
    Triggers Phase 1 of async runner.
    """
    # 1. Verify product belongs to caller
    prod_stmt = select(ProductModel).where(
        ProductModel.id == payload.product_id,
        ProductModel.owner_id == user.id,
    )
    product = (await session.execute(prod_stmt)).scalar_one_or_none()
    if product is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Product with id '{payload.product_id}' not found",
            status_code=404,
        )

    # 2. Check idempotency key if provided
    clean_idem = idempotency_key.strip() if idempotency_key else None
    if clean_idem:
        idem_stmt = select(ResearchRunModel).where(
            ResearchRunModel.owner_id == user.id,
            ResearchRunModel.idempotency_key == clean_idem,
        )
        existing = (await session.execute(idem_stmt)).scalar_one_or_none()
        if existing:
            return ResearchRunActionResponse(
                id=existing.id,
                status=ResearchRunStatus(existing.status),
            )

    # 3. Insert new research run
    run_id = uuid4()
    modes = snapshot_provider_modes()
    inputs_dict = payload.inputs.model_dump() if payload.inputs else {}

    new_run = ResearchRunModel(
        id=run_id,
        owner_id=user.id,
        product_id=payload.product_id,
        status="queued",
        stage="planning",
        inputs=inputs_dict,
        provider_modes=modes,
        idempotency_key=clean_idem,
        created_at=datetime.now(timezone.utc),
        heartbeat_at=datetime.now(timezone.utc),
    )
    session.add(new_run)
    await session.commit()

    # 4. Trigger Phase 1 of the async background runner
    asyncio.create_task(run_research_run_phase1(run_id))

    return ResearchRunActionResponse(id=run_id, status=ResearchRunStatus.QUEUED)


@runs_router.get("", response_model=list[ResearchRun])
async def list_research_runs(
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[ResearchRun]:
    """List all research runs belonging to the authenticated seller."""
    stmt = (
        select(ResearchRunModel)
        .where(ResearchRunModel.owner_id == user.id)
        .order_by(ResearchRunModel.created_at.desc(), ResearchRunModel.id.desc())
    )
    result = await session.execute(stmt)
    runs = result.scalars().all()
    return [_run_model_to_schema(r) for r in runs]


@runs_router.get("/{id}", response_model=ResearchRun)
async def get_research_run(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchRun:
    """Retrieve details, stage, and plan of a research run."""
    stmt = select(ResearchRunModel).where(
        ResearchRunModel.id == id,
        ResearchRunModel.owner_id == user.id,
    )
    run = (await session.execute(stmt)).scalar_one_or_none()
    if run is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Research run with id '{id}' not found",
            status_code=404,
        )
    return _run_model_to_schema(run)


@runs_router.post("/{id}/rerun", response_model=ResearchRunActionResponse)
async def rerun_research_run(
    id: UUID,
    payload: CreateResearchRunRequest | None = None,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchRunActionResponse:
    """Trigger a rerun for an existing research run, copying inputs and merging new inputs."""
    stmt = select(ResearchRunModel).where(
        ResearchRunModel.id == id,
        ResearchRunModel.owner_id == user.id,
    )
    old_run = (await session.execute(stmt)).scalar_one_or_none()
    if old_run is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Research run with id '{id}' not found",
            status_code=404,
        )

    # Merge inputs from old run and request body
    merged_inputs = dict(old_run.inputs or {})
    if payload and payload.inputs:
        new_inputs = payload.inputs.model_dump(exclude_unset=True)
        merged_inputs.update({k: v for k, v in new_inputs.items() if v is not None})

    new_run_id = uuid4()
    modes = snapshot_provider_modes()

    new_run = ResearchRunModel(
        id=new_run_id,
        owner_id=user.id,
        product_id=old_run.product_id,
        status="queued",
        stage="planning",
        inputs=merged_inputs,
        provider_modes=modes,
        created_at=datetime.now(timezone.utc),
        heartbeat_at=datetime.now(timezone.utc),
    )
    session.add(new_run)
    await session.commit()

    asyncio.create_task(run_research_run_phase1(new_run_id))

    return ResearchRunActionResponse(id=new_run_id, status=ResearchRunStatus.QUEUED)


@runs_router.get("/{id}/anchors", response_model=list[TasteAnchor])
async def get_run_anchors(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[TasteAnchor]:
    """Retrieve proposed, candidate, and confirmed anchors for a run."""
    # Verify parent run belongs to caller
    run_stmt = select(ResearchRunModel).where(
        ResearchRunModel.id == id,
        ResearchRunModel.owner_id == user.id,
    )
    run = (await session.execute(run_stmt)).scalar_one_or_none()
    if run is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Research run with id '{id}' not found",
            status_code=404,
        )

    stmt = (
        select(TasteAnchorModel)
        .where(
            TasteAnchorModel.run_id == id,
            TasteAnchorModel.owner_id == user.id,
        )
        .order_by(TasteAnchorModel.created_at.asc(), TasteAnchorModel.id.asc())
    )
    result = await session.execute(stmt)
    anchors = result.scalars().all()
    return [_anchor_model_to_schema(a) for a in anchors]


@runs_router.post("/{id}/anchors", response_model=TasteAnchor, status_code=201)
async def create_custom_anchor(
    id: UUID,
    payload: CreateAnchorRequest,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> TasteAnchor:
    """Add a custom user-defined taste anchor (DECISION-D3)."""
    # Verify parent run belongs to caller
    run_stmt = select(ResearchRunModel).where(
        ResearchRunModel.id == id,
        ResearchRunModel.owner_id == user.id,
    )
    run = (await session.execute(run_stmt)).scalar_one_or_none()
    if run is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Research run with id '{id}' not found",
            status_code=404,
        )

    anchor_id = uuid4()
    anchor = TasteAnchorModel(
        id=anchor_id,
        owner_id=user.id,
        run_id=id,
        label=payload.label,
        entity_type=payload.entity_type or "brand",
        external_id=None,
        source="user_added",
        status="confirmed",
        rationale=payload.rationale,
        metadata_json={},
        is_demo=False,
        created_at=datetime.now(timezone.utc),
    )
    session.add(anchor)
    await session.commit()
    await session.refresh(anchor)

    return _anchor_model_to_schema(anchor)


@taste_anchors_router.patch("/{id}", response_model=TasteAnchor)
async def update_taste_anchor(
    id: UUID,
    payload: UpdateAnchorRequest,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> TasteAnchor:
    """Confirm, reject, or edit an anchor. Verifies parent run ownership."""
    stmt = select(TasteAnchorModel).where(
        TasteAnchorModel.id == id,
        TasteAnchorModel.owner_id == user.id,
    )
    anchor = (await session.execute(stmt)).scalar_one_or_none()
    if anchor is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Taste anchor with id '{id}' not found",
            status_code=404,
        )

    # Verify parent run belongs to caller
    run_stmt = select(ResearchRunModel).where(
        ResearchRunModel.id == anchor.run_id,
        ResearchRunModel.owner_id == user.id,
    )
    run = (await session.execute(run_stmt)).scalar_one_or_none()
    if run is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Taste anchor with id '{id}' not found",
            status_code=404,
        )

    if payload.status is not None:
        anchor.status = payload.status.value if hasattr(payload.status, "value") else str(payload.status)
    if payload.label is not None:
        anchor.label = payload.label
    if payload.entity_type is not None:
        anchor.entity_type = payload.entity_type
    if payload.rationale is not None:
        anchor.rationale = payload.rationale

    await session.commit()
    await session.refresh(anchor)
    return _anchor_model_to_schema(anchor)


@runs_router.post("/{id}/confirm-anchors", response_model=ResearchRun)
async def confirm_run_anchors(
    id: UUID,
    payload: ConfirmAnchorsRequest = ConfirmAnchorsRequest(),
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ResearchRun:
    """
    Resume run after reviewing anchors (DECISION-D4).
    Requires run to be in awaiting_review state.
    Requires >= 1 confirmed anchor unless proceed_without_anchors is true (returns 422 on failure).
    Stores confirmed anchor_ids in run.inputs and transitions run to queued (stage: discovery).
    Triggers Phase 2 of the runner.
    """
    # 1. Verify run belongs to caller
    run_stmt = select(ResearchRunModel).where(
        ResearchRunModel.id == id,
        ResearchRunModel.owner_id == user.id,
    )
    run = (await session.execute(run_stmt)).scalar_one_or_none()
    if run is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Research run with id '{id}' not found",
            status_code=404,
        )

    # 2. Must be in awaiting_review or completed (allows confirming more anchors & expanding leads)
    if run.status not in ("awaiting_review", "completed"):
        raise AppError(
            code=ErrorCode.CONFLICT,
            message=f"Run '{id}' is not in awaiting_review or completed status (currently '{run.status}')",
            status_code=409,
        )

    # 3. Query confirmed anchors
    confirmed_stmt = select(TasteAnchorModel).where(
        TasteAnchorModel.run_id == id,
        TasteAnchorModel.owner_id == user.id,
        TasteAnchorModel.status == "confirmed",
    )
    confirmed_anchors = (await session.execute(confirmed_stmt)).scalars().all()

    # 4. Require >= 1 confirmed anchor unless proceed_without_anchors is true
    if len(confirmed_anchors) == 0 and not payload.proceed_without_anchors:
        raise AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="At least one confirmed anchor is required unless proceed_without_anchors is true",
            status_code=422,
            details={
                "field": "anchors",
                "reason": "At least one confirmed anchor is required to proceed",
                "anchors": "At least one confirmed anchor is required to proceed",
            },
        )

    # 5. Store confirmed anchor_ids in run.inputs
    inputs_data = dict(run.inputs or {})
    inputs_data["anchor_ids"] = [str(a.id) for a in confirmed_anchors]
    run.inputs = inputs_data

    # 6. Transition status to queued (stage: discovery)
    run.status = "queued"
    run.stage = "discovery"
    run.heartbeat_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(run)

    # 7. Trigger Phase 2 of the background runner
    asyncio.create_task(run_research_run_phase2(run.id))

    return _run_model_to_schema(run)


@runs_router.get("/{id}/hypotheses", response_model=list[MarketHypothesis])
async def get_run_hypotheses(
    id: UUID,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[MarketHypothesis]:
    """Retrieve market hypotheses with signals for a research run."""
    # Verify parent run belongs to caller
    run_stmt = select(ResearchRunModel).where(
        ResearchRunModel.id == id,
        ResearchRunModel.owner_id == user.id,
    )
    run = (await session.execute(run_stmt)).scalar_one_or_none()
    if run is None:
        raise AppError(
            code=ErrorCode.NOT_FOUND,
            message=f"Research run with id '{id}' not found",
            status_code=404,
        )

    stmt = (
        select(MarketHypothesisModel)
        .where(
            MarketHypothesisModel.run_id == id,
            MarketHypothesisModel.owner_id == user.id,
        )
        .order_by(MarketHypothesisModel.created_at.asc(), MarketHypothesisModel.id.asc())
    )
    result = await session.execute(stmt)
    hypotheses = result.scalars().all()
    return [_hypothesis_model_to_schema(h) for h in hypotheses]
