"""api/dependencies.py – Shared FastAPI dependencies."""
from __future__ import annotations
from functools import lru_cache
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status

from config import settings
from data.loader import DataLoader
from data.downloader import DataDownloader
from data.universe import UniverseManager


# ── Singletons (one per process) ──────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_loader() -> DataLoader:
    return DataLoader()

@lru_cache(maxsize=1)
def get_downloader() -> DataDownloader:
    return DataDownloader()

@lru_cache(maxsize=1)
def get_universe_manager() -> UniverseManager:
    return UniverseManager()


# ── Redis cache (optional, falls back to no-op) ───────────────────────────────

_redis_client = None

def get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            _redis_client.ping()
        except Exception:
            _redis_client = None
    return _redis_client


# ── DB session (async SQLAlchemy) ──────────────────────────────────────────────

async def get_db_session() -> AsyncGenerator:
    """Yield an async DB session; no-op if DB is unavailable."""
    try:
        from database.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            yield session
    except Exception:
        yield None


# ── Pagination helper ─────────────────────────────────────────────────────────

def pagination(skip: int = 0, limit: int = 100):
    if limit > 1000:
        raise HTTPException(status_code=400, detail="limit cannot exceed 1000")
    return {"skip": skip, "limit": limit}
