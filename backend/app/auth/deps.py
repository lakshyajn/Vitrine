"""
Authentication Dependencies (Supabase JWT Verification).
Extracts and validates Supabase JWT using SUPABASE_JWT_SECRET (HS256)
or Supabase JWKS endpoint (ES256/RS256).
Returns CurrentUser or raises 401 unauthorized in Contract v0.2 error envelope.
"""

from __future__ import annotations

import logging
from typing import Any
import urllib.error
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt import PyJWKClient, PyJWKClientConnectionError, PyJWKClientError, PyJWKSetError
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


def log_auth_failure(
    reason: str,
    alg: str | None = None,
    kid_present: bool = False,
    iss: str | None = None,
    aud: str | None = None,
) -> None:
    """Log a single structured line at WARNING per auth failure with non-secret facts only."""
    logger.warning(
        "auth_failure reason=%s alg=%s kid_present=%s iss=%s aud=%s",
        reason,
        alg,
        kid_present,
        iss,
        aud,
    )


def check_startup_config(settings: Settings) -> None:
    """Startup configuration check (log only, never crash)."""
    global _warned_allow_dev_tokens
    if settings.allow_dev_tokens and not _warned_allow_dev_tokens:
        _warned_allow_dev_tokens = True
        logger.warning(
            "SECURITY WARNING: ALLOW_DEV_TOKENS is true. "
            "Dev token aliases and unsigned tokens are accepted. Do not enable in production."
        )

    raw_secret = (settings.supabase_jwt_secret or "").strip()
    if raw_secret:
        if raw_secret.startswith("sb_"):
            logger.warning(
                "CONFIGURATION WARNING: SUPABASE_JWT_SECRET starts with 'sb_'. "
                "This appears to be an API key, not the JWT signing secret. HS256 verification will fail."
            )
        elif len(raw_secret.split(".")) == 3:
            logger.warning(
                "CONFIGURATION WARNING: SUPABASE_JWT_SECRET looks like a JWT (three dot-separated parts). "
                "This appears to be an API key, not the JWT signing secret. HS256 verification will fail."
            )

    raw_url = (settings.supabase_url or "").strip()
    if not raw_url:
        logger.warning(
            "CONFIGURATION WARNING: SUPABASE_URL is unset. "
            "Asymmetric token verification (ES256/RS256) and issuer checks will not function."
        )
    elif raw_url.endswith("/"):
        logger.warning(
            "CONFIGURATION WARNING: SUPABASE_URL ends with a trailing slash. "
            "Normalize by stripping the trailing slash to prevent issuer/JWKS URL mismatch."
        )


def check_and_warn_dev_tokens(settings: Settings) -> None:
    """Backwards-compatible wrapper for startup checks."""
    check_startup_config(settings)


