"""
AI Service Interface, FixtureAIService, and LiveAIService (WS3 Section 3).
Matches Contract v0.2 Appendix A.6 and preserves 100% compatibility with WS2 tests.
"""

from __future__ import annotations

import os
import time
from typing import Any, Protocol

from backend.ai.client import NebiusClient
from backend.ai.logging import log_ai_call
from backend.ai.prompts import (
    PROMPT_VERSION,
    build_task_a_prompt,
    build_task_b_prompt,
    build_task_c_prompt,
    build_task_d_prompt,
)
from backend.ai.validation import (
    execute_with_single_repair,
    validate_and_ground_outreach_draft,
    validate_lead_assessment_claims,
    validate_research_plan_claims,
)
from backend.app.core.errors import AppError
from contracts.schemas import (
    DimensionAssessment,
    DimensionLabel,
    EvidenceItem,
    FactUsed,
    Lead,
    LeadAssessment,
    LeadCandidate,
    OutreachDraft,
    OutreachDraftStatus,
    PriceSegment,
    Product,
    ProductAttributes,
    ProductInput,
    ResearchPlan,
)


def build_outreach_fact_catalog(
    product: Product, evidence: list[EvidenceItem]
) -> dict[str, dict[str, str | None]]:
    """Build deterministic numbered fact catalog from approved product + stored evidence."""
    catalog: dict[str, dict[str, str | None]] = {
        "fact-1": {
            "text": (
                f"Workshop specializes in {product.name} ({product.category}) crafted with "
                f"{', '.join(product.materials or ['natural fibres'])} and {', '.join(product.motifs or ['artisan'])} motifs"
            ),
            "source_url": None,
        },
        "fact-2": {
            "text": (
                f"Wholesale positioning: {product.price_segment}, MOQ {product.moq} sets, "
                f"monthly capacity {product.monthly_capacity or 1500} units"
            ),
            "source_url": None,
        },
    }
    for item in evidence:
        catalog[f"evidence-{item.id}"] = {
            "text": item.excerpt[:200],
            "source_url": item.url,
        }
    return catalog


class AIService(Protocol):
    async def structure_product(
        self, description: str, known: ProductInput | None = None
    ) -> ProductAttributes:
        ...

    async def plan_research(self, product: Product) -> ResearchPlan:
        ...

    async def assess_lead(
        self, product: Product, lead: LeadCandidate, evidence: list[EvidenceItem]
    ) -> LeadAssessment:
        ...

    async def draft_outreach(
        self,
        product: Product,
        lead: Lead,
        evidence: list[EvidenceItem],
        previous: OutreachDraft | None = None,
    ) -> OutreachDraft:
        ...


