"""
FastAPI Main Application Entrypoint.
Conforms strictly to Contract v0.2.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router, integrations_status
from backend.app.core.config import get_settings
from backend.app.core.errors import register_error_handlers
from backend.app.core.logging import RequestIdMiddleware, setup_logging
from backend.app.db.session import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: configure logging and ensure database tables exist
    setup_logging()
    await init_db()
    yield
    # Shutdown logic
    settings = get_settings()
    if ":memory:" not in settings.database_url:
        await close_db()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Retailer Discovery API",
        version="0.2.0",
        description="Backend API for Retailer Discovery & Outreach Studio",
        lifespan=lifespan,
    )

    # 1. Register Error Envelopes (Appendix A.5)
    register_error_handlers(app)

    # 2. Register Middleware (Order matters: RequestId inside, CORS outside)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # 3. Mount Routes
    app.include_router(api_router)

    # Top-level aliases for root liveness and integration checks
    @app.get("/health", tags=["System"], include_in_schema=False)
    async def root_health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/integrations/status", tags=["System"], include_in_schema=False)
    async def root_integrations_status() -> dict[str, Any]:
        return await integrations_status()

    return app


app = create_app()