def get_jwk_client(supabase_url: str) -> PyJWKClient:
    """Get or create cached PyJWKClient for the given Supabase URL with 5s timeout."""
    norm_url = supabase_url.strip().rstrip("/")
    jwks_url = f"{norm_url}/auth/v1/.well-known/jwks.json"
    if jwks_url not in _jwk_clients:
        _jwk_clients[jwks_url] = PyJWKClient(jwks_url, cache_keys=True, timeout=5)
    return _jwk_clients[jwks_url]


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
        log_auth_failure("missing_token")
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Missing or empty Authorization Bearer token",
            status_code=401,
        )

    token = credentials.credentials.strip()
    if not token:
        log_auth_failure("missing_token")
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Missing or empty Authorization Bearer token",
            status_code=401,
        )

    settings = get_settings()

    # Dev bypass: keep dev aliases only when allow_dev_tokens is true
    if settings.allow_dev_tokens:
        check_startup_config(settings)
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
        log_auth_failure("malformed")
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid authentication token header or format",
            status_code=401,
        )

    alg = header.get("alg")
    kid_present = bool(header.get("kid"))

    # Extract unverified claims for diagnosability without signature check
    try:
        unverified_claims = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_iss": False,
                "verify_exp": False,
                "verify_nbf": False,
                "verify_iat": False,
            },
        )
        unverified_iss = unverified_claims.get("iss")
        raw_aud = unverified_claims.get("aud")
        if isinstance(raw_aud, list):
            unverified_aud = ",".join(str(a) for a in raw_aud)
        elif raw_aud is not None:
            unverified_aud = str(raw_aud)
        else:
            unverified_aud = None
    except Exception:
        unverified_iss = None
        unverified_aud = None

    if not alg or alg.lower() == "none" or alg not in ("HS256", "ES256", "RS256"):
        log_auth_failure(
            "unsupported_alg",
            alg=alg,
            kid_present=kid_present,
            iss=unverified_iss,
            aud=unverified_aud,
        )
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
                    log_auth_failure(
                        "malformed",
                        alg=alg,
                        kid_present=kid_present,
                        iss=unverified_iss,
                        aud=unverified_aud,
                    )
                    raise AppError(
                        code=ErrorCode.UNAUTHORIZED,
                        message="Invalid authentication token format",
                        status_code=401,
                    )
            log_auth_failure(
                "secret_not_configured",
                alg=alg,
                kid_present=kid_present,
                iss=unverified_iss,
                aud=unverified_aud,
            )
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Server authentication secret (SUPABASE_JWT_SECRET) is not configured",
                status_code=401,
            )
        key = jwt_secret.strip()
    elif alg in ("ES256", "RS256"):
        supabase_url = (settings.supabase_url or "").strip().rstrip("/")
        if not supabase_url:
            log_auth_failure(
                "jwks_unavailable",
                alg=alg,
                kid_present=kid_present,
                iss=unverified_iss,
                aud=unverified_aud,
            )
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Server authentication URL (SUPABASE_URL) is not configured for asymmetric token verification",
                status_code=401,
            )
        if not kid_present:
            log_auth_failure(
                "no_matching_key",
                alg=alg,
                kid_present=False,
                iss=unverified_iss,
                aud=unverified_aud,
            )
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Authentication token missing key identifier ('kid')",
                status_code=401,
            )
        try:
            jwk_client = get_jwk_client(supabase_url)
            signing_key = jwk_client.get_signing_key_from_jwt(token)
            key = signing_key.key
        except (PyJWKClientConnectionError, PyJWKSetError, urllib.error.URLError):
            log_auth_failure(
                "jwks_unavailable",
                alg=alg,
                kid_present=kid_present,
                iss=unverified_iss,
                aud=unverified_aud,
            )
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Failed to fetch key for token verification",
                status_code=401,
            )
        except PyJWKClientError as exc:
            err_text = str(exc).lower()
            if "signing key" in err_text or "kid" in err_text or "match" in err_text:
                log_auth_failure(
                    "no_matching_key",
                    alg=alg,
                    kid_present=kid_present,
                    iss=unverified_iss,
                    aud=unverified_aud,
                )
            else:
                log_auth_failure(
                    "jwks_unavailable",
                    alg=alg,
                    kid_present=kid_present,
                    iss=unverified_iss,
                    aud=unverified_aud,
                )
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Failed to fetch key for token verification",
                status_code=401,
            )
        except Exception:
            log_auth_failure(
                "jwks_unavailable",
                alg=alg,
                kid_present=kid_present,
                iss=unverified_iss,
                aud=unverified_aud,
            )
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Failed to fetch key for token verification",
                status_code=401,
            )

    # 3. Always require audience="authenticated", expiry, sub, and issuer (when SUPABASE_URL is set)
    normalized_supabase_url = (settings.supabase_url or "").strip().rstrip("/")
    expected_issuer = (
        f"{normalized_supabase_url}/auth/v1"
        if normalized_supabase_url
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
        "leeway": 60,
    }
    if expected_issuer:
        decode_kwargs["issuer"] = expected_issuer

    try:
        payload = jwt.decode(**decode_kwargs)
    except jwt.ExpiredSignatureError:
        log_auth_failure("expired", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token has expired",
            status_code=401,
        )
    except jwt.ImmatureSignatureError:
        log_auth_failure("not_yet_valid", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token is not yet valid",
            status_code=401,
        )
    except jwt.InvalidAudienceError:
        log_auth_failure("bad_audience", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token has invalid audience",
            status_code=401,
        )
    except jwt.InvalidIssuerError:
        log_auth_failure("bad_issuer", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
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
                    log_auth_failure("bad_signature", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
                    raise AppError(
                        code=ErrorCode.UNAUTHORIZED,
                        message="Invalid authentication token signature",
                        status_code=401,
                    )
            except AppError:
                raise
            except Exception:
                log_auth_failure("bad_signature", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
                raise AppError(
                    code=ErrorCode.UNAUTHORIZED,
                    message="Invalid authentication token signature or format",
                    status_code=401,
                )
        else:
            log_auth_failure("bad_signature", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
            raise AppError(
                code=ErrorCode.UNAUTHORIZED,
                message="Invalid authentication token signature",
                status_code=401,
            )
    except jwt.MissingRequiredClaimError as claim_err:
        claim_name = getattr(claim_err, "claim", "claim")
        if claim_name == "sub":
            log_auth_failure("invalid_sub", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
        elif claim_name == "aud":
            log_auth_failure("bad_audience", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
        elif claim_name == "exp":
            log_auth_failure("expired", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
        else:
            log_auth_failure("malformed", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message=f"Authentication token missing required claim: {claim_name}",
            status_code=401,
        )
    except Exception:
        log_auth_failure("malformed", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Invalid authentication token",
            status_code=401,
        )

    # 4. Require a valid UUID sub
    sub = payload.get("sub")
    if not sub:
        log_auth_failure("invalid_sub", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
        raise AppError(
            code=ErrorCode.UNAUTHORIZED,
            message="Authentication token missing subject claim ('sub')",
            status_code=401,
        )

    try:
        user_uuid = UUID(str(sub))
    except (ValueError, TypeError):
        log_auth_failure("invalid_sub", alg=alg, kid_present=kid_present, iss=unverified_iss, aud=unverified_aud)
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