class FixtureAIService:
    """
    Fixture-backed AIService returning schema-validated Contract v0.2 data with 0 API keys.
    Enforces WS3 truth rules: empty evidence -> UNKNOWN (never LOW), strict evidence_ids citations.
    """

    model_id: str = "fixture-nemotron-stub"

    async def structure_product(
        self, description: str, known: ProductInput | None = None
    ) -> ProductAttributes:
        t0 = time.monotonic()
        known_input = known or ProductInput()
        desc_text = (description or "").strip()

        uncertain: list[str] = []
        if "lead time" not in desc_text.lower():
            uncertain.append("lead_time_days")
        if "certification" not in desc_text.lower() and "gots" not in desc_text.lower():
            uncertain.append("certifications")

        result = ProductAttributes(
            style=known_input.style or ["handcrafted", "botanical", "artisanal"],
            materials=known_input.materials or ["cotton", "natural linen"],
            motifs=known_input.motifs or ["floral", "botanical"],
            colours=known_input.colours or ["terracotta", "indigo", "ochre"],
            price_segment=known_input.price_segment or PriceSegment.MID_PREMIUM,
            target_retailer_types=known_input.target_retailer_types
            or ["boutique", "concept store", "home decor"],
            uncertain_fields=uncertain,
            assumptions=["Inferred botanical style from text description"],
            category=known_input.category or "Home Textiles",
            price_min=known_input.price_min if known_input.price_min is not None else 30.0,
            price_max=known_input.price_max if known_input.price_max is not None else 120.0,
            currency=known_input.currency or "USD",
            moq=known_input.moq or 50,
            monthly_capacity=known_input.monthly_capacity or 1500,
        )
        log_ai_call(
            task="structure_product",
            model_id=self.model_id,
            latency_ms=int((time.monotonic() - t0) * 1000),
            validation_ok=True,
        )
        return result

    async def plan_research(self, product: Product) -> ResearchPlan:
        t0 = time.monotonic()
        plan = ResearchPlan(
            target_regions=["Western Europe", "North America"],
            target_retailer_types=product.target_retailer_types
            or ["independent home boutique", "concept store"],
            aesthetic_candidates=[
                "Block Print Aesthetic",
                "Artisanal Home Textiles",
                "Botanical Living",
            ],
            search_queries=[
                f"independent home decor boutique {product.name}",
                "artisan textile boutique stockists",
                f"independent lifestyle shop {product.category} block print cotton",
            ],
            hypotheses_rationale="Small independent design shops value provenance and artisan stories.",
            notes="Fixture-backed initial research plan",
        )
        validate_research_plan_claims(plan)
        log_ai_call(
            task="plan_research",
            model_id=self.model_id,
            latency_ms=int((time.monotonic() - t0) * 1000),
            validation_ok=True,
        )
        return plan

    async def assess_lead(
        self, product: Product, lead: LeadCandidate, evidence: list[EvidenceItem]
    ) -> LeadAssessment:
        t0 = time.monotonic()
        valid_evidence_ids = [item.id for item in evidence if item.id is not None]

        # WS3 Section 3.3 & 3.4: Empty evidence MUST yield UNKNOWN labels, never LOW
        if not valid_evidence_ids:
            empty_assessment = LeadAssessment(
                category_fit=DimensionAssessment(
                    label=DimensionLabel.UNKNOWN,
                    reasons=[],
                    evidence_ids=[],
                ),
                aesthetic_fit=DimensionAssessment(
                    label=DimensionLabel.UNKNOWN,
                    reasons=[],
                    evidence_ids=[],
                ),
                seller_compat=DimensionAssessment(
                    label=DimensionLabel.UNKNOWN,
                    reasons=[],
                    evidence_ids=[],
                ),
                summary=f"Insufficient stored evidence to assess {lead.name}.",
                unknowns=[
                    "No verified retailer evidence excerpts available",
                    "Specific MOQ requirements not stated on public website",
                ],
                model_id=self.model_id,
            )
            log_ai_call(
                task="assess_lead",
                model_id=self.model_id,
                latency_ms=int((time.monotonic() - t0) * 1000),
                validation_ok=True,
            )
            return empty_assessment

        primary_id = valid_evidence_ids[:1]
        assessment = LeadAssessment(
            category_fit=DimensionAssessment(
                label=DimensionLabel.HIGH,
                reasons=["Carries curated table linens and home textiles."],
                evidence_ids=primary_id,
            ),
            aesthetic_fit=DimensionAssessment(
                label=DimensionLabel.HIGH,
                reasons=["Visual identity emphasizes warm earth tones and botanical motifs."],
                evidence_ids=primary_id,
            ),
            seller_compat=DimensionAssessment(
                label=DimensionLabel.MEDIUM,
                reasons=["Stockist price point matches mid-premium range."],
                evidence_ids=primary_id,
            ),
            summary=f"Strong potential boutique partner for {product.name}.",
            unknowns=["Specific MOQ requirements not stated on public website"],
            model_id=self.model_id,
        )
        validate_lead_assessment_claims(assessment, evidence)
        log_ai_call(
            task="assess_lead",
            model_id=self.model_id,
            latency_ms=int((time.monotonic() - t0) * 1000),
            validation_ok=True,
        )
        return assessment

    async def draft_outreach(
        self,
        product: Product,
        lead: Lead,
        evidence: list[EvidenceItem],
        previous: OutreachDraft | None = None,
    ) -> OutreachDraft:
        t0 = time.monotonic()
        first_evidence = evidence[0] if evidence else None
        facts = [
            FactUsed(
                fact_id="fact-1",
                text=f"Workshop specializes in {product.name} with {', '.join(product.motifs)} motifs",
                source_url=None,
            )
        ]
        if first_evidence:
            facts.append(
                FactUsed(
                    fact_id=f"evidence-{first_evidence.id}",
                    text=first_evidence.excerpt[:120],
                    source_url=first_evidence.url,
                )
            )

        warnings: list[str] = []
        if not evidence:
            warnings.append("No verified store excerpt was available; personalize before sending.")

        subject = f"Wholesale inquiry: Handcrafted textiles for {lead.name}"
        body = (
            f"Dear {lead.name} team,\n\n"
            f"We noticed your beautifully curated collection. We are an artisan workshop creating "
            f"{product.name.lower()} in botanical motifs and natural dyes, positioned at {product.price_segment}.\n\n"
            f"We would love to share our wholesale line sheet with you.\n\nWarm regards,\nSample Seller"
        )

        draft = OutreachDraft(
            lead_id=lead.id,
            product_id=product.id,
            version=(previous.version + 1) if previous else 1,
            subject=subject,
            body=body,
            facts_used=facts,
            warnings=warnings,
            status=OutreachDraftStatus.DRAFT,
            parent_draft_id=previous.id if previous else None,
            is_demo=True,
        )
        log_ai_call(
            task="draft_outreach",
            model_id=self.model_id,
            latency_ms=int((time.monotonic() - t0) * 1000),
            validation_ok=True,
        )
        return draft


