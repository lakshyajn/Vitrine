"""
Profile API Router (/api/v1/profile).
Implements GET /profile and PUT /profile with real DB persistence (DECISION-D16).
"""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from contracts.schemas import Profile, ProfileUpdate
from backend.app.auth.deps import CurrentUser, current_user
from backend.app.db.models import ProfileModel
from backend.app.db.session import get_db_session

profile_router = APIRouter(prefix="/profile", tags=["Profile"])


def _profile_model_to_schema(model: ProfileModel) -> Profile:
    return Profile(
        id=model.id,
        user_id=model.user_id,
        business_name=model.business_name,
        country=model.country,
        website=model.website,
        contact_email=model.contact_email,
        about=model.about,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


@profile_router.get("", response_model=Profile)
async def get_profile(
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Profile:
    """
    Retrieve the seller profile.
    Auto-creates an empty profile row if none exists (DECISION-D16).
    """
    stmt = select(ProfileModel).where(ProfileModel.user_id == user.id)
    profile = (await session.execute(stmt)).scalar_one_or_none()

    if profile is None:
        profile = ProfileModel(
            user_id=user.id,
            business_name="",
            country=None,
            website=None,
            contact_email=user.email,
            about=None,
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)

    return _profile_model_to_schema(profile)


@profile_router.put("", response_model=Profile)
async def update_profile(
    payload: ProfileUpdate,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Profile:
    """
    Update seller profile details (business_name, country, website, contact_email, about).
    Persists changes to the database.
    """
    stmt = select(ProfileModel).where(ProfileModel.user_id == user.id)
    profile = (await session.execute(stmt)).scalar_one_or_none()

    if profile is None:
        profile = ProfileModel(
            user_id=user.id,
            business_name=payload.business_name or "",
            country=payload.country,
            website=payload.website,
            contact_email=payload.contact_email or user.email,
            about=payload.about,
        )
        session.add(profile)
    else:
        update_data = payload.model_dump(exclude_unset=True)
        for field, val in update_data.items():
            setattr(profile, field, val)
        profile.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(profile)
    return _profile_model_to_schema(profile)
