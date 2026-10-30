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
    RetailerKind,
    SellsCategoryAnswer,
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
            style=known_input.style or (["minimalist"] if any(w in desc_text.lower() for w in ("pencil", "stationery", "minimal")) else ["handcrafted", "artisanal"]),
            materials=known_input.materials or ([m for m in ("cedar wood", "graphite", "wood", "ceramic", "leather", "cotton", "linen") if m in desc_text.lower()] or ["mixed materials"]),
            motifs=known_input.motifs or ([mo for mo in ("geometric", "botanical", "plain", "striped") if mo in desc_text.lower()]),
            colours=known_input.colours or ([c for c in ("black", "natural", "indigo", "terracotta", "white") if c in desc_text.lower()] or ["natural"]),
            price_segment=known_input.price_segment or PriceSegment.MID_PREMIUM,
            target_retailer_types=known_input.target_retailer_types
            or ["independent boutique", "concept store"],
            uncertain_fields=uncertain,
            assumptions=["Inferred product attributes from description text"],
            category=known_input.category or ("stationery" if any(w in desc_text.lower() or (known_input.name and w in known_input.name.lower()) for w in ("pencil", "pen", "notebook", "journal")) else ("ceramics" if any(w in desc_text.lower() for w in ("mug", "ceramic", "pottery")) else ("Home Textiles" if any(w in desc_text.lower() or (known_input.name and w in known_input.name.lower()) for w in ("textile", "linen", "cushion", "runner", "throw", "fabric")) else "handcrafted goods"))),
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
            or [f"independent {product.category} boutique", "concept store"],
            aesthetic_candidates=([] if any(w in product.category.lower() for w in ("stationery", "pencil", "pen", "tool", "office")) else [f"{product.category.title()} Aesthetic", f"Curated {product.category.title()}"]),




            search_queries=[
                f"independent {product.category} boutique {product.name}",
                f"curated {product.category} retailer stockists",
                f"buy {product.name} online store",
            ],



            taste_relevance=("not_applicable" if any(w in product.category.lower() for w in ("stationery", "pencil", "pen", "tool", "office")) else "applicable"),
            taste_relevance_reason="Utility category where aesthetic affinity is secondary to stockist availability." if any(w in product.category.lower() for w in ("stationery", "pencil", "pen", "tool", "office")) else f"Aesthetic affinity for {product.category}",
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
                reasons=[f"Carries curated collections matching {product.category}."],
                evidence_ids=primary_id,
            ),
            aesthetic_fit=DimensionAssessment(
                label=DimensionLabel.HIGH,
                reasons=[f"Visual identity emphasizes design profile matching {product.category}."],
                evidence_ids=primary_id,
            ),
            seller_compat=DimensionAssessment(
                label=DimensionLabel.MEDIUM,
                reasons=["Stockist price point matches mid-premium range."],
                evidence_ids=primary_id,
            ),
            retailer_kind=RetailerKind.RETAILER,
            retailer_kind_reasons=["Independent retail business selling curated products."],
            retailer_kind_evidence_ids=primary_id,
            sells_product_category=SellsCategoryAnswer.YES,
            sells_product_category_reasons=[f"Store catalog verifies active offerings in {product.category}."],
            sells_product_category_evidence_ids=primary_id,
            summary=f"Strong potential boutique partner for {product.name} ({product.category}).",
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
            # Prefer seller's own provided fields (only if explicitly set)
            if known:
                for key, val in known.model_dump(exclude_unset=True).items():
                    if val is not None and val != [] and val != "":
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
            return LeadAssessment(
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
                unknowns=["No evidence collected"],
                model_id=self.fast_client.model_id,
            )

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
    """
    Factory returning LiveAIService configured for Nebius Token Factory with automatic
    NVIDIA NIM fallback, or directly NVIDIA NIM if Token Factory is not configured.
    Falls back to FixtureAIService when no keys are provided or APP_ENV=test.
    Enforces production safeguards against unconfigured providers in production.
    """
    if os.environ.get("APP_ENV") == "test":
        return FixtureAIService()

    app_env = "dev"
    try:
        from backend.app.core.config import get_settings
        settings = get_settings()
        app_env = getattr(settings, "app_env", "dev") or "dev"
    except Exception:
        settings = None

    # 1. Nebius Token Factory Key
    tf_key = (
        os.environ.get("NEBIUS_TOKEN_FACTORY_API_KEY", "").strip()
        or (getattr(settings, "nebius_token_factory_api_key", None) or "").strip()
    )
    # If a user accidentally placed an nvapi-* key into NEBIUS_TOKEN_FACTORY_API_KEY, treat it as NVIDIA key
    nvidia_ultra_override = ""
    if tf_key.startswith("nvapi-"):
        nvidia_ultra_override = tf_key
        tf_key = ""

    # 2. Respective NVIDIA NIM keys for Ultra 550B and Super VL 120B
    nvidia_ultra_key = (
        os.environ.get("NEBIUS_API_KEY", "").strip()
        or (getattr(settings, "nebius_api_key", None) or "").strip()
        or nvidia_ultra_override
    )
    nvidia_fast_key = (
        os.environ.get("NEMOTRON_FAST_API_KEY", "").strip()
        or (getattr(settings, "nemotron_fast_api_key", None) or "").strip()
    )

    # 3. Model IDs
    model_id = (
        os.environ.get("NEBIUS_MODEL_ID", "").strip()
        or getattr(settings, "nebius_model_id", "nvidia/nemotron-3-ultra-550b-a55b")
    )
    fast_model_id = (
        os.environ.get("NEMOTRON_FAST_MODEL_ID", "").strip()
        or getattr(settings, "nemotron_fast_model_id", "nvidia/nemotron-3.5-super-vl-120b-a12b")
    )

    # 4. Base URLs
    tf_base_url = (
        os.environ.get("NEBIUS_BASE_URL", "").strip()
        or getattr(settings, "nebius_base_url", "https://api.tokenfactory.nebius.com/v1")
    )
    nvidia_base_url = "https://integrate.api.nvidia.com/v1"

    # If neither Token Factory nor NVIDIA keys are available, check production safeguard or fallback to fixture
    if not tf_key and not nvidia_ultra_key and not nvidia_fast_key:
        if str(app_env).strip().lower() in ("production", "prod"):
            raise AppError("ai_generation_failed", "AI service provider is unconfigured or unavailable in production.")
        return FixtureAIService()

    # --------------------------------------------------------------------------
    # Fallback Case: Token Factory Key is NOT found / not configured.
    # Runs exactly as before Token Factory: calls Ultra & Super via NVIDIA NIM.
    # --------------------------------------------------------------------------
    if not tf_key:
        primary_key = nvidia_ultra_key or nvidia_fast_key
        fast_key = nvidia_fast_key or nvidia_ultra_key

        primary_client = NebiusClient(
            api_key=primary_key,
            model_id=model_id,
            base_url=nvidia_base_url,
        )
        fast_client = None
        if fast_key:
            fast_client = NebiusClient(
                api_key=fast_key,
                model_id=fast_model_id,
                base_url=nvidia_base_url,
            )
        return LiveAIService(primary_client, fast_client=fast_client)

    # --------------------------------------------------------------------------
    # Token Factory Case: Token Factory Key IS found.
    # Targets Token Factory with transparent runtime fallback to NVIDIA NIM.
    # --------------------------------------------------------------------------
    primary_client = NebiusClient(
        api_key=tf_key,
        model_id=model_id,
        base_url=tf_base_url,
        fallback_api_key=nvidia_ultra_key or None,
        fallback_base_url=nvidia_base_url,
    )

    fast_client = NebiusClient(
        api_key=tf_key,
        model_id=fast_model_id,
        base_url=tf_base_url,
        fallback_api_key=nvidia_fast_key or nvidia_ultra_key or None,
        fallback_base_url=nvidia_base_url,
    )

    return LiveAIService(primary_client, fast_client=fast_client)

    # 1. Nebius Token Factory Key
    tf_key = (
        os.environ.get("NEBIUS_TOKEN_FACTORY_API_KEY", "").strip()
        or (getattr(settings, "nebius_token_factory_api_key", None) or "").strip()
    )
    # If a user accidentally placed an nvapi-* key into NEBIUS_TOKEN_FACTORY_API_KEY, treat it as NVIDIA key
    nvidia_ultra_override = ""
    if tf_key.startswith("nvapi-"):
        nvidia_ultra_override = tf_key
        tf_key = ""

    # 2. Respective NVIDIA NIM keys for Ultra 550B and Super VL 120B
    nvidia_ultra_key = (
        os.environ.get("NEBIUS_API_KEY", "").strip()
        or (getattr(settings, "nebius_api_key", None) or "").strip()
        or nvidia_ultra_override
    )
    nvidia_fast_key = (
        os.environ.get("NEMOTRON_FAST_API_KEY", "").strip()
        or (getattr(settings, "nemotron_fast_api_key", None) or "").strip()
    )

    # 3. Model IDs
    model_id = (
        os.environ.get("NEBIUS_MODEL_ID", "").strip()
        or getattr(settings, "nebius_model_id", "nvidia/nemotron-3-ultra-550b-a55b")
    )
    fast_model_id = (
        os.environ.get("NEMOTRON_FAST_MODEL_ID", "").strip()
        or getattr(settings, "nemotron_fast_model_id", "nvidia/nemotron-3.5-super-vl-120b-a12b")
    )

    # 4. Base URLs
    tf_base_url = (
        os.environ.get("NEBIUS_BASE_URL", "").strip()
        or getattr(settings, "nebius_base_url", "https://api.tokenfactory.nebius.com/v1")
    )
    nvidia_base_url = "https://integrate.api.nvidia.com/v1"

    # If neither Token Factory nor NVIDIA keys are available, use Fixture service
    if not tf_key and not nvidia_ultra_key and not nvidia_fast_key:
        return FixtureAIService()

    # --------------------------------------------------------------------------
    # Fallback Case: Token Factory Key is NOT found / not configured.
    # Runs exactly as before Token Factory: calls Ultra & Super via NVIDIA NIM.
    # --------------------------------------------------------------------------
    if not tf_key:
        primary_key = nvidia_ultra_key or nvidia_fast_key
        fast_key = nvidia_fast_key or nvidia_ultra_key

        primary_client = NebiusClient(
            api_key=primary_key,
            model_id=model_id,
            base_url=nvidia_base_url,
        )
        fast_client = None
        if fast_key:
            fast_client = NebiusClient(
                api_key=fast_key,
                model_id=fast_model_id,
                base_url=nvidia_base_url,
            )
        return LiveAIService(primary_client, fast_client=fast_client)

    # --------------------------------------------------------------------------
    # Token Factory Case: Token Factory Key IS found.
    # Targets Token Factory with transparent runtime fallback to NVIDIA NIM.
    # --------------------------------------------------------------------------
    primary_client = NebiusClient(
        api_key=tf_key,
        model_id=model_id,
        base_url=tf_base_url,
        fallback_api_key=nvidia_ultra_key or None,
        fallback_base_url=nvidia_base_url,
    )

    fast_client = NebiusClient(
        api_key=tf_key,
        model_id=fast_model_id,
        base_url=tf_base_url,
        fallback_api_key=nvidia_fast_key or nvidia_ultra_key or None,
        fallback_base_url=nvidia_base_url,
    )

    return LiveAIService(primary_client, fast_client=fast_client)
