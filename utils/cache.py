"""
utils/cache.py
Caching utilities: Redis (primary) with disk-cache fallback.
"""
from __future__ import annotations
import hashlib
import json
import logging
import pickle
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

from config import settings, CACHE_DIR

logger = logging.getLogger(__name__)


# ── Redis cache ────────────────────────────────────────────────────────────────

class RedisCache:
    """Redis-backed cache with JSON or pickle serialisation."""

    def __init__(self, url: Optional[str] = None) -> None:
        self._url    = url or settings.redis_url
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import redis
                self._client = redis.from_url(self._url, decode_responses=False)
                self._client.ping()
                logger.debug("Redis connected at %s", self._url)
            except Exception as e:
                logger.warning("Redis unavailable: %s – using disk cache", e)
                self._client = None
        return self._client

    def get(self, key: str) -> Optional[Any]:
        if self.client is None:
            return None
        try:
            raw = self.client.get(key)
            return pickle.loads(raw) if raw else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = settings.cache_ttl_seconds) -> bool:
        if self.client is None:
            return False
        try:
            self.client.setex(key, ttl, pickle.dumps(value))
            return True
        except Exception:
            return False

    def delete(self, key: str) -> None:
        if self.client:
            try:
                self.client.delete(key)
            except Exception:
                pass

    def flush(self) -> None:
        if self.client:
            try:
                self.client.flushdb()
            except Exception:
                pass

    @property
    def available(self) -> bool:
        return self.client is not None


# ── Disk cache (fallback) ──────────────────────────────────────────────────────

class DiskCache:
    """Simple file-system cache using pickle."""

    def __init__(self, directory: Path = CACHE_DIR) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = hashlib.md5(key.encode()).hexdigest()
        return self.directory / f"{safe}.pkl"

    def get(self, key: str) -> Optional[Any]:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            return pickle.loads(p.read_bytes())
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = 0) -> bool:
        try:
            self._path(key).write_bytes(pickle.dumps(value))
            return True
        except Exception:
            return False

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()


# ── Unified cache ──────────────────────────────────────────────────────────────

class Cache:
    """Try Redis first, fall back to disk."""

    def __init__(self) -> None:
        self.redis = RedisCache()
        self.disk  = DiskCache()

    def get(self, key: str) -> Optional[Any]:
        val = self.redis.get(key)
        if val is not None:
            return val
        return self.disk.get(key)

    def set(self, key: str, value: Any, ttl: int = settings.cache_ttl_seconds) -> None:
        if not self.redis.set(key, value, ttl):
            self.disk.set(key, value)

    def delete(self, key: str) -> None:
        self.redis.delete(key)
        self.disk.delete(key)

    @staticmethod
    def make_key(*args: Any) -> str:
        return hashlib.md5("|".join(str(a) for a in args).encode()).hexdigest()


# ── Decorator ──────────────────────────────────────────────────────────────────

_cache = Cache()


def cached(ttl: int = settings.cache_ttl_seconds, prefix: str = ""):
    """Decorator: cache the return value of a function."""
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = f"{prefix}:{fn.__name__}:{Cache.make_key(*args, **kwargs)}"
            hit = _cache.get(key)
            if hit is not None:
                logger.debug("Cache HIT: %s", key[:40])
                return hit
            result = fn(*args, **kwargs)
            _cache.set(key, result, ttl)
            return result
        return wrapper
    return decorator
