"""
Database Session and Engine Management (SQLAlchemy 2.0 Async).
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.core.config import get_settings
from backend.app.db.models import Base


def _normalize_database_url(url: str) -> str:
    """Normalize database URL for async drivers (postgresql -> postgresql+asyncpg)."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def create_engine_from_url(database_url: str) -> AsyncEngine:
    norm_url = _normalize_database_url(database_url)
    connect_args = {}
    extra_kwargs = {}
    if "sqlite" in norm_url:
        connect_args["check_same_thread"] = False
        if ":memory:" in norm_url:
            from sqlalchemy.pool import StaticPool
            extra_kwargs["poolclass"] = StaticPool
    return create_async_engine(norm_url, echo=False, connect_args=connect_args, **extra_kwargs)


# Global engine and sessionmaker
settings = get_settings()
engine: AsyncEngine = create_engine_from_url(settings.database_url)
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


_db_initialized: bool = False


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency providing a transactional AsyncSession."""
    global _db_initialized
    if not _db_initialized:
        await init_db()
        _db_initialized = True

    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db(engine_override: AsyncEngine | None = None) -> None:
    """Initialize database tables (used for test setup)."""
    target_engine = engine_override or engine
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db(engine_override: AsyncEngine | None = None) -> None:
    """Dispose database engine connections."""
    target_engine = engine_override or engine
    await target_engine.dispose()
