"""
Authentication Dependencies (Supabase JWT Verification).
Extracts and validates Supabase JWT using SUPABASE_JWT_SECRET (HS256)
or Supabase JWKS endpoint (ES256/RS256).
Returns CurrentUser or raises 401 unauthorized in Contract v0.2 error envelope.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import PyJWKClient
from pydantic import BaseModel, Field

from contracts.schemas import ErrorCode
from backend.app.core.config import Settings, get_settings
from backend.app.core.errors import AppError

logger = logging.getLogger(__name__)

# HTTPBearer with auto_error=False so we can return custom 401 unauthorized error envelope
security_scheme = HTTPBearer(auto_error=False)

DEFAULT_DEMO_OWNER_ID = UUID("00000000-0000-0000-0000-000000000001")

_warned_allow_dev_tokens: bool = False
_jwk_clients: dict[str, PyJWKClient] = {}


def check_and_warn_dev_tokens(settings: Settings) -> None:
    """Log a single startup warning when allow_dev_tokens is enabled."""
    global _warned_allow_dev_tokens
    if settings.allow_dev_tokens and not _warned_allow_dev_tokens:
        _warned_allow_dev_tokens = True
        logger.warning(
            "SECURITY WARNING: allow_dev_tokens is enabled. "
            "Dev token aliases and unsigned tokens are accepted. Do not enable in production."
        )


def get_jwk_client(supabase_url: str) -> PyJWKClient:
    """Get or create cached PyJWKClient for the given Supabase URL."""
    url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    if url not in _jwk_clients:
        _jwk_clients[url] = PyJWKClient(url, cache_keys=True)
    return _jwk_clients[url]


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
    if not token:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Missing or empty Authorization Bearer token",
            status_code=401,
        )

    settings = get_settings()

    # Dev bypass: keep dev aliases only when allow_dev_tokens is true
    if settings.allow_dev_tokens:
        check_and_warn_dev_tokens(settings)
        if token in ("dev-token", "dev-test-token", "demo-token", "dev", "test", "mock"):
            return CurrentUser(
                id=DEFAULT_DEMO_OWNER_ID,
                email="artisan@sampleseller.test",
                role="authenticated",
            )

    # 1. Read unverified header alg
    try:
        header = jwt.get_unverified_header(token)
    except Exception:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid authentication token header or format",
            status_code=401,
        )

    alg = header.get("alg")
    if not alg or alg.lower() == "none" or alg not in ("HS256", "ES256", "RS256"):
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid authentication token algorithm",
            status_code=401,
        )

    # 2. Determine key and algorithms
    key: Any = None
    if alg == "HS256":
        jwt_secret = settings.supabase_jwt_secret
        if not jwt_secret or not jwt_secret.strip():
            # If allow_dev_tokens is enabled, allow unsigned dev token
            if settings.allow_dev_tokens:
                try:
                    payload = jwt.decode(
                        token,
                        options={"verify_signature": False, "verify_aud": False, "verify_exp": False},
                    )
                    sub_val = payload.get("sub")
                    if sub_val:
                        return CurrentUser(
                            id=UUID(str(sub_val)),
                            email=payload.get("email"),
                            role=payload.get("role", "authenticated"),
                            app_metadata=payload.get("app_metadata", {}),
                            user_metadata=payload.get("user_metadata", {}),
                        )
                    return CurrentUser(
                        id=DEFAULT_DEMO_OWNER_ID,
                        email="artisan@sampleseller.test",
                        role="authenticated",
                    )
                except Exception:
                    raise AppError(
                        code=ErrorCode.UNAUTHORIZED,
                        message="Invalid authentication token format",
                        status_code=401,
                    )
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Server authentication secret (SUPABASE_JWT_SECRET) is not configured",
                status_code=401,
            )
        key = jwt_secret.strip()
    elif alg in ("ES256", "RS256"):
        supabase_url = settings.supabase_url
        if not supabase_url or not supabase_url.strip():
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Server authentication URL (SUPABASE_URL) is not configured for asymmetric token verification",
                status_code=401,
            )
        try:
            jwk_client = get_jwk_client(supabase_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token)
            key = signing_key.key
        except Exception:
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Failed to fetch key for token verification",
                status_code=401,
            )

    # 3. Always require audience="authenticated", expiry, sub, and issuer (when SUPABASE_URL is set)
    expected_issuer = (
        f"{settings.supabase_url.rstrip('/')}/auth/v1"
        if settings.supabase_url and settings.supabase_url.strip()
        else None
    )

    decode_options: dict[str, Any] = {
        "verify_signature": True,
        "verify_aud": True,
        "verify_exp": True,
        "verify_iss": bool(expected_issuer),
        "require": ["exp", "aud", "sub"],
    }

    decode_kwargs: dict[str, Any] = {
        "jwt": token,
        "key": key,
        "algorithms": [alg],
        "audience": "authenticated",
        "options": decode_options,
    }
    if expected_issuer:
        decode_kwargs["issuer"] = expected_issuer

    try:
        payload = jwt.decode(**decode_kwargs)
    except jwt.ExpiredSignatureError:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token has expired",
            status_code=401,
        )
    except jwt.InvalidAudienceError:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token has invalid audience",
            status_code=401,
        )
    except jwt.InvalidIssuerError:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token has invalid issuer",
            status_code=401,
        )
    except (jwt.InvalidSignatureError, jwt.DecodeError):
        if settings.allow_dev_tokens:
            try:
                unverified = jwt.decode(
                    token,
                    options={"verify_signature": False, "verify_aud": False, "verify_exp": False},
                )
                if (
                    unverified.get("iss") == "vitrine-dev"
                    or str(unverified.get("sub")) == str(DEFAULT_DEMO_OWNER_ID)
                ):
                    payload = unverified
                else:
                    raise AppError(
                        code=ErrorCode.UNAUTHORIZED,
                        message="Invalid authentication token signature",
                        status_code=401,
                    )
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
                message="Invalid authentication token signature",
                status_code=401,
            )
    except jwt.MissingRequiredClaimError as claim_err:
        claim_name = getattr(claim_err, "claim", "claim")
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message=f"Authentication token missing required claim: {claim_name}",
            status_code=401,
        )
    except Exception:
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid authentication token",
            status_code=401,
        )

    # 4. Require a valid UUID sub
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
