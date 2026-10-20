"""
WS3 Schemas Module.
Re-exports canonical Contract v0.2 models from contracts.schemas and defines
WS3-internal telemetry and counterparty verification models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from contracts.schemas import (
    ContractModel,
    CulturalAffinity,
    DimensionAssessment,
    DimensionLabel,
    ErrorCode,
    EvidenceItem,
    EvidenceSourceType,
    FactUsed,
    HypothesisSignal,
    InsightOptions,
    IntegrationState,
    Lead,
    LeadAssessment,
    LeadCandidate,
    LeadLocation,
    LeadReviewStatus,
    LeadScores,
    LeadTier,
    MarketHypothesis,
    MarketHypothesisStatus,
    OutreachDraft,
    OutreachDraftStatus,
    PriceSegment,
    Product,
    ProductAttributes,
    ProductInput,
    ProvenanceTag,
    ResearchPlan,
    TasteAnchor,
    TasteAnchorSource,
    TasteAnchorStatus,
    TasteEntity,
    TasteSignal,
)


class AICallLog(ContractModel):
    """Structured telemetry record for every LLM invocation (WS3 Sec 3.2)."""

    task: str
    model_id: str
    prompt_version: str = "v1.0"
    latency_ms: int
    validation_ok: bool
    tokens_in: int | None = None
    tokens_out: int | None = None
    error_code: str | None = None
    run_id: UUID | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AccountStructureType(str, Enum):
    INDIVIDUAL_BUSINESS = "individual_business"
    MULTI_BRAND_PROPRIETOR = "multi_brand_proprietor"
    ARTISAN_COOPERATIVE_NODAL = "artisan_cooperative_nodal"


class HistoricalIncidentType(str, Enum):
    CLEAN = "clean"
    OPERATIONAL_DISPUTE = "operational_dispute"
    HARD_FRAUD = "hard_fraud"


class ExistingBusinessRecord(ContractModel):
    business_id: str
    legal_business_name: str
    trade_name: str
    category: str
    bank_account_hash: str
    tax_id_hash: str
    device_fingerprint_hash: str
    workshop_pincode: str
    workshop_address: str
    product_image_phashes: list[str] = Field(default_factory=list)
    incident_status: HistoricalIncidentType = HistoricalIncidentType.CLEAN


class SellerVerificationInput(ContractModel):
    legal_business_name: str
    trade_name: str
    proprietor_name: str
    category: str
    account_structure: AccountStructureType = AccountStructureType.INDIVIDUAL_BUSINESS
    pan_number: str
    gstin: str
    iec_code: str
    bank_account_number: str
    bank_ifsc: str
    bank_account_holder_name: str
    workshop_address: str
    workshop_pincode: str
    device_fingerprint_hash: str
    product_image_phashes: list[str] = Field(default_factory=list)
    liveness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    face_match_similarity: float = Field(default=1.0, ge=0.0, le=1.0)


class SellerTrustVerdict(ContractModel):
    is_allowed_to_trade: bool
    trust_tier: str  # "verified" | "ring_fenced_escrow" | "needs_manual_review" | "blocked_phoenix_clone"
    shared_account_detected: bool
    linked_business_ids: list[str] = Field(default_factory=list)
    contagion_score: float = Field(default=0.0, ge=0.0, le=100.0)
    upfront_payout_allowed_pct: int
    shipment_verified_payout_pct: int
    delivery_payout_pct: int
    reasons: list[str] = Field(default_factory=list)


class ShipmentMilestoneCheckInput(ContractModel):
    order_id: str
    carrier_name: str
    tracking_or_bl_number: str
    carrier_reported_status: str  # e.g., "LABEL_CREATED", "IN_TRANSIT", "DELIVERED"
    origin_city: str
    expected_origin_city: str
    destination_country: str
    expected_destination_country: str
    reported_weight_kg: float
    expected_min_weight_kg: float


class ShipmentMilestoneVerdict(ContractModel):
    milestone_verified: bool
    release_tranche_pct: int
    status_summary: str
    warnings: list[str] = Field(default_factory=list)


__all__ = [
    "AICallLog",
    "AccountStructureType",
    "ContractModel",
    "CulturalAffinity",
    "DimensionAssessment",
    "DimensionLabel",
    "ErrorCode",
    "EvidenceItem",
    "EvidenceSourceType",
    "ExistingBusinessRecord",
    "FactUsed",
    "HistoricalIncidentType",
    "HypothesisSignal",
    "InsightOptions",
    "IntegrationState",
    "Lead",
    "LeadAssessment",
    "LeadCandidate",
    "LeadLocation",
    "LeadReviewStatus",
    "LeadScores",
    "LeadTier",
    "MarketHypothesis",
    "MarketHypothesisStatus",
    "OutreachDraft",
    "OutreachDraftStatus",
    "PriceSegment",
    "Product",
    "ProductAttributes",
    "ProductInput",
    "ProvenanceTag",
    "ResearchPlan",
    "SellerTrustVerdict",
    "SellerVerificationInput",
    "ShipmentMilestoneCheckInput",
    "ShipmentMilestoneVerdict",
    "TasteAnchor",
    "TasteAnchorSource",
    "TasteAnchorStatus",
    "TasteEntity",
    "TasteSignal",
]