"""
Authentication Dependencies (Supabase JWT Verification).
Extracts and validates Supabase JWT using SUPABASE_JWT_SECRET.
Returns CurrentUser or raises 401 unauthorized in Contract v0.2 error envelope.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel, Field

from contracts.schemas import ErrorCode
from backend.app.core.config import get_settings
from backend.app.core.errors import AppError

# HTTPBearer with auto_error=False so we can return custom 401 unauthorized error envelope
security_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Authenticated seller extracted from verified Supabase JWT."""
    id: UUID
    email: str | None = None
    role: str = "authenticated"
    app_metadata: dict[str, Any] = Field(default_factory=dict)
    user_metadata: dict[str, Any] = Field(default_factory=dict)


async def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> CurrentUser:
    """
    FastAPI dependency verifying Supabase JWT on every authenticated route.
    Never trust user_id or owner_id sent in request payloads or query parameters.
    """
    if not credentials or not credentials.credentials:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Missing or empty Authorization Bearer token",
            status_code=401,
        )

    token = credentials.credentials.strip()
    settings = get_settings()
    jwt_secret = settings.supabase_jwt_secret

    if not jwt_secret or not jwt_secret.strip():
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Server authentication secret (SUPABASE_JWT_SECRET) is not configured",
            status_code=401,
        )

    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False, "verify_signature": True},
        )
    except jwt.ExpiredSignatureError:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token has expired",
            status_code=401,
        )
    except (jwt.InvalidSignatureError, jwt.DecodeError):
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid authentication token signature or format",
            status_code=401,
        )
    except Exception as e:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message=f"Authentication token validation failed: {str(e)}",
            status_code=401,
        )

    sub = payload.get("sub")
    if not sub:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token missing subject claim ('sub')",
            status_code=401,
        )

    try:
        user_uuid = UUID(str(sub))
    except (ValueError, TypeError):
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token subject ('sub') is not a valid UUID",
            status_code=401,
        )

    return CurrentUser(
        id=user_uuid,
        email=payload.get("email"),
        role=payload.get("role", "authenticated"),
        app_metadata=payload.get("app_metadata", {}),
        user_metadata=payload.get("user_metadata", {}),
    )
