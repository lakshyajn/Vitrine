"""
Background Runner for Research Runs (Workflow State Machine).
Implements Phase 1 (Planning -> Anchor Proposal -> Anchor Review) per AGENT.md Section 5.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from uuid import UUID

from sqlalchemy import select

from contracts.schemas import (
    ResearchPlan,
)
from backend.ai.service import get_ai_service
from backend.app.api.products import _product_model_to_schema
from backend.app.db.models import (
    MarketHypothesisModel,
    ProductModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.session import async_session_maker
from backend.integrations.qloo.provider import get_taste_provider

logger = logging.getLogger(__name__)


async def run_research_run_phase1(run_id: UUID) -> None:
    """
    Phase 1 of Research Run State Machine:
    1. Transition queued -> running (stage: planning), call plan_research, persist plan.
    2. Transition to stage: anchor_proposal, create taste_anchors from aesthetic_candidates (source: ai_proposed),
       call get_taste_provider().search_entities() on candidate labels (D15) and save returned entities with
       provider's source and is_demo, create initial market_hypotheses (status: proposed D13).
    3. Transition to status: awaiting_review, stage: anchor_review, and stop cleanly.
    """
    async with async_session_maker() as session:
        stmt = select(ResearchRunModel).where(ResearchRunModel.id == run_id)
        run = (await session.execute(stmt)).scalar_one_or_none()
        if not run:
            logger.error("Research run %s not found for Phase 1 execution", run_id)
            return

        # Check associated product
        prod_stmt = select(ProductModel).where(ProductModel.id == run.product_id)
        product_model = (await session.execute(prod_stmt)).scalar_one_or_none()
        if not product_model:
            run.status = "failed"
            run.error = {"code": "not_found", "message": "Associated product not found"}
            run.finished_at = datetime.now(timezone.utc)
            await session.commit()
            return

        product_schema = _product_model_to_schema(product_model)

        # 1. Transition queued -> running (stage: planning)
        run.status = "running"
        run.stage = "planning"
        run.started_at = datetime.now(timezone.utc)
        run.heartbeat_at = datetime.now(timezone.utc)
        await session.commit()

        # Call AI service plan_research(product)
        ai_service = get_ai_service()
        try:
            plan = await ai_service.plan_research(product_schema)
            plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else dict(plan)
            run.plan = plan_dict
        except Exception as exc:
            logger.exception("AI planning failed for run %s", run_id)
            run.status = "failed"
            run.error = {"code": "ai_output_invalid", "message": f"Planning failed: {str(exc)}"}
            run.finished_at = datetime.now(timezone.utc)
            await session.commit()
            return

        # 2. Transition to stage: anchor_proposal
        run.stage = "anchor_proposal"
        run.heartbeat_at = datetime.now(timezone.utc)
        await session.commit()

        # Resolve anchors via Taste Provider
        taste_provider = get_taste_provider()
        provider_name = getattr(taste_provider, "name", "mock")
        provider_is_demo = getattr(taste_provider, "is_demo", True)
        taste_source = "qloo" if provider_name == "qloo" else "demo"

        candidates = (
            plan.aesthetic_candidates
            if hasattr(plan, "aesthetic_candidates") and plan.aesthetic_candidates
            else plan_dict.get("aesthetic_candidates", [])
        )

        for candidate in candidates:
            clean_label = str(candidate).strip()
            if not clean_label:
                continue

            # (a) Create ai_proposed anchor
            ai_anchor = TasteAnchorModel(
                owner_id=run.owner_id,
                run_id=run.id,
                label=clean_label,
                entity_type="brand",
                external_id=None,
                source="ai_proposed",
                status="proposed",
                rationale=getattr(plan, "hypotheses_rationale", None) or f"Aesthetic candidate: {clean_label}",
                metadata_json={},
                is_demo=True,
            )
            session.add(ai_anchor)

            # (b) Call get_taste_provider().search_entities() on candidate labels (D15)
            try:
                entities = await taste_provider.search_entities(clean_label)
                for entity in entities:
                    entity_anchor = TasteAnchorModel(
                        owner_id=run.owner_id,
                        run_id=run.id,
                        label=entity.name or clean_label,
                        entity_type=entity.entity_type or "brand",
                        external_id=entity.id,
                        source=taste_source,
                        status="proposed",
                        rationale=f"Resolved taste entity from {provider_name}",
                        metadata_json=entity.metadata or {},
                        is_demo=provider_is_demo,
                    )
                    session.add(entity_anchor)
            except Exception as exc:
                logger.warning("Taste provider search_entities failed for '%s': %s", clean_label, exc)

        # Create initial market_hypotheses (status: proposed per D13)
        target_regions = (
            plan.target_regions
            if hasattr(plan, "target_regions") and plan.target_regions
            else plan_dict.get("target_regions", ["Western Europe"])
        )
        for region in target_regions:
            hypothesis = MarketHypothesisModel(
                owner_id=run.owner_id,
                run_id=run.id,
                title=f"Independent Retailer Affinity in {region}",
                rationale=getattr(plan, "hypotheses_rationale", None) or f"Target boutique stockists in {region} demonstrate cultural alignment.",
                region_hint=region,
                signals=[],
                status="proposed",  # D13 default proposed
            )
            session.add(hypothesis)

        # 3. Transition to status="awaiting_review", stage="anchor_review", and stop cleanly
        run.status = "awaiting_review"
        run.stage = "anchor_review"
        run.heartbeat_at = datetime.now(timezone.utc)
        await session.commit()
        logger.info("Research run %s reached awaiting_review (stage: anchor_review)", run_id)


async def run_research_run_phase2(run_id: UUID) -> None:
    """
    Phase 2 of Research Run State Machine (Discovery -> Assessment -> Scoring -> Done).
    Triggered after confirm-anchors. Skeleton for Step 6 (Day 3).
    """
    logger.info("Phase 2 triggered for run %s", run_id)
