"""
Professional AI - Redis Cache Utility
Provides caching layer with TTL support for frequently accessed data.
"""

import json
import pickle
import hashlib
from typing import Optional, Any, Callable, Awaitable
from functools import wraps
from loguru import logger

from app.config import settings

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, caching disabled")


class CacheService:
    """Redis-based caching service with TTL support."""

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._enabled = REDIS_AVAILABLE and settings.REDIS_URL

    async def get_client(self) -> Optional[redis.Redis]:
        """Get or create Redis client."""
        if not self._enabled or self._client is not None:
            return self._client

        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                protocol=2,
            )
            await self._client.ping()
            logger.info("Redis cache connected")
            return self._client
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self._enabled = False
            return None

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = await self.get_client()
        if not client:
            return None

        try:
            value = await client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            logger.debug(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL (seconds)."""
        client = await self.get_client()
        if not client:
            return False

        try:
            await client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.debug(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        client = await self.get_client()
        if not client:
            return False

        try:
            await client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        client = await self.get_client()
        if not client:
            return 0

        try:
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Cache clear error: {e}")
            return 0

    async def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], Awaitable[Any]],
        ttl: int = 300,
    ) -> Any:
        """Get from cache or fetch and cache if missing."""
        cached = await self.get(key)
        if cached is not None:
            return cached

        value = await fetch_func()
        await self.set(key, value, ttl)
        return value

    def cached(self, ttl: int = 300, key_prefix: str = ""):
        """Decorator to cache function results."""
        def decorator(func: Callable[..., Awaitable[Any]]):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args[1:] if arg is not None)  # Skip self
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()) if v is not None)
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

                return await self.get_or_set(cache_key, lambda: func(*args, **kwargs), ttl)
            return wrapper
        return decorator


# Global cache instance
cache_service = CacheService()
