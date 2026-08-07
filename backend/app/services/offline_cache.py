"""
Professional AI - Offline Cache Service
Local file-based cache that works without internet or Redis.
Stores AI responses, translations, and other data for offline access.
"""

import json
import os
import time
import hashlib
import pickle
import gzip
import secrets
from typing import Optional, Any, Dict, List, Callable, Awaitable
from pathlib import Path
from dataclasses import dataclass, field
from loguru import logger
from datetime import datetime, timedelta

from app.config import settings


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float
    expires_at: float
    tags: List[str] = field(default_factory=list)
    encrypted: bool = False
    size_bytes: int = 0


class OfflineCacheService:
    """
    File-based cache for offline mode.
    Uses encrypted local storage with TTL support.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self._cache_dir = Path(cache_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "offline_cache",
        ))
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self._cache_dir / "index.json"
        self._index: Dict[str, Dict[str, Any]] = {}
        self._encryption_key: Optional[bytes] = None
        self._load_index()

    def _load_index(self):
        """Load cache index from disk."""
        if self._index_file.exists():
            try:
                with open(self._index_file, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self._index = {}

    def _save_index(self):
        """Save cache index to disk."""
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f, default=str)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")

    def _get_encryption_key(self) -> Optional[bytes]:
        """Get or create encryption key for offline data."""
        if self._encryption_key is None:
            key = settings.ENCRYPTION_KEY
            if key:
                try:
                    import base64
                    self._encryption_key = base64.urlsafe_b64decode(key.encode() + b"=")
                except Exception:
                    try:
                        self._encryption_key = key.encode()[:32].ljust(32, b"0")
                    except Exception:
                        self._encryption_key = None
        return self._encryption_key

    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt data with AES."""
        key = self._get_encryption_key()
        if not key:
            return data
        try:
            from cryptography.fernet import Fernet
            import base64
            key_b64 = base64.urlsafe_b64encode(key[:32])
            f = Fernet(key_b64)
            return f.encrypt(data)
        except Exception:
            return data

    def _decrypt(self, data: bytes) -> bytes:
        """Decrypt data with AES."""
        key = self._get_encryption_key()
        if not key:
            return data
        try:
            from cryptography.fernet import Fernet
            import base64
            key_b64 = base64.urlsafe_b64encode(key[:32])
            f = Fernet(key_b64)
            return f.decrypt(data)
        except Exception:
            return data

    def _key_to_path(self, key: str) -> Path:
        """Convert cache key to file path."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self._cache_dir / f"{key_hash}.cache"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._index:
            return None

        entry_data = self._index[key]
        expires_at = entry_data.get("expires_at", 0)
        if time.time() > expires_at:
            await self.delete(key)
            return None

        path = self._key_to_path(key)
        if not path.exists():
            del self._index[key]
            self._save_index()
            return None

        try:
            with open(path, "rb") as f:
                data = f.read()

            if entry_data.get("encrypted"):
                data = self._decrypt(data)

            if entry_data.get("compressed"):
                data = gzip.decompress(data)

            value = pickle.loads(data)
            return value
        except Exception as e:
            logger.debug(f"Cache get error for {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        tags: Optional[List[str]] = None,
        encrypt: bool = True,
        compress: bool = True,
    ) -> bool:
        """Set value in cache with TTL."""
        try:
            path = self._key_to_path(key)
            data = pickle.dumps(value)

            if compress and len(data) > 1024:
                data = gzip.compress(data)

            if encrypt and self._get_encryption_key():
                data = self._encrypt(data)
                encrypted = True
            else:
                encrypted = False

            with open(path, "wb") as f:
                f.write(data)

            self._index[key] = {
                "created_at": time.time(),
                "expires_at": time.time() + ttl,
                "tags": tags or [],
                "encrypted": encrypted,
                "compressed": compress and len(data) > 1024,
                "size_bytes": len(data),
            }
            self._save_index()
            return True
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            path = self._key_to_path(key)
            if path.exists():
                path.unlink()
            if key in self._index:
                del self._index[key]
                self._save_index()
            return True
        except Exception as e:
            logger.debug(f"Cache delete error for {key}: {e}")
            return False

    async def clear(self, tags: Optional[List[str]] = None) -> int:
        """Clear cache entries, optionally filtered by tags."""
        keys_to_delete = []
        for key, entry in self._index.items():
            if tags is None or any(tag in entry.get("tags", []) for tag in tags):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            await self.delete(key)

        return len(keys_to_delete)

    async def cleanup_expired(self) -> int:
        """Remove expired entries."""
        now = time.time()
        expired_keys = [
            key for key, entry in self._index.items()
            if now > entry.get("expires_at", 0)
        ]
        for key in expired_keys:
            await self.delete(key)
        return len(expired_keys)

    async def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], Awaitable[Any]],
        ttl: int = 3600,
        tags: Optional[List[str]] = None,
    ) -> Any:
        """Get from cache or fetch and cache if missing."""
        cached = await self.get(key)
        if cached is not None:
            logger.debug(f"Cache hit: {key}")
            return cached

        value = await fetch_func()
        await self.set(key, value, ttl=ttl, tags=tags)
        return value

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = sum(e.get("size_bytes", 0) for e in self._index.values())
        now = time.time()
        active = sum(1 for e in self._index.values() if now < e.get("expires_at", 0))
        expired = len(self._index) - active
        return {
            "total_entries": len(self._index),
            "active_entries": active,
            "expired_entries": expired,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "cache_dir": str(self._cache_dir),
        }

    def cached(self, ttl: int = 3600, key_prefix: str = "", tags: Optional[List[str]] = None):
        """Decorator to cache function results."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args if arg is not None)
                key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()) if v is not None)
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

                return await self.get_or_set(
                    cache_key,
                    lambda: func(*args, **kwargs),
                    ttl=ttl,
                    tags=tags,
                )
            return wrapper
        return decorator


offline_cache = OfflineCacheService()