class LiveAIService:
    """
    Live Nebius/Nemotron AIService with strict schema validation,
    evidence citation post-checks, and single-repair retry (WS3 Section 3.2 & 3.3).

    Dual-Model Routing Architecture:
    - Primary Model (nvidia/nemotron-3-ultra-550b-a55b):
      Deep strategic reasoning for Task B (plan_research) and high-touch Task D (draft_outreach).
    - Fast Model (nvidia/nemotron-3.5-super-vl-120b-a12b):
      High-throughput vision/language extraction for Task A (structure_product) and
      rapid per-lead assessment for Task C (assess_lead) across discovery candidates.
    Cross-model fallback ensures resilient operation if either endpoint experiences upstream issues.
    """

    def __init__(
        self,
        client: NebiusClient,
        fast_client: NebiusClient | None = None,
    ) -> None:
        self.client = client
        self.fast_client = fast_client or client
        self.model_id = client.model_id
        self.fast_model_id = self.fast_client.model_id

    async def structure_product(
        self, description: str, known: ProductInput | None = None
    ) -> ProductAttributes:
        t0 = time.monotonic()
        known_input = known or ProductInput()
        messages = build_task_a_prompt(description, known_input)

        def _parse(data: dict[str, Any]) -> ProductAttributes:
            # Prefer seller's own provided fields
            for key, val in known_input.model_dump(exclude_none=True).items():
                if val:
                    data[key] = val
            return ProductAttributes.model_validate(data)

        # Fast model (Super VL 120B) first for rapid product structuring, fallback to primary
        clients_to_try = [self.fast_client]
        if self.fast_client is not self.client:
            clients_to_try.append(self.client)

        last_exc: Exception | None = None
        for active_client in clients_to_try:
            try:
                result, t_in, t_out = await execute_with_single_repair(
                    llm_call=lambda msgs: active_client.complete_json(msgs, temperature=0.1),
                    messages=messages,
                    parse_and_validate=_parse,
                )
                log_ai_call(
                    task="structure_product",
                    model_id=active_client.model_id,
                    prompt_version=PROMPT_VERSION,
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    validation_ok=True,
                    tokens_in=t_in,
                    tokens_out=t_out,
                )
                return result
            except AppError as exc:
                last_exc = exc
                log_ai_call(
                    task="structure_product",
                    model_id=active_client.model_id,
                    prompt_version=PROMPT_VERSION,
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    validation_ok=False,
                    error_code=str(exc.code),
                )
        if last_exc:
            raise last_exc
        raise AppError("AI service failed to structure product", code="ai_generation_failed")

    async def plan_research(self, product: Product) -> ResearchPlan:
        t0 = time.monotonic()
        messages = build_task_b_prompt(product)

        def _parse(data: dict[str, Any]) -> ResearchPlan:
            plan = ResearchPlan.model_validate(data)
            validate_research_plan_claims(plan)
            return plan

        # Primary model (Ultra 550B) first for deep reasoning hypotheses, fallback to fast
        clients_to_try = [self.client]
        if self.fast_client is not self.client:
            clients_to_try.append(self.fast_client)

        last_exc: Exception | None = None
        for active_client in clients_to_try:
            try:
                result, t_in, t_out = await execute_with_single_repair(
                    llm_call=lambda msgs: active_client.complete_json(msgs, temperature=0.2),
                    messages=messages,
                    parse_and_validate=_parse,
                )
                log_ai_call(
                    task="plan_research",
                    model_id=active_client.model_id,
                    prompt_version=PROMPT_VERSION,
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    validation_ok=True,
                    tokens_in=t_in,
                    tokens_out=t_out,
                )
                return result
            except AppError as exc:
                last_exc = exc
                log_ai_call(
                    task="plan_research",
                    model_id=active_client.model_id,
                    prompt_version=PROMPT_VERSION,
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    validation_ok=False,
                    error_code=str(exc.code),
                )
        if last_exc:
            raise last_exc
        raise AppError("AI service failed to generate research plan", code="ai_generation_failed")

    async def assess_lead(
        self, product: Product, lead: LeadCandidate, evidence: list[EvidenceItem]
    ) -> LeadAssessment:
        if not evidence:
            return await FixtureAIService().assess_lead(product, lead, evidence)

        t0 = time.monotonic()
        messages = build_task_c_prompt(product, lead, evidence)

        # Fast model (Super VL 120B) first for fast per-lead assessment across large candidate batches
        clients_to_try = [self.fast_client]
        if self.fast_client is not self.client:
            clients_to_try.append(self.client)

        last_exc: Exception | None = None
        for active_client in clients_to_try:
            current_model = active_client.model_id

            def _parse(data: dict[str, Any]) -> LeadAssessment:
                data["model_id"] = current_model
                assessment = LeadAssessment.model_validate(data)
                validate_lead_assessment_claims(assessment, evidence)
                return assessment

            try:
                result, t_in, t_out = await execute_with_single_repair(
                    llm_call=lambda msgs: active_client.complete_json(msgs, temperature=0.1),
                    messages=messages,
                    parse_and_validate=_parse,
                )
                log_ai_call(
                    task="assess_lead",
                    model_id=active_client.model_id,
                    prompt_version=PROMPT_VERSION,
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    validation_ok=True,
                    tokens_in=t_in,
                    tokens_out=t_out,
                )
                return result
            except AppError as exc:
                last_exc = exc
                log_ai_call(
                    task="assess_lead",
                    model_id=active_client.model_id,
                    prompt_version=PROMPT_VERSION,
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    validation_ok=False,
                    error_code=str(exc.code),
                )
        if last_exc:
            raise last_exc
        raise AppError("AI service failed to assess lead", code="ai_generation_failed")

    async def draft_outreach(
        self,
        product: Product,
        lead: Lead,
        evidence: list[EvidenceItem],
        previous: OutreachDraft | None = None,
    ) -> OutreachDraft:
        t0 = time.monotonic()
        catalog = build_outreach_fact_catalog(product, evidence)
        messages = build_task_d_prompt(catalog, lead.name, previous=previous)

        def _parse(data: dict[str, Any]) -> OutreachDraft:
            grounded = validate_and_ground_outreach_draft(data, catalog)
            return OutreachDraft(
                lead_id=lead.id,
                product_id=product.id,
                version=(previous.version + 1) if previous else 1,
                subject=grounded["subject"],
                body=grounded["body"],
                facts_used=[FactUsed.model_validate(f) for f in grounded["facts_used"]],
                warnings=grounded["warnings"],
                status=OutreachDraftStatus.DRAFT,
                parent_draft_id=previous.id if previous else None,
                is_demo=False,
            )

        # Primary model (Ultra 550B) first for nuanced buyer outreach drafting, fallback to fast
        clients_to_try = [self.client]
        if self.fast_client is not self.client:
            clients_to_try.append(self.fast_client)

        last_exc: Exception | None = None
        for active_client in clients_to_try:
            try:
                result, t_in, t_out = await execute_with_single_repair(
                    llm_call=lambda msgs: active_client.complete_json(msgs, temperature=0.35),
                    messages=messages,
                    parse_and_validate=_parse,
                )
                log_ai_call(
                    task="draft_outreach",
                    model_id=active_client.model_id,
                    prompt_version=PROMPT_VERSION,
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    validation_ok=True,
                    tokens_in=t_in,
                    tokens_out=t_out,
                )
                return result
            except AppError as exc:
                last_exc = exc
                log_ai_call(
                    task="draft_outreach",
                    model_id=active_client.model_id,
                    prompt_version=PROMPT_VERSION,
                    latency_ms=int((time.monotonic() - t0) * 1000),
                    validation_ok=False,
                    error_code=str(exc.code),
                )
        if last_exc:
            raise last_exc
        raise AppError("AI service failed to draft outreach", code="ai_generation_failed")


