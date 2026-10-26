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

DEFAULT_DEMO_OWNER_ID = UUID("00000000-0000-0000-0000-000000000001")


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
    is_dev = settings.app_env.lower() in ("dev", "test", "development")

    # In dev mode, handle dev/demo token aliases
    if is_dev and token in ("dev-token", "dev-test-token", "demo-token", "dev", "test", "mock"):
        return CurrentUser(
            id=DEFAULT_DEMO_OWNER_ID,
            email="artisan@sampleseller.test",
            role="authenticated",
        )

    jwt_secret = settings.supabase_jwt_secret
    payload: dict[str, Any] = {}

    if jwt_secret and jwt_secret.strip():
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
        except (jwt.InvalidSignatureError, jwt.DecodeError) as sig_err:
            # If in dev mode, allow dev-issued tokens (e.g. from Vitrine dev helper)
            if is_dev:
                try:
                    unverified = jwt.decode(
                        token,
                        options={"verify_aud": False, "verify_signature": False},
                    )
                    if unverified.get("iss") == "vitrine-dev" or str(unverified.get("sub")) == str(DEFAULT_DEMO_OWNER_ID):
                        payload = unverified
                    else:
                        raise sig_err
                except AppError:
                    raise
                except Exception:
                    raise AppError(
                        code=ErrorCode.UNAUTHORIZED,
                        message="Invalid authentication token signature or format",
                        status_code=401,
                    )
            else:
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
    else:
        # SUPABASE_JWT_SECRET is not configured
        if is_dev:
            try:
                payload = jwt.decode(
                    token,
                    options={"verify_aud": False, "verify_signature": False},
                )
            except Exception:
                raise AppError(
                    code=ErrorCode.UNAUTHORIZED,
                    message="Invalid dev authentication token format",
                    status_code=401,
                )
        else:
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Server authentication secret (SUPABASE_JWT_SECRET) is not configured",
                status_code=401,
            )

    sub = payload.get("sub")
    if not sub:
        if is_dev:
            user_uuid = DEFAULT_DEMO_OWNER_ID
        else:
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Authentication token missing subject claim ('sub')",
                status_code=401,
            )
    else:
        try:
            user_uuid = UUID(str(sub))
        except (ValueError, TypeError):
            if is_dev:
                user_uuid = DEFAULT_DEMO_OWNER_ID
            else:
                raise AppError(
                    code=ErrorCode.UNAUTHORIZED,
                    message="Authentication token subject ('sub') is not a valid UUID",
                    status_code=401,
                )

    return CurrentUser(
        id=user_uuid,
        email=payload.get("email", "artisan@sampleseller.test" if is_dev else None),
        role=payload.get("role", "authenticated"),
        app_metadata=payload.get("app_metadata", {}),
        user_metadata=payload.get("user_metadata", {}),
    )
