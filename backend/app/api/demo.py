"""
Demo Workspace Seed API Router (/api/v1/demo).
Allows seeding demo scenario records scoped strictly to the calling authenticated maker.
Available only in dev and test environments (returns 404 in production).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.deps import CurrentUser, current_user
from backend.app.core.config import get_settings
from backend.app.db.seed_demo import seed_demo_data
from backend.app.db.session import get_db_session

demo_router = APIRouter(prefix="/demo", tags=["Demo"])


class DemoSeedSummary(BaseModel):
    products_seeded: int = Field(..., description="Number of demo products seeded for the caller")
    leads_seeded: int = Field(..., description="Number of demo buyer leads seeded for the caller")
    runs_seeded: int = Field(..., description="Number of demo research runs seeded for the caller")
    drafts_seeded: int = Field(..., description="Number of demo outreach drafts seeded for the caller")


@demo_router.post(
    "/seed",
    response_model=DemoSeedSummary,
    status_code=status.HTTP_200_OK,
    summary="Seed Fixed Demo Scenario",
    description="Seeds realistic demo products, research runs, leads, and outreach drafts scoped exclusively to the authenticated user. Idempotent per caller. Available only when APP_ENV is dev or test.",
)
async def seed_demo_workspace(
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> DemoSeedSummary:
    settings = get_settings()
    app_env = (settings.app_env or "production").lower()

    if app_env not in ("dev", "test"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo seed endpoint is only available in dev and test environments",
        )

    result = await seed_demo_data(session, user.id)

    return DemoSeedSummary(
        products_seeded=result["products_seeded"],
        leads_seeded=result["leads_seeded"],
        runs_seeded=result["runs_seeded"],
        drafts_seeded=result["drafts_seeded"],
    )
