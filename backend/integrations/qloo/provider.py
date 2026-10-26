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


class QlooTasteProvider:
    """
    Live Qloo Cultural Taste & Affinity Intelligence Provider.
    Calls Qloo API (/search and /v2/insights) with real authentication,
    strict error propagation for orchestrator retry/fallback, and maps
    real Qloo entities & affinity vectors to TasteEntity and TasteSignal.
    """

    name: str = "qloo"
    is_demo: bool = False

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://hackathon.api.qloo.com",
        timeout_seconds: float = 15.0,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = (base_url or "https://hackathon.api.qloo.com").rstrip("/")
        self.timeout_seconds = float(timeout_seconds)

    async def search_entities(self, query: str) -> list[TasteEntity]:
        import httpx

        clean_q = (query or "").strip()
        if not clean_q:
            return []

        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
        }
        params = {"query": clean_q}

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                f"{self.base_url}/search",
                params=params,
                headers=headers,
            )

        if response.status_code == 200:
            data = response.json()
            raw_results = data.get("results") or []
            entities: list[TasteEntity] = []

            for item in raw_results:
                eid = item.get("entity_id")
                name = item.get("name")
                if not eid or not name:
                    continue

                types = [str(t).lower() for t in (item.get("types") or [])]
                if any("place" in t for t in types):
                    etype = "place"
                elif any("brand" in t for t in types):
                    etype = "brand"
                else:
                    etype = "brand"

                props = item.get("properties") or {}
                category = (
                    props.get("industry")
                    or props.get("category_description")
                    or props.get("description")
                    or "Home Decor & Living"
                )

                entities.append(
                    TasteEntity(
                        id=str(eid),
                        name=str(name),
                        entity_type=etype,
                        metadata={
                            "category": str(category)[:150],
                            "address": props.get("address"),
                            "is_demo": False,
                        },
                    )
                )

            return entities

        # Propagate status error so QlooOrchestrator can handle retry or fallback
        response.raise_for_status()
        return []

    async def get_insights(self, entity_id: str, options: InsightOptions) -> list[TasteSignal]:
        import httpx

        eid = (entity_id or "").strip()
        if not eid:
            return []

        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
        }
        params = {
            "filter.type": "urn:entity:brand",
            "entity_ids": eid,
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                f"{self.base_url}/v2/insights",
                params=params,
                headers=headers,
            )

        if response.status_code == 200:
            data = response.json()
            entities = data.get("results", {}).get("entities", [])
            signals: list[TasteSignal] = []

            for ent in entities:
                name = ent.get("name")
                if not name:
                    continue

                query_info = ent.get("query") or {}
                affinity = query_info.get("affinity")
                props = ent.get("properties") or {}
                desc = (
                    props.get("description")
                    or props.get("style_description")
                    or props.get("category_description")
                    or ""
                )

                score_val: float | None = float(affinity) if isinstance(affinity, (int, float)) else None
                aff_label = f"{score_val:.2f}" if score_val is not None else "high"
                text = f"Cultural affinity signal ({aff_label}) with {name}. {desc}".strip()

                signals.append(
                    TasteSignal(
                        type="cultural_affinity",
                        text=text[:300],
                        source="qloo",
                        score=score_val,
                        raw={
                            "affinity_score": score_val,
                            "entity_name": name,
                            "entity_id": ent.get("entity_id"),
                            "subtype": ent.get("subtype"),
                            "is_demo": False,
                        },
                    )
                )

            return signals

        response.raise_for_status()
        return []


def get_taste_provider() -> TasteResearchProvider:
    """Factory returning QlooTasteProvider if QLOO_API_KEY is configured, else MockTasteProvider."""
    # Explicit empty environment variable forces MockTasteProvider (e.g. in test isolation)
    if "QLOO_API_KEY" in os.environ and not os.environ["QLOO_API_KEY"].strip():
        return MockTasteProvider()

    api_key = os.environ.get("QLOO_API_KEY", "").strip()
    base_url = os.environ.get("QLOO_BASE_URL", "").strip() or "https://hackathon.api.qloo.com"
    timeout = 15.0

    try:
        from backend.app.core.config import get_settings

        settings = get_settings()
        api_key = api_key or getattr(settings, "qloo_api_key", None)
        base_url = getattr(settings, "qloo_base_url", None) or base_url
        timeout = float(getattr(settings, "qloo_timeout_seconds", 15.0))
    except Exception:
        pass

    if api_key and str(api_key).strip():
        return QlooTasteProvider(
            api_key=str(api_key).strip(),
            base_url=str(base_url).strip(),
            timeout_seconds=timeout,
        )
    return MockTasteProvider()