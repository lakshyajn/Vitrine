"""
Taste Research Provider Interface and Mock Implementation (WS3 Section 5).
Matches Contract v0.2 Appendix A.6 and includes deliberate empty and weak-signal
cases as required by WS3 Section 5.1.
"""

from __future__ import annotations

import os
from typing import Protocol

from contracts.schemas import InsightOptions, TasteEntity, TasteSignal


class TasteResearchProvider(Protocol):
    name: str  # "mock" or "qloo"
    is_demo: bool  # True for mock provider

    async def search_entities(self, query: str) -> list[TasteEntity]:
        ...

    async def get_insights(self, entity_id: str, options: InsightOptions) -> list[TasteSignal]:
        ...


class MockTasteProvider:
    """
    Mock taste provider returning fixture data with is_demo: True and 'demo-' prefix IDs.
    Includes deliberate empty ('empty'/'none') and weak ('weak') cases for UI/backend testing.
    """

    name: str = "mock"
    is_demo: bool = True

    async def search_entities(self, query: str) -> list[TasteEntity]:
        clean_q = (query or "").strip()
        if not clean_q or "empty" in clean_q.lower() or "no_match" in clean_q.lower():
            return []

        slug = clean_q.lower().replace(" ", "-")[:20]
        if "weak" in clean_q.lower():
            return [
                TasteEntity(
                    id=f"demo-entity-weak-{slug}",
                    name=f"{clean_q} (Sparse Demo Context)",
                    entity_type="brand",
                    metadata={"category": "Home Decor & Living", "confidence": "low", "is_demo": True},
                )
            ]

        return [
            TasteEntity(
                id=f"demo-entity-{slug}",
                name=f"{clean_q} (Aesthetic Context)",
                entity_type="brand",
                metadata={"category": "Home Decor & Living", "is_demo": True},
            )
        ]

    async def get_insights(self, entity_id: str, options: InsightOptions) -> list[TasteSignal]:
        eid = (entity_id or "").strip()
        if not eid or "empty" in eid.lower():
            return []

        if "weak" in eid.lower():
            return [
                TasteSignal(
                    type="weak_affinity_signal",
                    text=f"Limited demo signal for {eid}; insufficient regional density.",
                    source="mock_taste_provider",
                    source_ref=f"call-{eid}",
                    score=0.25,
                    raw={"affinity_score": 0.25, "confidence": "low", "is_demo": True},
                )
            ]

        return [
            TasteSignal(
                type="affinity_trend",
                text=f"High cultural affinity between artisan textiles and independent design boutiques for {eid}.",
                source="mock_taste_provider",
                source_ref=f"call-{eid}",
                score=0.88,
                raw={"affinity_score": 0.88, "confidence": "medium", "is_demo": True},
            )
        ]


def get_taste_provider() -> TasteResearchProvider:
    """Factory returning TasteResearchProvider (Mock until QLOO_API_KEY + live responses are verified)."""
    api_key = os.environ.get("QLOO_API_KEY")
    if api_key and api_key.strip():
        # Per WS3 Section 5.4: Never guess Qloo schemas before real API docs/responses are recorded.
        pass
    return MockTasteProvider()