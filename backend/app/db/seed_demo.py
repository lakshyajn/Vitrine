"""
Fixed Demo Scenario Seed Script (Step 9 Part B).
Idempotently seeds demo data with is_demo=True on all entities:
- Profile: "Sample Seller" (small textile workshop)
- 4 Products: Block-printed cotton table runner, cushion cover set, table linen set, throw
  (botanical motifs; terracotta, indigo, ochre colours; mid_premium; MOQ 50; capacity 1500)
- 1 Completed ResearchRun with confirmed TasteAnchors, MarketHypothesis rows,
  3 scored Leads (qualified and needs_review) with EvidenceItems, and 1 OutreachDraft.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import logging
import sys
from typing import Any
from uuid import NAMESPACE_DNS, UUID, uuid5

from sqlalchemy import select

from backend.app.db.models import (
    LeadEvidenceModel,
    LeadModel,
    MarketHypothesisModel,
    OutreachDraftModel,
    ProductModel,
    ProfileModel,
    ResearchRunModel,
    TasteAnchorModel,
)
from backend.app.db.session import async_session_maker, init_db

logger = logging.getLogger(__name__)

DEFAULT_DEMO_OWNER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _gen_id(owner_id: UUID, key: str) -> UUID:
    """Generate a deterministic UUID from owner_id and unique key for idempotency."""
    return uuid5(NAMESPACE_DNS, f"{owner_id}:{key}")


async def seed_demo_data(session: Any, owner_id: UUID) -> dict[str, Any]:
    """
    Idempotently seeds the Fixed Demo Scenario into the database.
    Ensures is_demo=True on every created/updated model.
    """
    now = datetime.now(timezone.utc)

    # 1. Profile: Sample Seller
    profile_stmt = select(ProfileModel).where(ProfileModel.user_id == owner_id)
    profile = (await session.execute(profile_stmt)).scalar_one_or_none()
    if profile is None:
        profile = ProfileModel(
            id=_gen_id(owner_id, "profile"),
            user_id=owner_id,
            business_name="Sample Seller",
            country="India",
            website="https://sampleseller.test",
            contact_email="artisan@sampleseller.test",
            about="Small textile workshop specializing in heritage hand block-printed botanical home textiles.",
            created_at=now,
            updated_at=now,
        )
        session.add(profile)
    else:
        profile.business_name = "Sample Seller"
        profile.country = "India"
        profile.website = "https://sampleseller.test"
        profile.contact_email = "artisan@sampleseller.test"
        profile.about = "Small textile workshop specializing in heritage hand block-printed botanical home textiles."
        profile.updated_at = now

    await session.flush()

    # 2. 4 Products (mid_premium, MOQ 50, capacity 1500, botanical motifs, terracotta/indigo/ochre)
    product_specs = [
        {
            "name": "Block-printed cotton table runner",
            "category": "Home Textiles",
            "description": "Handcrafted block-printed cotton table runner featuring botanical motifs dyed with terracotta, indigo, and ochre pigments.",
            "price_min": 28.0,
            "price_max": 45.0,
        },
        {
            "name": "Cushion cover set",
            "category": "Home Textiles",
            "description": "Set of 2 hand block-printed cushion covers in heritage botanical motifs with natural terracotta and indigo accents.",
            "price_min": 35.0,
            "price_max": 60.0,
        },
        {
            "name": "Table linen set",
            "category": "Home Textiles",
            "description": "Artisan table linen set consisting of napkins and placemats with delicate ochre and indigo floral block prints.",
            "price_min": 45.0,
            "price_max": 85.0,
        },
        {
            "name": "Throw",
            "category": "Home Textiles",
            "description": "Hand-spun woven cotton throw with block-printed botanical borders and fringe detailing.",
            "price_min": 55.0,
            "price_max": 110.0,
        },
    ]

    seeded_products: list[ProductModel] = []
    for spec in product_specs:
        prod_id = _gen_id(owner_id, f"product:{spec['name']}")
        prod_stmt = select(ProductModel).where(ProductModel.id == prod_id)
        prod = (await session.execute(prod_stmt)).scalar_one_or_none()
        if prod is None:
            prod = ProductModel(
                id=prod_id,
                owner_id=owner_id,
                name=spec["name"],
                category=spec["category"],
                description=spec["description"],
                materials=["Cotton", "Linen"],
                style=["Artisan", "Heritage"],
                motifs=["botanical motifs"],
                colours=["terracotta", "indigo", "ochre"],
                price_segment="mid_premium",
                price_min=spec["price_min"],
                price_max=spec["price_max"],
                currency="USD",
                moq=50,
                monthly_capacity=1500,
                target_retailer_types=["boutique", "concept_store"],
                images=[],
                is_demo=True,
                created_at=now,
                updated_at=now,
            )
            session.add(prod)
        else:
            prod.name = spec["name"]
            prod.category = spec["category"]
            prod.description = spec["description"]
            prod.materials = ["Cotton", "Linen"]
            prod.style = ["Artisan", "Heritage"]
            prod.motifs = ["botanical motifs"]
            prod.colours = ["terracotta", "indigo", "ochre"]
            prod.price_segment = "mid_premium"
            prod.price_min = spec["price_min"]
            prod.price_max = spec["price_max"]
            prod.moq = 50
            prod.monthly_capacity = 1500
            prod.is_demo = True
            prod.updated_at = now
        seeded_products.append(prod)

    await session.flush()
    primary_product = seeded_products[0]

    # 3. 1 Completed ResearchRun
    run_id = _gen_id(owner_id, "demo-run-1")
    run_stmt = select(ResearchRunModel).where(ResearchRunModel.id == run_id)
    run = (await session.execute(run_stmt)).scalar_one_or_none()
    if run is None:
        run = ResearchRunModel(
            id=run_id,
            owner_id=owner_id,
            product_id=primary_product.id,
            status="completed",
            stage="done",
            inputs={
                "regions": ["Western Europe", "North America"],
                "retailer_types": ["boutique", "concept_store"],
                "notes": "Discovery for premium botanical handcrafted home textiles.",
                "demo_scenario": "fixed_demo",
            },
            plan={
                "target_regions": ["Western Europe"],
                "aesthetic_candidates": ["Block Print Aesthetic", "Artisan Home Decor"],
                "hypotheses_rationale": "High cultural affinity for artisan textiles in Western Europe design boutiques.",
            },
            provider_modes={"taste": "mock", "search": "mock", "ai": "mock"},
            started_at=now,
            finished_at=now,
            heartbeat_at=now,
            active_elapsed_seconds=45,
            created_at=now,
        )
        session.add(run)
    else:
        run.product_id = primary_product.id
        run.status = "completed"
        run.stage = "done"
        run.provider_modes = {"taste": "mock", "search": "mock", "ai": "mock"}

    await session.flush()

    # 4. Confirmed Taste Anchors
    anchor_specs = [
        {
            "label": "Block Print Aesthetic",
            "entity_type": "brand",
            "external_id": "demo-entity-block-print-aesthetic",
            "rationale": "Heritage block printing aligns with boutique aesthetic.",
        },
        {
            "label": "Artisan Home Decor",
            "entity_type": "brand",
            "external_id": "demo-entity-artisan-home-decor",
            "rationale": "High alignment with handcrafted textile stockists.",
        },
    ]

    seeded_anchors: list[TasteAnchorModel] = []
    for aspec in anchor_specs:
        aid = _gen_id(owner_id, f"anchor:{aspec['label']}")
        astmt = select(TasteAnchorModel).where(TasteAnchorModel.id == aid)
        anchor = (await session.execute(astmt)).scalar_one_or_none()
        if anchor is None:
            anchor = TasteAnchorModel(
                id=aid,
                owner_id=owner_id,
                run_id=run.id,
                label=aspec["label"],
                entity_type=aspec["entity_type"],
                external_id=aspec["external_id"],
                source="demo",
                status="confirmed",
                rationale=aspec["rationale"],
                metadata_json={"category": "Home Decor & Living", "is_demo": True},
                is_demo=True,
                created_at=now,
            )
            session.add(anchor)
        else:
            anchor.status = "confirmed"
            anchor.is_demo = True
        seeded_anchors.append(anchor)

    await session.flush()

    # 5. Market Hypothesis rows
    hypo_id = _gen_id(owner_id, "hypo:western-europe")
    hypo_stmt = select(MarketHypothesisModel).where(MarketHypothesisModel.id == hypo_id)
    hypo = (await session.execute(hypo_stmt)).scalar_one_or_none()
    if hypo is None:
        hypo = MarketHypothesisModel(
            id=hypo_id,
            owner_id=owner_id,
            run_id=run.id,
            title="Independent Retailer Affinity in Western Europe",
            rationale="Target boutique stockists in Western Europe demonstrate cultural alignment with artisanal textiles.",
            region_hint="Western Europe",
            status="confirmed",
            signals=[
                {
                    "type": "affinity_trend",
                    "text": "High cultural affinity between artisan textiles and independent design boutiques for demo-entity-block-print-aesthetic.",
                    "source": "mock",
                    "source_ref": "demo-call-1",
                    "is_demo": True,
                }
            ],
            created_at=now,
        )
        session.add(hypo)
    else:
        hypo.status = "confirmed"

    await session.flush()

    # 6. 3 Scored Leads (qualified and needs_review)
    lead_specs = [
        {
            "name": "Maison & Objet Boutique",
            "website": "https://maison-objet-boutique.test",
            "canonical_domain": "maison-objet-boutique.test",
            "tier": "qualified",
            "city": "Paris",
            "region": "Western Europe",
            "country": "France",
            "retailer_type": "boutique",
            "scores": {
                "category_fit": 0.92,
                "aesthetic_fit": 0.88,
                "evidence_quality": 0.85,
                "seller_compat": 0.82,
                "overall": 0.87,
                "completeness": 0.90,
                "tier_reasons": ["High category and aesthetic alignment with verified independent boutique stockist evidence."],
            },
            "assessment": {
                "category_fit": {
                    "label": "high",
                    "reasons": ["Strong stockist history for artisan textiles", "Dedicated home accessories section"],
                    "evidence_ids": [],
                },
                "aesthetic_fit": {
                    "label": "high",
                    "reasons": ["Botanical motif curation aligns with interior textiles collection"],
                    "evidence_ids": [],
                },
                "seller_compat": {
                    "label": "high",
                    "reasons": ["Independent boutique scale matches workshop capacity"],
                    "evidence_ids": [],
                },
                "summary": "Premier Parisian concept boutique specializing in handcrafted interior textiles.",
                "unknowns": [],
            },
            "cultural_affinity": {
                "provider": "mock",
                "is_demo": True,
                "retrieved_at": now.isoformat(),
                "anchor_ids": [str(seeded_anchors[0].id)],
                "signals": [
                    {
                        "type": "affinity_trend",
                        "text": "High cultural affinity between artisan textiles and independent design boutiques for demo-entity-block-print-aesthetic.",
                        "source_ref": "demo-call-1",
                    }
                ],
            },
            "evidence_url": "https://maison-objet-boutique.test/about",
            "evidence_excerpt": "Maison & Objet curates independent design and handcrafted home decor collections.",
        },
        {
            "name": "Atelier Living Concept",
            "website": "https://atelier-living-concept.test",
            "canonical_domain": "atelier-living-concept.test",
            "tier": "qualified",
            "city": "London",
            "region": "Western Europe",
            "country": "United Kingdom",
            "retailer_type": "concept_store",
            "scores": {
                "category_fit": 0.86,
                "aesthetic_fit": 0.84,
                "evidence_quality": 0.80,
                "seller_compat": 0.78,
                "overall": 0.82,
                "completeness": 0.85,
                "tier_reasons": ["Verified lifestyle retailer stocking small-batch ethical makers."],
            },
            "assessment": {
                "category_fit": {
                    "label": "high",
                    "reasons": ["Design-led showroom featuring sustainable textile and home decor collections"],
                    "evidence_ids": [],
                },
                "aesthetic_fit": {
                    "label": "high",
                    "reasons": ["Focus on sustainable dyes and ethical workshop aesthetics"],
                    "evidence_ids": [],
                },
                "seller_compat": {
                    "label": "medium",
                    "reasons": ["Verified lifestyle retailer stocking small-batch ethical makers"],
                    "evidence_ids": [],
                },
                "summary": "Design-led London showroom featuring sustainable textile and home decor collections.",
                "unknowns": [],
            },
            "cultural_affinity": {
                "provider": "mock",
                "is_demo": True,
                "retrieved_at": now.isoformat(),
                "anchor_ids": [str(seeded_anchors[1].id)],
                "signals": [
                    {
                        "type": "affinity_trend",
                        "text": "High cultural affinity between artisan textiles and independent design boutiques for demo-entity-artisan-home-decor.",
                        "source_ref": "demo-call-2",
                    }
                ],
            },
            "evidence_url": "https://atelier-living-concept.test/designers",
            "evidence_excerpt": "We champion global heritage textiles crafted with eco-friendly natural dyes.",
        },
        {
            "name": "Galerie Moderne Living",
            "website": "https://galerie-moderne-living.test",
            "canonical_domain": "galerie-moderne-living.test",
            "tier": "needs_review",
            "city": "Berlin",
            "region": "Western Europe",
            "country": "Germany",
            "retailer_type": "boutique",
            "scores": {
                "category_fit": 0.70,
                "aesthetic_fit": 0.65,
                "evidence_quality": 0.60,
                "seller_compat": 0.55,
                "overall": 0.63,
                "completeness": 0.70,
                "tier_reasons": ["Moderate aesthetic overlap; wholesale MOQ policy requires manual verification."],
            },
            "assessment": {
                "category_fit": {
                    "label": "medium",
                    "reasons": ["Contemporary European interior store with selective textile offerings"],
                    "evidence_ids": [],
                },
                "aesthetic_fit": {
                    "label": "medium",
                    "reasons": ["Carries niche artisanal brands and selected hand-dyed textile accents"],
                    "evidence_ids": [],
                },
                "seller_compat": {
                    "label": "low",
                    "reasons": ["Uncertain wholesale terms; MOQ policy requires verification"],
                    "evidence_ids": [],
                },
                "summary": "Contemporary European interior store with selective textile offerings.",
                "unknowns": ["Buyer contact email not verified"],
            },
            "cultural_affinity": None,
            "evidence_url": "https://galerie-moderne-living.test/collections",
            "evidence_excerpt": "Featuring European design objects and selected hand-dyed textile accents.",
        },
    ]

    seeded_leads: list[LeadModel] = []
    for lspec in lead_specs:
        lid = _gen_id(owner_id, f"lead:{lspec['canonical_domain']}")
        lstmt = select(LeadModel).where(LeadModel.id == lid)
        lead = (await session.execute(lstmt)).scalar_one_or_none()
        if lead is None:
            lead = LeadModel(
                id=lid,
                owner_id=owner_id,
                run_id=run.id,
                product_id=primary_product.id,
                name=lspec["name"],
                website=lspec["website"],
                canonical_domain=lspec["canonical_domain"],
                location={
                    "city": lspec["city"],
                    "region": lspec["region"],
                    "country": lspec["country"],
                },
                retailer_type=lspec["retailer_type"],
                website_verified=True,
                website_checked_at=now,
                tier=lspec["tier"],
                scores=lspec["scores"],
                assessment=lspec["assessment"],
                cultural_affinity=lspec["cultural_affinity"],
                review_status="new",
                notes=None,
                duplicate_of=None,
                is_demo=True,
                created_at=now,
                updated_at=now,
            )
            session.add(lead)
        else:
            lead.tier = lspec["tier"]
            lead.scores = lspec["scores"]
            lead.assessment = lspec["assessment"]
            lead.cultural_affinity = lspec["cultural_affinity"]
            lead.is_demo = True
            lead.updated_at = now

        seeded_leads.append(lead)

        # Evidence for this lead
        ev_id = _gen_id(owner_id, f"evidence:{lspec['canonical_domain']}")
        ev_stmt = select(LeadEvidenceModel).where(LeadEvidenceModel.id == ev_id)
        ev = (await session.execute(ev_stmt)).scalar_one_or_none()
        if ev is None:
            ev = LeadEvidenceModel(
                id=ev_id,
                owner_id=owner_id,
                lead_id=lid,
                url=lspec["evidence_url"],
                excerpt=lspec["evidence_excerpt"],
                source_type="official_site",
                retrieved_at=now,
                published_at=None,
                domain_matches_lead=True,
                provenance="verified_fact",
                is_demo=True,
                created_at=now,
            )
            session.add(ev)
        else:
            ev.is_demo = True

    await session.flush()

    # 7. 1 OutreachDraft
    draft_id = _gen_id(owner_id, "demo-outreach-draft-1")
    draft_stmt = select(OutreachDraftModel).where(OutreachDraftModel.id == draft_id)
    draft = (await session.execute(draft_stmt)).scalar_one_or_none()
    if draft is None:
        draft = OutreachDraftModel(
            id=draft_id,
            owner_id=owner_id,
            lead_id=seeded_leads[0].id,
            product_id=primary_product.id,
            version=1,
            subject="Handcrafted botanical block-printed textiles for Maison & Objet Boutique",
            body=(
                "Dear Maison & Objet Buying Team,\n\n"
                "We admire your curation of handcrafted home goods and artisanal collections. "
                "Our workshop produces hand block-printed cotton table runners featuring heritage botanical motifs "
                "crafted with natural terracotta, indigo, and ochre dyes.\n\n"
                "Given your focus on distinctive interior textiles, we would love to share our latest lookbook and wholesale catalog with you.\n\n"
                "Warm regards,\nSample Seller"
            ),
            facts_used=[
                {
                    "fact": "Maison & Objet curates independent design and handcrafted home decor collections.",
                    "source_url": "https://maison-objet-boutique.test/about",
                }
            ],
            warnings=[],
            status="draft",
            followup_notes=None,
            parent_draft_id=None,
            is_demo=True,
            created_at=now,
            updated_at=now,
        )
        session.add(draft)
    else:
        draft.is_demo = True
        draft.updated_at = now

    await session.commit()

    return {
        "profile": profile,
        "products": seeded_products,
        "run": run,
        "anchors": seeded_anchors,
        "hypothesis": hypo,
        "leads": seeded_leads,
        "draft": draft,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Fixed Demo Scenario data")
    parser.add_argument(
        "--owner-id",
        type=str,
        default=str(DEFAULT_DEMO_OWNER_ID),
        help="UUID of the seller/owner",
    )
    args = parser.parse_args()

    owner_uuid = UUID(args.owner_id)
    print(f"Initializing database and seeding demo data for owner_id: {owner_uuid}")
    await init_db()

    async with async_session_maker() as session:
        result = await seed_demo_data(session, owner_uuid)
        print(f"Successfully seeded demo scenario:")
        print(f" - Profile: {result['profile'].business_name}")
        print(f" - Products: {len(result['products'])} items")
        print(f" - Research Run: {result['run'].id} (status: {result['run'].status})")
        print(f" - Taste Anchors: {len(result['anchors'])} confirmed")
        print(f" - Leads: {len(result['leads'])} scored")
        print(f" - Outreach Draft: 1 draft for {result['leads'][0].name}")


if __name__ == "__main__":
    asyncio.run(main())
