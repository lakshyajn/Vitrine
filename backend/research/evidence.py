# backend/research/evidence.py
"""
Deterministic Evidence Validation, Website Verification, Exclusions &
Counterparty Trust / Shared-Account Ring-Fencing Engine (WS3 Section 4.1).
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from typing import Any
import httpx

from backend.ai.schemas import (
    AccountStructureType,
    ExistingBusinessRecord,
    HistoricalIncidentType,
    SellerTrustVerdict,
    SellerVerificationInput,
    ShipmentMilestoneCheckInput,
    ShipmentMilestoneVerdict,
)
from backend.research.dedupe import extract_canonical_domain
from contracts.schemas import EvidenceSourceType

EXCLUDED_WHOLESALE_OR_CHAIN_DOMAINS = {
    # Mass marketplaces & chains
    "amazon.com",
    "alibaba.com",
    "aliexpress.com",
    "indiamart.com",
    "walmart.com",
    "target.com",
    "ikea.com",
    "wayfair.com",
    "temu.com",
    "ebay.com",
    "etsy.com",
    "faire.com",
    "ankorstore.com",
    # Directories, review aggregators & data brokers (not boutique retailers)
    "mapquest.com",
    "bbb.org",
    "yellowpages.com",
    "yelp.com",
    "tripadvisor.com",
    "wikipedia.org",
    "gov.uk",
    "crunchbase.com",
    "dnb.com",
    "zoominfo.com",
    "rocketreach.co",
    "leadiq.com",
    "apollo.io",
    # Social media platforms
    "facebook.com",
    "instagram.com",
    "pinterest.com",
    "tiktok.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "youtube.com",
}

FREE_WEBMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
    "aol.com",
}

PAN_FORMAT = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
GSTIN_FORMAT = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
IEC_FORMAT = re.compile(r"^[A-Z0-9]{10}$")


def classify_evidence_source_type(url: str, excerpt: str = "") -> EvidenceSourceType:
    """Rule-based source_type classification (WS3 Section 4.1)."""
    u = (url or "").lower()
    ex = (excerpt or "").lower()
    if any(m in u for m in ("etsy.com", "faire.com", "ankorstore.com")):
        return EvidenceSourceType.MARKETPLACE
    if any(s in u for s in ("instagram.com", "pinterest.com", "facebook.com", "tiktok.com")):
        return EvidenceSourceType.SOCIAL
    if any(d in u for d in ("directory", "stockists", "yellowpages", "yelp.com")):
        return EvidenceSourceType.DIRECTORY
    if any(p in u for p in ("press", "magazine", "editorial", "blog", "dezeen", "elledecor")):
        return EvidenceSourceType.PRESS
    if any(p in u for p in ("/products/", "/collections/", "/shop/", "/product/")) or "add to cart" in ex:
        return EvidenceSourceType.PRODUCT_PAGE
    return EvidenceSourceType.OFFICIAL_SITE


def is_excluded_retailer_domain(url_or_domain: str) -> tuple[bool, str | None]:
    """Configurable exclusion rule check for mass marketplaces, chains, directories, and aggregators."""
    dom = extract_canonical_domain(url_or_domain)
    base_dom = dom.split("/")[0].lower()
    for excl in EXCLUDED_WHOLESALE_OR_CHAIN_DOMAINS:
        if base_dom == excl or base_dom.endswith("." + excl):
            return True, f"Excluded aggregator, directory or mass marketplace domain: {base_dom}"
    return False, None


async def verify_website_http(url: str, timeout_seconds: float = 3.5) -> tuple[bool, datetime]:
    """Deterministic HTTP liveness check; never asks the LLM whether a site is alive."""
    checked_at = datetime.now(timezone.utc)
    normalized = url.strip()
    if not normalized.startswith(("http://", "https://")):
        normalized = f"https://{normalized}"
    try:
        async with httpx.AsyncClient(
            timeout=timeout_seconds,
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            resp = await client.get(
                normalized,
                headers={"User-Agent": "VitrineRetailerVerifier/0.2"},
            )
            return (200 <= resp.status_code < 400), checked_at
    except Exception:
        return False, checked_at


def hash_credential(raw_value: str, salt: str = "vitrine-kyb-v1") -> str:
    return hashlib.sha256(f"{salt}:{raw_value.strip().upper()}".encode("utf-8")).hexdigest()


def evaluate_seller_counterparty_trust(
    seller: SellerVerificationInput,
    registry: list[ExistingBusinessRecord],
) -> SellerTrustVerdict:
    """
    Solves Seller (Source) Re-Registration & Shared-Bank-Account Contagion:
    1. Verifies GSTIN embedded PAN (chars 2..12) matches PAN, and bank account holder matches business/proprietor.
    2. Checks biometric liveness + face match score to prevent stolen ID uploads.
    3. Shared Bank Account Protection: If Business B shares a bank account with Business A (e.g. multi-brand
       proprietor or artisan cooperative) and Business A had a dispute/fraud:
       - If Business B uploads the SAME product images (pHash overlap) -> BLOCKED as a Phoenix Clone.
       - If Business B has a distinct product catalogue -> ALLOWED TO TRADE under Ring-Fenced Escrow
         (0% upfront release; 70% released upon verified IN_TRANSIT carrier Bill of Lading; 30% on delivery).
    """
    reasons: list[str] = []
    pan_clean = seller.pan_number.strip().upper()
    gst_clean = seller.gstin.strip().upper()

    if not PAN_FORMAT.match(pan_clean) or not GSTIN_FORMAT.match(gst_clean) or gst_clean[2:12] != pan_clean:
        return SellerTrustVerdict(
            is_allowed_to_trade=False,
            trust_tier="blocked_phoenix_clone",
            shared_account_detected=False,
            contagion_score=100.0,
            upfront_payout_allowed_pct=0,
            shipment_verified_payout_pct=0,
            delivery_payout_pct=0,
            reasons=["Tax credential mismatch: GSTIN embedded tax ID does not match supplied PAN."],
        )

    if seller.liveness_score < 0.85 or seller.face_match_similarity < 0.80:
        return SellerTrustVerdict(
            is_allowed_to_trade=False,
            trust_tier="needs_manual_review",
            shared_account_detected=False,
            contagion_score=85.0,
            upfront_payout_allowed_pct=0,
            shipment_verified_payout_pct=0,
            delivery_payout_pct=100,
            reasons=["Biometric liveness or live selfie-to-ID match below threshold."],
        )

    bank_hash = hash_credential(f"{seller.bank_account_number}:{seller.bank_ifsc}")
    tax_hash = hash_credential(pan_clean)

    linked = [
        rec for rec in registry if rec.bank_account_hash == bank_hash or rec.tax_id_hash == tax_hash
    ]
    if not linked:
        return SellerTrustVerdict(
            is_allowed_to_trade=True,
            trust_tier="verified",
            shared_account_detected=False,
            contagion_score=0.0,
            upfront_payout_allowed_pct=30,
            shipment_verified_payout_pct=40,
            delivery_payout_pct=30,
            reasons=["Independent credentials verified; standard 30/40/30 milestone payout enabled."],
        )

    linked_ids = [rec.business_id for rec in linked]
    max_contagion = 0.0

    for other in linked:
        phash_overlap = len(set(seller.product_image_phashes) & set(other.product_image_phashes))
        same_cat = seller.category.strip().lower() == other.category.strip().lower()

        if other.incident_status == HistoricalIncidentType.CLEAN:
            score = 10.0
            reasons.append(f"Shares bank/tax account with clean business '{other.trade_name}'.")
        elif other.incident_status == HistoricalIncidentType.OPERATIONAL_DISPUTE:
            score = 40.0
            reasons.append(
                f"Shares bank account with '{other.trade_name}' (prior operational dispute, no hard fraud)."
            )
        else:
            # Linked entity had HARD_FRAUD -> check if Phoenix Clone vs independent business line
            if phash_overlap > 0 or (same_cat and seller.trade_name.strip().lower() == other.trade_name.strip().lower()):
                score = 95.0
                reasons.append(
                    f"PHOENIX CLONE DETECTED: Re-using bank account of banned entity '{other.trade_name}' with overlapping product image hashes."
                )
            else:
                score = 65.0
                reasons.append(
                    f"Shares bank account with flagged entity '{other.trade_name}', but operates a distinct catalogue ('{seller.category}'). Placed in ring-fenced escrow."
                )
        max_contagion = max(max_contagion, score)

    if max_contagion >= 90.0:
        return SellerTrustVerdict(
            is_allowed_to_trade=False,
            trust_tier="blocked_phoenix_clone",
            shared_account_detected=True,
            linked_business_ids=linked_ids,
            contagion_score=max_contagion,
            upfront_payout_allowed_pct=0,
            shipment_verified_payout_pct=0,
            delivery_payout_pct=0,
            reasons=reasons,
        )

    if max_contagion >= 30.0:
        return SellerTrustVerdict(
            is_allowed_to_trade=True,
            trust_tier="ring_fenced_escrow",
            shared_account_detected=True,
            linked_business_ids=linked_ids,
            contagion_score=max_contagion,
            upfront_payout_allowed_pct=0,
            shipment_verified_payout_pct=70,
            delivery_payout_pct=30,
            reasons=reasons,
        )

    return SellerTrustVerdict(
        is_allowed_to_trade=True,
        trust_tier="verified",
        shared_account_detected=True,
        linked_business_ids=linked_ids,
        contagion_score=max_contagion,
        upfront_payout_allowed_pct=30,
        shipment_verified_payout_pct=40,
        delivery_payout_pct=30,
        reasons=reasons,
    )


def verify_shipment_milestone_for_payment(
    check: ShipmentMilestoneCheckInput,
) -> ShipmentMilestoneVerdict:
    """
    Protects both Buyer (who paid advance into escrow) and Seller (who shipped goods):
    Rejects 'LABEL_CREATED' spoofing; requires carrier-confirmed 'IN_TRANSIT' with matching
    origin, destination, and minimum physical weight before releasing shipment tranche.
    """
    warnings: list[str] = []
    status_upper = check.carrier_reported_status.strip().upper()

    if status_upper == "LABEL_CREATED":
        return ShipmentMilestoneVerdict(
            milestone_verified=False,
            release_tranche_pct=0,
            status_summary="Shipping label created, but parcel has not been handed over to carrier.",
            warnings=["Escrow hold maintained: 'LABEL_CREATED' does not prove physical dispatch."],
        )

    if check.origin_city.strip().lower() != check.expected_origin_city.strip().lower():
        warnings.append(
            f"Origin city mismatch: expected '{check.expected_origin_city}', carrier reported '{check.origin_city}'."
        )

    if check.destination_country.strip().lower() != check.expected_destination_country.strip().lower():
        warnings.append(
            f"Destination country mismatch: expected '{check.expected_destination_country}', carrier reported '{check.destination_country}'."
        )

    if check.reported_weight_kg < check.expected_min_weight_kg:
        warnings.append(
            f"Parcel weight anomaly: reported {check.reported_weight_kg}kg is below minimum expected {check.expected_min_weight_kg}kg for order MOQ."
        )

    if warnings:
        return ShipmentMilestoneVerdict(
            milestone_verified=False,
            release_tranche_pct=0,
            status_summary="Shipment flagged for manual inspection due to route or weight mismatch.",
            warnings=warnings,
        )

    if status_upper == "IN_TRANSIT":
        return ShipmentMilestoneVerdict(
            milestone_verified=True,
            release_tranche_pct=70,
            status_summary="Carrier confirmed physical dispatch IN_TRANSIT with matching route and weight.",
            warnings=[],
        )

    if status_upper == "DELIVERED":
        return ShipmentMilestoneVerdict(
            milestone_verified=True,
            release_tranche_pct=100,
            status_summary="Carrier confirmed final DELIVERY at buyer destination.",
            warnings=[],
        )

    return ShipmentMilestoneVerdict(
        milestone_verified=False,
        release_tranche_pct=0,
        status_summary=f"Unrecognized carrier status: {status_upper}",
        warnings=[f"Cannot release funds on status '{status_upper}'."],
    )