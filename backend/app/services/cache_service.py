"""
Professional AI - Redis Cache Service
High-performance caching for repeated AI responses, API calls, and database queries.
"""

import json
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
from loguru import logger

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - caching disabled")

from app.config import settings


class CacheService:
    """Redis-based caching service with TTL and pattern-based invalidation."""

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._enabled = REDIS_AVAILABLE and settings.REDIS_ENABLED
        self._default_ttl = settings.CACHE_DEFAULT_TTL
        self._ai_cache_ttl = settings.CACHE_AI_TTL

    async def connect(self):
        """Connect to Redis."""
        if not self._enabled:
            logger.info("Redis caching disabled")
            return

        try:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                max_connections=50,
            )
            # Test connection
            await self._redis.ping()
            logger.info(f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self._enabled = False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    def _generate_key(self, prefix: str, data: str) -> str:
        """Generate cache key from data."""
        hash_obj = hashlib.md5(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._enabled or not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.debug(f"Cache get error: {e}")

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache with TTL."""
        if not self._enabled or not self._redis:
            return False

        try:
            serialized = json.dumps(value, default=str)
            await self._redis.setex(
                key,
                ttl or self._default_ttl,
                serialized,
            )
            return True
        except Exception as e:
            logger.debug(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self._enabled or not self._redis:
            return False

        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self._enabled or not self._redis:
            return 0

        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
                return len(keys)
        except Exception as e:
            logger.debug(f"Cache delete pattern error: {e}")

        return 0

    async def get_or_set(
        self,
        key: str,
        callback,
        ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache or execute callback and cache result."""
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            logger.debug(f"Cache hit: {key}")
            return cached

        # Execute callback
        logger.debug(f"Cache miss: {key}")
        value = await callback()

        # Cache result
        if value is not None:
            await self.set(key, value, ttl)

        return value

    # AI-specific caching methods

    async def get_ai_response(self, prompt_hash: str) -> Optional[Dict]:
        """Get cached AI response."""
        return await self.get(f"ai:response:{prompt_hash}")

    async def cache_ai_response(self, prompt_hash: str, response: Dict) -> bool:
        """Cache AI response."""
        return await self.set(
            f"ai:response:{prompt_hash}",
            response,
            ttl=self._ai_cache_ttl,
        )

    def hash_prompt(self, prompt: str, model: str, system_prompt: Optional[str] = None) -> str:
        """Generate hash for AI prompt."""
        data = f"{prompt}:{model}:{system_prompt or ''}"
        return hashlib.sha256(data.encode()).hexdigest()

    # User-specific caching

    async def get_user_data(self, user_id: str, key: str) -> Optional[Any]:
        """Get cached user data."""
        return await self.get(f"user:{user_id}:{key}")

    async def set_user_data(
        self,
        user_id: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache user data."""
        return await self.set(
            f"user:{user_id}:{key}",
            value,
            ttl=ttl or 300,  # 5 minutes default
        )

    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache for a user."""
        return await self.delete_pattern(f"user:{user_id}:*")

    # Rate limiting

    async def increment_rate_limit(self, key: str, window: int) -> int:
        """Increment rate limit counter."""
        if not self._enabled or not self._redis:
            return 0

        try:
            current = await self._redis.incr(key)
            if current == 1:
                await self._redis.expire(key, window)
            return current
        except Exception as e:
            logger.debug(f"Rate limit error: {e}")
            return 0

    async def get_rate_limit(self, key: str) -> int:
        """Get current rate limit count."""
        if not self._enabled or not self._redis:
            return 0

        try:
            value = await self._redis.get(key)
            return int(value) if value else 0
        except Exception:
            return 0


# Singleton instance
cache_service = CacheService()