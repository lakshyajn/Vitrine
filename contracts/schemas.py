"""
Contracts Schemas (v0.2)
Shared Pydantic v2 data models, enumerations, and error envelopes.
Strictly snake_case.
Precedence: Rank 1 in AGENT.md Section 0.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ==============================================================================
# 1. Enumerations (AGENT.md Section 4.1 & WS2_Spec Appendix A.2)
# ==============================================================================

class ResearchRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchRunStage(str, Enum):
    PLANNING = "planning"
    ANCHOR_PROPOSAL = "anchor_proposal"
    ANCHOR_REVIEW = "anchor_review"
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"
    SCORING = "scoring"
    DONE = "done"


class LeadReviewStatus(str, Enum):
    NEW = "new"
    SAVED = "saved"
    REJECTED = "rejected"
    CONTACTED = "contacted"


class LeadTier(str, Enum):
    QUALIFIED = "qualified"
    NEEDS_REVIEW = "needs_review"
    UNQUALIFIED = "unqualified"


class RetailerKind(str, Enum):
    RETAILER = "retailer"
    MAKER_BRAND = "maker_brand"
    MARKETPLACE = "marketplace"
    MEDIA_REFERENCE = "media_reference"
    INSTITUTION = "institution"
    OTHER = "other"
    UNKNOWN = "unknown"


class SellsCategoryAnswer(str, Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class OutreachDraftStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    CONTACTED = "contacted"


class TasteAnchorStatus(str, Enum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class TasteAnchorSource(str, Enum):
    AI_PROPOSED = "ai_proposed"
    USER_ADDED = "user_added"
    QLOO = "qloo"
    DEMO = "demo"


class MarketHypothesisStatus(str, Enum):
    # DECISION-D13
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class DimensionLabel(str, Enum):
    # DECISION-D14: Strictly high | medium | low | unknown across all 3 dimensions
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"

    @classmethod
    def from_str_defensive(cls, val: str | None) -> DimensionLabel:
        if not val:
            return cls.UNKNOWN
        v = val.strip().lower()
        if v in ("high", "match"):
            return cls.HIGH
        if v in ("medium", "adjacent"):
            return cls.MEDIUM
        if v in ("low", "mismatch"):
            return cls.LOW
        if v == "unknown":
            return cls.UNKNOWN
        return cls.UNKNOWN

    def to_score(self) -> float | None:
        """Map dimension label to deterministic score (0-100) or None."""
        if self == DimensionLabel.HIGH:
            return 100.0
        if self == DimensionLabel.MEDIUM:
            return 60.0
        if self == DimensionLabel.LOW:
            return 20.0
        return None  # UNKNOWN strictly maps to None, never 0


class EvidenceSourceType(str, Enum):
    OFFICIAL_SITE = "official_site"
    PRODUCT_PAGE = "product_page"
    SOCIAL = "social"
    DIRECTORY = "directory"
    PRESS = "press"
    MARKETPLACE = "marketplace"
    OTHER = "other"


class ProvenanceTag(str, Enum):
    VERIFIED_FACT = "verified_fact"
    AI_ASSESSMENT = "ai_assessment"
    UNKNOWN = "unknown"
    DEMO_DATA = "demo_data"


class IntegrationState(str, Enum):
    # DECISION-D1
    LIVE = "live"
    MOCK = "mock"
    PENDING = "pending"
    DISABLED = "disabled"


class PriceSegment(str, Enum):
    BUDGET = "budget"
    MID = "mid"
    MID_PREMIUM = "mid_premium"
    PREMIUM = "premium"
    LUXURY = "luxury"


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    UPSTREAM_TIMEOUT = "upstream_timeout"
    UPSTREAM_UNAVAILABLE = "upstream_unavailable"
    AI_OUTPUT_INVALID = "ai_output_invalid"
    RATE_LIMITED = "rate_limited"
    INTERNAL_ERROR = "internal_error"


# ==============================================================================
# 2. Base Configuration & Error Envelope
# ==============================================================================

class ContractModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        extra="ignore",
    )


class ErrorDetail(ContractModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None
    request_id: str = Field(default_factory=lambda: str(uuid4()))


class ErrorEnvelope(ContractModel):
    error: ErrorDetail


# ==============================================================================
# 3. Core Data Models
# ==============================================================================

class Profile(ContractModel):
    # DECISION-D16
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    business_name: str
    country: str | None = None
    website: str | None = None
    contact_email: str | None = None
    about: str | None = None
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class Product(ContractModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID
    name: str
    category: str
    description: str
    materials: list[str] = Field(default_factory=list)
    style: list[str] = Field(default_factory=list)
    motifs: list[str] = Field(default_factory=list)
    colours: list[str] = Field(default_factory=list)
    price_segment: PriceSegment = PriceSegment.MID_PREMIUM
    price_min: float | None = None
    price_max: float | None = None
    currency: str = "USD"
    moq: int = Field(default=1, ge=1)
    monthly_capacity: int | None = None
    target_retailer_types: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)  # DECISION-D18
    is_demo: bool = False
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    @model_validator(mode="after")
    def validate_price_range(self) -> Product:
        if self.price_min is not None and self.price_max is not None:
            if self.price_min > self.price_max:
                raise ValueError("price_min must be <= price_max")
        return self


class ProductInput(ContractModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    materials: list[str] = Field(default_factory=list)
    style: list[str] = Field(default_factory=list)
    motifs: list[str] = Field(default_factory=list)
    colours: list[str] = Field(default_factory=list)
    price_segment: PriceSegment | None = None
    price_min: float | None = None
    price_max: float | None = None
    currency: str = "USD"
    moq: int = Field(default=1, ge=1)
    monthly_capacity: int | None = None
    target_retailer_types: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)


class ProductAttributes(ContractModel):
    # DECISION-D19: Task A output
    style: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    motifs: list[str] = Field(default_factory=list)
    colours: list[str] = Field(default_factory=list)
    price_segment: PriceSegment | None = None
    target_retailer_types: list[str] = Field(default_factory=list)
    uncertain_fields: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    # Optional fields extracted if mentioned in text
    category: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    currency: str | None = None
    moq: int | None = None
    monthly_capacity: int | None = None


class ResearchPlan(ContractModel):
    target_regions: list[str] = Field(default_factory=list)
    target_retailer_types: list[str] = Field(default_factory=list)
    aesthetic_candidates: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)
    taste_relevance: str | None = "applicable"
    taste_relevance_reason: str | None = None
    hypotheses_rationale: str | None = None
    notes: str | None = None


class ResearchRunInputs(ContractModel):
    regions: list[str] = Field(default_factory=list)
    retailer_types: list[str] = Field(default_factory=list)
    notes: str | None = None
    anchor_ids: list[UUID] = Field(default_factory=list)


class ProviderModes(ContractModel):
    # DECISION-D1
    taste: IntegrationState = IntegrationState.MOCK
    search: IntegrationState = IntegrationState.MOCK
    ai: IntegrationState = IntegrationState.MOCK


class RunError(ContractModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None


class ResearchRun(ContractModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID | None = None
    product_id: UUID
    status: ResearchRunStatus = ResearchRunStatus.QUEUED
    stage: ResearchRunStage = ResearchRunStage.PLANNING
    inputs: ResearchRunInputs = Field(default_factory=ResearchRunInputs)
    plan: ResearchPlan | None = None
    error: RunError | None = None
    provider_modes: ProviderModes = Field(default_factory=ProviderModes)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    heartbeat_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utc_now)  # DECISION-D20


class TasteAnchor(ContractModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID | None = None
    run_id: UUID
    label: str
    entity_type: str = "brand"
    external_id: str | None = None
    source: TasteAnchorSource = TasteAnchorSource.AI_PROPOSED
    status: TasteAnchorStatus = TasteAnchorStatus.PROPOSED
    rationale: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_demo: bool = True


class HypothesisSignal(ContractModel):
    type: str
    text: str
    source: str
    source_ref: str | None = None
    is_demo: bool = True


class MarketHypothesis(ContractModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID | None = None
    run_id: UUID
    title: str
    rationale: str | None = None
    region_hint: str | None = None
    signals: list[HypothesisSignal] = Field(default_factory=list)
    status: MarketHypothesisStatus = MarketHypothesisStatus.PROPOSED  # DECISION-D13


class CulturalAffinity(ContractModel):
    # Contract v0.2 Appendix A.3
    provider: str = "mock"
    is_demo: bool = True
    retrieved_at: datetime = Field(default_factory=_utc_now)
    anchor_ids: list[UUID] = Field(default_factory=list)
    signals: list[dict[str, Any]] = Field(default_factory=list)


class LeadLocation(ContractModel):
    city: str | None = None
    region: str | None = None
    country: str | None = None


class LeadScores(ContractModel):
    # CRITICAL: Dimension scores are nullable float | None = None (NEVER default to 0)
    category_fit: float | None = None
    aesthetic_fit: float | None = None
    evidence_quality: float | None = None
    seller_compat: float | None = None
    overall: float | None = None
    completeness: float | None = None
    tier_reasons: list[str] = Field(default_factory=list)  # DECISION-D6


class DimensionAssessment(ContractModel):
    label: DimensionLabel
    reasons: list[str] = Field(default_factory=list)
    evidence_ids: list[UUID] = Field(default_factory=list)

    @field_validator("label", mode="before")
    @classmethod
    def parse_defensive_label(cls, v: Any) -> Any:
        if isinstance(v, str):
            return DimensionLabel.from_str_defensive(v)
        return v


class LeadAssessment(ContractModel):
    category_fit: DimensionAssessment
    aesthetic_fit: DimensionAssessment
    seller_compat: DimensionAssessment
    retailer_kind: RetailerKind | None = None
    retailer_kind_reasons: list[str] = Field(default_factory=list)
    retailer_kind_evidence_ids: list[UUID] = Field(default_factory=list)
    sells_product_category: SellsCategoryAnswer | None = None
    sells_product_category_reasons: list[str] = Field(default_factory=list)
    sells_product_category_evidence_ids: list[UUID] = Field(default_factory=list)
    summary: str
    unknowns: list[str] = Field(default_factory=list)
    model_id: str | None = None
    generated_at: datetime = Field(default_factory=_utc_now)


class EvidenceItem(ContractModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID | None = None
    lead_id: UUID
    url: str
    excerpt: str
    source_type: EvidenceSourceType = EvidenceSourceType.OFFICIAL_SITE
    retrieved_at: datetime = Field(default_factory=_utc_now)
    published_at: datetime | None = None
    domain_matches_lead: bool = True
    provenance: ProvenanceTag = ProvenanceTag.VERIFIED_FACT
    is_demo: bool = False  # DECISION-D1


class Lead(ContractModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID | None = None
    run_id: UUID
    product_id: UUID
    name: str
    website: str
    canonical_domain: str
    location: LeadLocation | None = None
    retailer_kind: RetailerKind | None = None
    retailer_type: str | None = None
    website_verified: bool = False
    website_checked_at: datetime | None = None
    tier: LeadTier = LeadTier.NEEDS_REVIEW
    scores: LeadScores = Field(default_factory=LeadScores)
    assessment: LeadAssessment | None = None
    cultural_affinity: CulturalAffinity | None = None
    review_status: LeadReviewStatus = LeadReviewStatus.NEW
    notes: str | None = None
    duplicate_of: UUID | None = None
    contact_email: str | None = None
    is_demo: bool = False  # DECISION-D1
    created_at: datetime = Field(default_factory=_utc_now)  # DECISION-D20


class LeadCandidate(ContractModel):
    name: str
    website: str
    canonical_domain: str
    location: LeadLocation | None = None
    retailer_kind: RetailerKind | None = None
    retailer_type: str | None = None
    website_verified: bool = False
    evidence: list[EvidenceItem] = Field(default_factory=list)
    possible_duplicate_of_domain: str | None = None  # DECISION-D9
    contact_email: str | None = None


class FactUsed(ContractModel):
    fact_id: str
    text: str
    source_url: str | None = None


class OutreachDraft(ContractModel):
    id: UUID = Field(default_factory=uuid4)
    owner_id: UUID | None = None
    lead_id: UUID
    product_id: UUID
    version: int = 1
    subject: str
    body: str
    facts_used: list[FactUsed] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)  # DECISION-D5
    status: OutreachDraftStatus = OutreachDraftStatus.DRAFT
    followup_notes: str | None = None
    parent_draft_id: UUID | None = None  # DECISION-D20
    is_demo: bool = False  # DECISION-D1
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)  # DECISION-D20


# ==============================================================================
# 4. Service and Provider Types (WS3 Interfaces / Appendix A.6)
# ==============================================================================

class TasteEntity(ContractModel):
    id: str
    name: str
    entity_type: str = "brand"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TasteSignal(ContractModel):
    type: str
    text: str
    source: str
    source_ref: str | None = None
    score: float | None = None
    raw: dict[str, Any] | None = None


class InsightOptions(ContractModel):
    entity_type: str | None = None
    max_results: int = 10


class LeadPagedResponse(ContractModel):
    # DECISION-D7
    items: list[Lead]
    total: int
    page: int
    page_size: int


# ==============================================================================
# 5. Request & Update Payloads for API Endpoints (Section 4.3 / Appendix A.4)
# ==============================================================================

class ProfileUpdate(ContractModel):
    # DECISION-D16
    business_name: str | None = None
    country: str | None = None
    website: str | None = None
    contact_email: str | None = None
    about: str | None = None


class ProductCreate(ContractModel):
    name: str
    category: str
    description: str
    materials: list[str] = Field(default_factory=list)
    style: list[str] = Field(default_factory=list)
    motifs: list[str] = Field(default_factory=list)
    colours: list[str] = Field(default_factory=list)
    price_segment: PriceSegment = PriceSegment.MID_PREMIUM
    price_min: float | None = None
    price_max: float | None = None
    currency: str = "USD"
    moq: int = Field(default=1, ge=1)
    monthly_capacity: int | None = None
    target_retailer_types: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    is_demo: bool = False

    @model_validator(mode="after")
    def validate_price_range(self) -> ProductCreate:
        if self.price_min is not None and self.price_max is not None:
            if self.price_min > self.price_max:
                raise ValueError("price_min must be <= price_max")
        return self


class ProductUpdate(ContractModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    materials: list[str] | None = None
    style: list[str] | None = None
    motifs: list[str] | None = None
    colours: list[str] | None = None
    price_segment: PriceSegment | None = None
    price_min: float | None = None
    price_max: float | None = None
    currency: str | None = None
    moq: int | None = Field(default=None, ge=1)
    monthly_capacity: int | None = None
    target_retailer_types: list[str] | None = None
    images: list[str] | None = None
    is_demo: bool | None = None

    @model_validator(mode="after")
    def validate_price_range(self) -> ProductUpdate:
        if self.price_min is not None and self.price_max is not None:
            if self.price_min > self.price_max:
                raise ValueError("price_min must be <= price_max")
        return self


class ExtractProfileRequest(ContractModel):
    description: str
    known: ProductInput | None = None


class CreateResearchRunRequest(ContractModel):
    product_id: UUID
    inputs: ResearchRunInputs = Field(default_factory=ResearchRunInputs)


class ResearchRunActionResponse(ContractModel):
    id: UUID
    status: ResearchRunStatus


class CreateAnchorRequest(ContractModel):
    # DECISION-D3
    label: str
    entity_type: str = "brand"
    rationale: str | None = None


class UpdateAnchorRequest(ContractModel):
    label: str | None = None
    entity_type: str | None = None
    status: TasteAnchorStatus | None = None
    rationale: str | None = None


class ConfirmAnchorsRequest(ContractModel):
    # DECISION-D4
    proceed_without_anchors: bool = False


class UpdateLeadRequest(ContractModel):
    review_status: LeadReviewStatus | None = None
    notes: str | None = None
    contact_email: str | None = None


class ContactScrapeResult(ContractModel):
    lead_id: UUID
    email: str
    source: str
    source_url: str | None = None
    is_fallback: bool = False
    confidence: float = 1.0
    all_candidates: list[str] = Field(default_factory=list)


class UpdateOutreachDraftRequest(ContractModel):
    subject: str | None = None
    body: str | None = None
    status: OutreachDraftStatus | None = None
    followup_notes: str | None = None

