"""
Main API Router for /api/v1 endpoints.
Aggregates all modular domain routers.
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from contracts.schemas import IntegrationState
from backend.app.api.leads import leads_router
from backend.app.api.outreach import lead_outreach_router, outreach_router
from backend.app.api.products import products_router
from backend.app.api.profile import profile_router
from backend.app.api.research_runs import runs_router, taste_anchors_router
from backend.app.core.config import get_settings

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Liveness check (no authentication required)."""
    return {"status": "ok"}


@api_router.get("/integrations/status", tags=["System"])
async def integrations_status() -> dict[str, Any]:
    """
    Returns the operational integration states (live vs mock) of Nebius, Tavily, and Qloo.
    Never exposes API keys or secrets.
    """
    settings = get_settings()

    ai_state = IntegrationState.LIVE.value if settings.is_ai_live else IntegrationState.MOCK.value
    search_state = IntegrationState.LIVE.value if settings.is_search_live else IntegrationState.MOCK.value
    taste_state = IntegrationState.LIVE.value if settings.is_taste_live else IntegrationState.MOCK.value

    return {
        "ai": {
            "state": ai_state,
            "model_id": settings.nebius_model_id,
        },
        "search": {
            "state": search_state,
            "provider_name": "tavily" if settings.is_search_live else "fixture-tavily",
        },
        "taste": {
            "state": taste_state,
            "provider_name": "qloo" if settings.is_taste_live else "mock",
        },
    }


# Mount all domain sub-routers
api_router.include_router(profile_router)
api_router.include_router(products_router)
api_router.include_router(runs_router)
api_router.include_router(taste_anchors_router)
api_router.include_router(leads_router)
api_router.include_router(lead_outreach_router)
api_router.include_router(outreach_router)
