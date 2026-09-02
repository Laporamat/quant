"""database/session.py – DB connection and async session factory."""
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import settings
from database.models import Base

# ── Async engine (FastAPI) ─────────────────────────────────────────────────────
async_engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    echo=settings.debug,
)
AsyncSessionLocal = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# ── Sync engine (scripts / jobs) ──────────────────────────────────────────────
sync_engine = create_engine(
    settings.database_url_sync,
    pool_size=settings.db_pool_size,
    echo=settings.debug,
)
SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)


async def init_db() -> None:
    """Create all tables (idempotent)."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_sync_session() -> Session:
    return SyncSessionLocal()
