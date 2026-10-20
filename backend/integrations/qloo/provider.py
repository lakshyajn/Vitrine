"""
Taste Research Provider Interface and Mock Implementation (WS3 stub for WS2).
Matching WS2_Spec.md Appendix A.6.
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
    """Mock taste provider returning fixture data with is_demo: True."""

    name: str = "mock"
    is_demo: bool = True

    async def search_entities(self, query: str) -> list[TasteEntity]:
        clean_q = query.strip()
        return [
            TasteEntity(
                id=f"demo-entity-{clean_q.lower().replace(' ', '-')[:20]}",
                name=f"{clean_q} (Aesthetic Context)",
                entity_type="brand",
                metadata={"category": "Home Decor & Living", "is_demo": True},
            )
        ]

    async def get_insights(self, entity_id: str, options: InsightOptions) -> list[TasteSignal]:
        return [
            TasteSignal(
                type="affinity_trend",
                text=f"High cultural affinity between artisan textiles and independent design boutiques for {entity_id}.",
                source="mock_taste_provider",
                source_ref=f"call-{entity_id}",
                score=0.88,
                raw={"affinity_score": 0.88, "confidence": "medium"},
            )
        ]


def get_taste_provider() -> TasteResearchProvider:
    """Factory returning TasteResearchProvider (real Qloo if QLOO_API_KEY set, else Mock)."""
    # WS3 will provide the full real Qloo client during Qloo activation.
    # Currently returns MockTasteProvider when no valid key is present.
    api_key = os.environ.get("QLOO_API_KEY")
    if api_key and api_key.strip():
        # Stub for future real provider activation
        # WS3 will plug real Qloo implementation here
        pass
    return MockTasteProvider()
