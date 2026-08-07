"""
Professional AI - Media Provider Key Rotation
Multi-key support for all media providers with automatic rotation
on rate-limit (429) or auth failure (401). Owner adds keys in .env
— no code change needed. Keys never expire.
"""

from __future__ import annotations

import time
from typing import List, Dict, Any, Optional


class ProviderKeyManager:
    """
    Generic multi-key rotation manager for any media provider.
    Used for: fal.ai, Replicate, Kling, Runway, ElevenLabs.
    """

    def __init__(
        self,
        keys: List[str],
        rate_limit_cooldown: float = 60.0,
        max_errors: int = 5,
    ):
        self._keys: List[str] = [k.strip() for k in keys if k.strip()]
        self._cooldown = rate_limit_cooldown
        self._max_errors = max_errors
        self._index: int = 0
        self._status: Dict[str, Dict[str, Any]] = {}

        for key in self._keys:
            self._status[key] = {
                "rate_limited_until": 0.0,
                "error_count": 0,
                "success_count": 0,
                "last_used": 0.0,
            }

    @property
    def total_keys(self) -> int:
        return len(self._keys)

    @property
    def active_keys(self) -> int:
        now = time.time()
        return sum(
            1 for k in self._keys
            if self._status[k]["rate_limited_until"] <= now
            and self._status[k]["error_count"] < self._max_errors
        )

    def get_active_key(self) -> Optional[str]:
        """Get next usable key, rotating automatically."""
        if not self._keys:
            return None

        now = time.time()
        for i in range(len(self._keys)):
            idx = (self._index + i) % len(self._keys)
            key = self._keys[idx]
            status = self._status[key]

            if status["rate_limited_until"] > now:
                continue
            if status["error_count"] >= self._max_errors:
                continue

            self._index = (idx + 1) % len(self._keys)
            status["last_used"] = now
            return key

        # All keys exhausted — soft reset
        for k in self._keys:
            self._status[k]["error_count"] = 0
            self._status[k]["rate_limited_until"] = 0.0

        self._index = 0
        return self._keys[0] if self._keys else None

    def mark_rate_limited(self, key: str, retry_after: float = 60.0):
        if key in self._status:
            self._status[key]["rate_limited_until"] = time.time() + retry_after

    def mark_error(self, key: str):
        if key in self._status:
            self._status[key]["error_count"] += 1

    def mark_success(self, key: str):
        if key in self._status:
            s = self._status[key]
            s["error_count"] = 0
            s["success_count"] += 1

    def get_status(self) -> Dict[str, Any]:
        now = time.time()
        return {
            "total_keys": len(self._keys),
            "active_keys": self.active_keys,
            "keys": [
                {
                    "prefix": k[:8] + "...",
                    "rate_limited": self._status[k]["rate_limited_until"] > now,
                    "errors": self._status[k]["error_count"],
                    "successes": self._status[k]["success_count"],
                }
                for k in self._keys
            ],
        }

    def reload(self, new_keys: List[str]):
        """Refresh keys from env (owner can add keys without restart)."""
        self._keys = [k.strip() for k in new_keys if k.strip()]
        for key in self._keys:
            if key not in self._status:
                self._status[key] = {
                    "rate_limited_until": 0.0,
                    "error_count": 0,
                    "success_count": 0,
                    "last_used": 0.0,
                }


class MediaKeyVault:
    """
    Central key vault for all media providers.
    Loads keys from comma-separated env vars.
    """

    def __init__(self):
        self.fal = ProviderKeyManager(getattr(settings, "FAL_KEYS", "").split(","))
        self.replicate = ProviderKeyManager(getattr(settings, "REPLICATE_KEYS", "").split(","))
        self.kling = ProviderKeyManager(getattr(settings, "KLING_KEYS", "").split(","))
        self.runway = ProviderKeyManager(getattr(settings, "RUNWAY_KEYS", "").split(","))
        self.elevenlabs = ProviderKeyManager(
            getattr(settings, "ELEVENLABS_KEYS", "").split(","),
            rate_limit_cooldown=120.0,
        )

    def get_status(self) -> Dict[str, Any]:
        return {
            "fal": self.fal.get_status(),
            "replicate": self.replicate.get_status(),
            "kling": self.kling.get_status(),
            "runway": self.runway.get_status(),
            "elevenlabs": self.elevenlabs.get_status(),
        }


# Lazy import to avoid circular
from app.config import settings  # noqa: E402

media_key_vault = MediaKeyVault()