def get_ai_service() -> AIService:
    """Factory returning LiveAIService if NEBIUS_API_KEY is configured, else FixtureAIService."""
    if "NEBIUS_API_KEY" in os.environ and not os.environ["NEBIUS_API_KEY"].strip():
        return FixtureAIService()

    api_key = os.environ.get("NEBIUS_API_KEY", "").strip()
    model_id = os.environ.get("NEBIUS_MODEL_ID", "").strip() or "nvidia/nemotron-3-ultra-550b-a55b"
    base_url = os.environ.get("NEBIUS_BASE_URL", "").strip() or "https://integrate.api.nvidia.com/v1"

    fast_api_key = os.environ.get("NEMOTRON_FAST_API_KEY", "").strip()
    fast_model_id = (
        os.environ.get("NEMOTRON_FAST_MODEL_ID", "").strip()
        or "nvidia/nemotron-3.5-super-vl-120b-a12b"
    )
    fast_base_url = (
        os.environ.get("NEMOTRON_FAST_BASE_URL", "").strip()
        or "https://integrate.api.nvidia.com/v1"
    )

    try:
        from backend.app.core.config import get_settings

        settings = get_settings()
        api_key = api_key or getattr(settings, "nebius_api_key", None)
        model_id = getattr(settings, "nebius_model_id", None) or model_id
        base_url = getattr(settings, "nebius_base_url", None) or base_url

        fast_api_key = fast_api_key or getattr(settings, "nemotron_fast_api_key", None)
        fast_model_id = getattr(settings, "nemotron_fast_model_id", None) or fast_model_id
        fast_base_url = getattr(settings, "nemotron_fast_base_url", None) or fast_base_url
    except Exception:
        pass

    # If primary key is absent but fast key is present, use fast key as primary as well
    if not api_key and fast_api_key:
        api_key = fast_api_key
        model_id = fast_model_id
        base_url = fast_base_url

    if api_key and str(api_key).strip():
        primary_client = NebiusClient(
            api_key=str(api_key).strip(),
            model_id=str(model_id).strip(),
            base_url=str(base_url).strip(),
        )
        fast_client = None
        if fast_api_key and str(fast_api_key).strip():
            fast_client = NebiusClient(
                api_key=str(fast_api_key).strip(),
                model_id=str(fast_model_id).strip(),
                base_url=str(fast_base_url).strip(),
            )
        return LiveAIService(primary_client, fast_client=fast_client)
    return FixtureAIService()