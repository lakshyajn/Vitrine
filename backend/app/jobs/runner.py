"""
Background Runner for Research Runs (Workflow State Machine).
Implements Phase 1 (Planning -> Anchor Proposal -> Anchor Review)
and Phase 2 (Discovery -> Assessment -> Scoring -> Done).

Precedence:
- AGENT.md Sections 3, 5, 7, 9, 11 (DECISION-D2, D8, D9, D15)
- WS2_Spec.md Sections 4, 5.1, 5.2, 8
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, update

from contracts.schemas import (
    EvidenceItem,
    EvidenceSourceType,
    InsightOptions,
    LeadLocation,
    ProvenanceTag,
    ResearchPlan,
    TasteAnchor,
    TasteAnchorSource,
    TasteAnchorStatus,
)
from backend.ai.service import get_ai_service
from backend.app.api.products import _product_model_to_schema
from backend.app.core.config import get_settings
from backend.app.db.models import (
    LeadEvidenceModel,
    LeadModel,
    MarketHypothesisModel,
    ProductModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.session import async_session_maker
from backend.app.scoring import compute_scores_and_tier, is_domain_excluded
from backend.integrations.qloo.provider import get_taste_provider
from backend.research.pipeline import get_research_pipeline

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
    Triggered after confirm-anchors (AGENT.md Section 3, 5, 11 D2, D8, D9, D15 & WS2 Spec Section 5.1).

    Orchestrates:
    1. Transition queued -> running (stage: discovery).
    2. Taste resolution on confirmed anchors: resolve missing entity IDs and get_insights(),
       attaching returned signals to market_hypotheses with accurate source and is_demo (D15).
    3. Execute ResearchPipeline.run(...) capped at MAX_LEADS_PER_RUN (default 40).
    4. Clean zero-candidate completion if Tavily/mock finds nothing (never invent leads).
    5. Transition to stage: assessment and stage: scoring:
       - Upsert LeadModel on (owner_id, product_id, canonical_domain). On conflict, update run_id (D2).
       - Insert/upsert lead_evidence rows FIRST so every EvidenceItem has a persisted DB UUID (D8).
       - Resolve duplicate_of from possible_duplicate_of_domain (D9).
       - Call assess_lead and compute_scores_and_tier with per-lead error isolation.
    6. Transition status: completed, stage: done.
    """
    logger.info("Starting Phase 2 for research run %s", run_id)
    try:
        async with async_session_maker() as session:
            # 1. Fetch Run and Product
            run_stmt = select(ResearchRunModel).where(ResearchRunModel.id == run_id)
            run = (await session.execute(run_stmt)).scalar_one_or_none()
            if not run:
                logger.error("Research run %s not found for Phase 2 execution", run_id)
                return

            # Check run status: only queued or awaiting_review can transition to Phase 2
            if run.status not in ("queued", "awaiting_review"):
                logger.info(
                    "Research run %s status is '%s' (not queued/awaiting_review), skipping Phase 2",
                    run_id,
                    run.status,
                )
                return

            prod_stmt = select(ProductModel).where(ProductModel.id == run.product_id)
            product_model = (await session.execute(prod_stmt)).scalar_one_or_none()
            if not product_model:
                run.status = "failed"
                run.error = {"code": "not_found", "message": "Associated product not found"}
                run.finished_at = datetime.now(timezone.utc)
                await session.commit()
                return

            product_schema = _product_model_to_schema(product_model)
            plan_schema = (
                ResearchPlan.model_validate(run.plan)
                if run.plan
                else ResearchPlan()
            )

            # Transition queued -> running (stage: discovery)
            run.status = "running"
            run.stage = "discovery"
            run.started_at = run.started_at or datetime.now(timezone.utc)
            run.heartbeat_at = datetime.now(timezone.utc)
            await session.commit()

            # 2. Taste resolution on confirmed anchors (DECISION-D15)
            taste_provider = get_taste_provider()
            anchors_stmt = select(TasteAnchorModel).where(
                TasteAnchorModel.run_id == run.id,
                TasteAnchorModel.status == "confirmed",
            )
            confirmed_models = (await session.execute(anchors_stmt)).scalars().all()

            signals_to_attach: list[dict[str, Any]] = []
            for anchor_m in confirmed_models:
                # Resolve missing entity IDs for custom or unlinked anchors
                if not anchor_m.external_id:
                    try:
                        entities = await taste_provider.search_entities(anchor_m.label)
                        if entities:
                            anchor_m.external_id = entities[0].id
                            if entities[0].metadata:
                                meta = dict(anchor_m.metadata_json or {})
                                meta.update(entities[0].metadata)
                                anchor_m.metadata_json = meta
                    except Exception as exc:
                        logger.warning("Entity search failed for anchor %s: %s", anchor_m.label, exc)

                # Fetch insights from taste provider
                target_entity = anchor_m.external_id or anchor_m.label
                try:
                    insights = await taste_provider.get_insights(
                        target_entity,
                        InsightOptions(entity_type=anchor_m.entity_type, max_results=5),
                    )
                    for sig in insights:
                        signals_to_attach.append({
                            "type": sig.type,
                            "text": sig.text,
                            "source": sig.source or getattr(taste_provider, "name", "mock"),
                            "source_ref": sig.source_ref,
                            "is_demo": getattr(sig, "is_demo", getattr(taste_provider, "is_demo", True)),
                        })
                except Exception as exc:
                    logger.warning("Insights lookup failed for anchor %s: %s", target_entity, exc)

            # Attach signals to market hypotheses for this run (DECISION-D15)
            if signals_to_attach:
                hypos_stmt = select(MarketHypothesisModel).where(MarketHypothesisModel.run_id == run.id)
                hypos = (await session.execute(hypos_stmt)).scalars().all()
                if hypos:
                    for hypo in hypos:
                        existing = list(hypo.signals or [])
                        seen = {(s.get("type"), s.get("text")) for s in existing}
                        for new_s in signals_to_attach:
                            key = (new_s.get("type"), new_s.get("text"))
                            if key not in seen:
                                existing.append(new_s)
                                seen.add(key)
                        hypo.signals = existing
                else:
                    new_hypo = MarketHypothesisModel(
                        owner_id=run.owner_id,
                        run_id=run.id,
                        title="Taste Anchor Signals",
                        rationale="Signals resolved from confirmed taste anchors.",
                        region_hint=None,
                        signals=signals_to_attach,
                        status="confirmed",
                    )
                    session.add(new_hypo)

            await session.commit()

            # Build confirmed anchors schema list for ResearchPipeline
            confirmed_anchor_schemas = [
                TasteAnchor(
                    id=am.id,
                    owner_id=am.owner_id,
                    run_id=am.run_id,
                    label=am.label,
                    entity_type=am.entity_type,
                    external_id=am.external_id,
                    source=(
                        TasteAnchorSource(am.source)
                        if am.source in TasteAnchorSource._value2member_map_
                        else TasteAnchorSource.AI_PROPOSED
                    ),
                    status=(
                        TasteAnchorStatus(am.status)
                        if am.status in TasteAnchorStatus._value2member_map_
                        else TasteAnchorStatus.CONFIRMED
                    ),
                    rationale=am.rationale,
                    metadata=am.metadata_json or {},
                    is_demo=am.is_demo,
                )
                for am in confirmed_models
            ]

            # 3. Call ResearchPipeline
            pipeline = get_research_pipeline()

            def on_progress(stage: str, data: dict[str, Any]) -> None:
                logger.info("Pipeline progress for run %s: stage=%s data=%s", run.id, stage, data)

            try:
                candidates = await pipeline.run(
                    product=product_schema,
                    plan=plan_schema,
                    anchors=confirmed_anchor_schemas,
                    on_progress=on_progress,
                )
            except Exception as exc:
                logger.exception("Research pipeline execution failed for run %s: %s", run.id, exc)
                run.status = "failed"
                run.error = {"code": "upstream_unavailable", "message": f"Discovery failed: {str(exc)}"}
                run.finished_at = datetime.now(timezone.utc)
                await session.commit()
                return

            # Apply lead cap (default 40)
            settings = get_settings()
            max_leads = getattr(settings, "max_leads_per_run", 40)
            candidates = candidates[:max_leads]

            # 4. Handle 0 candidates cleanly (AGENT.md Section 9)
            if not candidates:
                run.status = "completed"
                run.stage = "done"
                run.finished_at = datetime.now(timezone.utc)
                plan_data = dict(run.plan or {})
                plan_data["notes"] = (
                    (plan_data.get("notes") or "") + " [Discovery completed: 0 candidate leads found]"
                ).strip()
                run.plan = plan_data
                await session.commit()
                logger.info("Run %s completed with zero leads (clean completion)", run.id)
                return

            # 5. Transition to stage: assessment
            run.stage = "assessment"
            run.heartbeat_at = datetime.now(timezone.utc)
            await session.commit()

            ai_service = get_ai_service()
            seen_domains_in_run: dict[str, UUID] = {}

            for candidate in candidates:
                # (a) Upsert Lead row on (owner_id, product_id, canonical_domain) (DECISION-D2)
                lead_model = None
                if candidate.canonical_domain in seen_domains_in_run:
                    existing_id = seen_domains_in_run[candidate.canonical_domain]
                    lead_model = (
                        await session.execute(
                            select(LeadModel).where(LeadModel.id == existing_id)
                        )
                    ).scalar_one_or_none()

                if lead_model is None:
                    lead_stmt = select(LeadModel).where(
                        LeadModel.owner_id == run.owner_id,
                        LeadModel.product_id == run.product_id,
                        LeadModel.canonical_domain == candidate.canonical_domain,
                    )
                    lead_model = (await session.execute(lead_stmt)).scalar_one_or_none()

                if lead_model is not None:
                    # Update run_id to current run so GET /leads?run_id= returns it (DECISION-D2)
                    lead_model.run_id = run.id
                    lead_model.website_verified = candidate.website_verified
                    lead_model.website_checked_at = datetime.now(timezone.utc)
                    if candidate.name:
                        lead_model.name = candidate.name
                    if candidate.location:
                        lead_model.location = candidate.location.model_dump(mode="json")
                else:
                    lead_model = LeadModel(
                        id=uuid4(),
                        owner_id=run.owner_id,
                        run_id=run.id,
                        product_id=run.product_id,
                        name=candidate.name,
                        website=candidate.website,
                        canonical_domain=candidate.canonical_domain,
                        location=candidate.location.model_dump(mode="json") if candidate.location else None,
                        retailer_type=candidate.retailer_type or "boutique",
                        website_verified=candidate.website_verified,
                        website_checked_at=datetime.now(timezone.utc),
                        tier="needs_review",
                        scores={},
                        assessment=None,
                        cultural_affinity=None,
                        review_status="new",
                        notes=None,
                        duplicate_of=None,
                        is_demo=getattr(candidate, "is_demo", False),
                    )
                    session.add(lead_model)

                await session.flush()
                seen_domains_in_run[candidate.canonical_domain] = lead_model.id

                # (b) Insert/upsert lead_evidence rows FIRST so EvidenceItems have DB UUIDs (DECISION-D8)
                existing_ev_stmt = select(LeadEvidenceModel).where(LeadEvidenceModel.lead_id == lead_model.id)
                existing_evs = (await session.execute(existing_ev_stmt)).scalars().all()
                existing_keys = {(ev.url.strip(), ev.excerpt.strip()) for ev in existing_evs}

                for item in (candidate.evidence or []):
                    key = (item.url.strip(), item.excerpt.strip())
                    if key not in existing_keys:
                        ev_model = LeadEvidenceModel(
                            id=uuid4(),
                            owner_id=run.owner_id,
                            lead_id=lead_model.id,
                            url=item.url.strip(),
                            excerpt=item.excerpt.strip(),
                            source_type=(
                                item.source_type.value
                                if hasattr(item.source_type, "value")
                                else str(item.source_type)
                            ),
                            retrieved_at=item.retrieved_at or datetime.now(timezone.utc),
                            published_at=item.published_at,
                            domain_matches_lead=item.domain_matches_lead,
                            provenance=(
                                item.provenance.value
                                if hasattr(item.provenance, "value")
                                else str(item.provenance)
                            ),
                            is_demo=getattr(item, "is_demo", False),
                        )
                        session.add(ev_model)
                        existing_keys.add(key)

                await session.flush()

                # Reload all persisted evidence items with actual DB UUIDs
                all_ev_stmt = select(LeadEvidenceModel).where(LeadEvidenceModel.lead_id == lead_model.id)
                persisted_ev_models = (await session.execute(all_ev_stmt)).scalars().all()

                persisted_evidence_items = [
                    EvidenceItem(
                        id=em.id,
                        owner_id=em.owner_id,
                        lead_id=em.lead_id,
                        url=em.url,
                        excerpt=em.excerpt,
                        source_type=(
                            EvidenceSourceType(em.source_type)
                            if em.source_type in EvidenceSourceType._value2member_map_
                            else EvidenceSourceType.OFFICIAL_SITE
                        ),
                        retrieved_at=em.retrieved_at,
                        published_at=em.published_at,
                        domain_matches_lead=em.domain_matches_lead,
                        provenance=(
                            ProvenanceTag(em.provenance)
                            if em.provenance in ProvenanceTag._value2member_map_
                            else ProvenanceTag.VERIFIED_FACT
                        ),
                        is_demo=em.is_demo,
                    )
                    for em in persisted_ev_models
                ]

                # (c) Resolve duplicate_of if possible_duplicate_of_domain is set (DECISION-D9)
                if candidate.possible_duplicate_of_domain:
                    dup_target_stmt = select(LeadModel.id).where(
                        LeadModel.owner_id == run.owner_id,
                        LeadModel.product_id == run.product_id,
                        LeadModel.canonical_domain == candidate.possible_duplicate_of_domain,
                    )
                    dup_id = (await session.execute(dup_target_stmt)).scalar_one_or_none()
                    if dup_id:
                        lead_model.duplicate_of = dup_id

                await session.commit()

                # (d) Assessment & scoring with per-lead failure isolation (AGENT.md Section 5)
                try:
                    assessment = await ai_service.assess_lead(
                        product=product_schema,
                        lead=candidate,
                        evidence=persisted_evidence_items,
                    )
                    assessment_dict = (
                        assessment.model_dump(mode="json")
                        if hasattr(assessment, "model_dump")
                        else dict(assessment)
                    )

                    is_excluded = is_domain_excluded(candidate.canonical_domain)
                    scores, tier = compute_scores_and_tier(
                        lead_candidate=candidate,
                        evidence_items=persisted_evidence_items,
                        assessment=assessment,
                        is_excluded_domain=is_excluded,
                    )

                    lead_model.assessment = assessment_dict
                    lead_model.scores = scores.model_dump(mode="json")
                    lead_model.tier = tier.value if hasattr(tier, "value") else str(tier)

                except Exception as exc:
                    logger.warning(
                        "Per-lead assessment/scoring failed for %s: %s (isolating to needs_review)",
                        candidate.canonical_domain,
                        exc,
                    )
                    err_note = f"Per-lead assessment error: {str(exc)}"
                    lead_model.tier = "needs_review"
                    lead_model.notes = err_note

                    fallback_scores, _ = compute_scores_and_tier(
                        lead_candidate=candidate,
                        evidence_items=persisted_evidence_items,
                        assessment=None,
                        is_excluded_domain=is_domain_excluded(candidate.canonical_domain),
                    )
                    scores_dict = fallback_scores.model_dump(mode="json")
                    scores_dict["tier_reasons"] = [err_note] + scores_dict.get("tier_reasons", [])
                    lead_model.scores = scores_dict
                    lead_model.assessment = {
                        "summary": "Assessment incomplete due to processing error.",
                        "unknowns": [err_note],
                    }

                await session.commit()

            # (e) Second pass: Resolve duplicate_of for candidates where secondary was discovered before primary
            for candidate in candidates:
                if candidate.possible_duplicate_of_domain:
                    primary_stmt = select(LeadModel.id).where(
                        LeadModel.owner_id == run.owner_id,
                        LeadModel.product_id == run.product_id,
                        LeadModel.canonical_domain == candidate.possible_duplicate_of_domain,
                    )
                    primary_id = (await session.execute(primary_stmt)).scalar_one_or_none()
                    if primary_id:
                        await session.execute(
                            update(LeadModel)
                            .where(
                                LeadModel.owner_id == run.owner_id,
                                LeadModel.product_id == run.product_id,
                                LeadModel.canonical_domain == candidate.canonical_domain,
                            )
                            .values(duplicate_of=primary_id)
                        )
            await session.commit()

            # 6. Transition stage to scoring, then completion
            run.stage = "scoring"
            run.heartbeat_at = datetime.now(timezone.utc)
            await session.commit()

            run.status = "completed"
            run.stage = "done"
            run.finished_at = datetime.now(timezone.utc)
            run.heartbeat_at = datetime.now(timezone.utc)
            await session.commit()
            logger.info("Research run %s completed Phase 2 successfully with %d candidates", run.id, len(candidates))

    except Exception as exc:
        logger.exception("Unhandled error in run_research_run_phase2 for run %s: %s", run_id, exc)
        try:
            async with async_session_maker() as err_session:
                r = (await err_session.execute(select(ResearchRunModel).where(ResearchRunModel.id == run_id))).scalar_one_or_none()
                if r:
                    r.status = "failed"
                    r.error = {"code": "internal_error", "message": f"Run execution failed: {str(exc)}"}
                    r.finished_at = datetime.now(timezone.utc)
                    await err_session.commit()
        except Exception:
            pass
