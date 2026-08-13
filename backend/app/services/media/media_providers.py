"""
Professional AI - Media Providers Configuration
Central registry of all media providers with model names, limits,
resolution options, cost per generation, and failover order.

Multi-key support: comma-separated keys in .env. Empty keys are silently skipped.
If a provider fails or rate-limits, auto-switch to the next provider in the chain.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from app.config import settings


# =====================================================================
# Media Types
# =====================================================================

class MediaType:
    IMAGE = "image"
    VIDEO = "video"
    POSTER = "poster"
    ANIMATION = "animation"


# =====================================================================
# Cost per generation (in credits)
# =====================================================================

COSTS = {
    "image": {
        "standard": 10,
        "hd": 15,
        "ultra": 25,
    },
    "video": {
        "short": 20,
        "medium": 40,
        "long": 80,
    },
    "poster": {
        "standard": 10,
        "hd": 15,
    },
    "animation": {
        "short": 15,
        "medium": 30,
        "long": 60,
    },
}


# =====================================================================
# Resolution presets (width x height)
# =====================================================================

RESOLUTIONS = {
    "720p": {"width": 1280, "height": 720, "label": "720p", "paid": False},
    "1080p": {"width": 1920, "height": 1080, "label": "1080p", "paid": True},
    "4k": {"width": 3840, "height": 2160, "label": "4K", "paid": True},
    "8k": {"width": 7680, "height": 4320, "label": "8K", "paid": True},
}


# =====================================================================
# Helper: load comma-separated keys from env
# =====================================================================

def _load_keys(env_var: str, fallback_single: Optional[str] = None) -> List[str]:
    keys_str = getattr(settings, env_var, "") or ""
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    if fallback_single:
        single = getattr(settings, fallback_single, None)
        if single and single.strip() and single.strip() not in keys:
            keys.insert(0, single.strip())
    return keys


# =====================================================================
# Provider Definitions
# =====================================================================

PROVIDERS: Dict[str, Dict[str, Any]] = {
    # -----------------------------------------------------------------
    # fal.ai — Video (Kling, MiniMax/Hailuo, Hunyuan, Veo 3) + Image (Flux, SDXL)
    # -----------------------------------------------------------------
    "fal_ai": {
        "name": "fal.ai",
        "type": ["image", "video"],
        "keys_env": "FAL_KEYS",
        "single_key_env": "FAL_AI_API_KEY",
        "api_url": getattr(settings, "FAL_AI_API_URL", "https://queue.fal.run"),
        "models": {
            "image": [
                {"id": "fal-ai/flux/dev", "name": "Flux Dev", "max_res": "2K", "cost": "standard"},
                {"id": "fal-ai/flux/schnell", "name": "Flux Schnell", "max_res": "2K", "cost": "standard"},
                {"id": "fal-ai/stable-diffusion-xl", "name": "SDXL", "max_res": "1K", "cost": "standard"},
                {"id": "fal-ai/playground-v2.5", "name": "Playground v2.5", "max_res": "1K", "cost": "standard"},
            ],
            "video": [
                {"id": "fal-ai/kling-video/v2.5", "name": "Kling v2.5", "max_duration": 10, "cost": "short"},
                {"id": "fal-ai/kling-video/v1.6", "name": "Kling 1.6", "max_duration": 10, "cost": "short"},
                {"id": "fal-ai/minimax/hailuo", "name": "Hailuo MiniMax", "max_duration": 6, "cost": "short"},
                {"id": "fal-ai/hunyuan-video", "name": "Hunyuan Video", "max_duration": 16, "cost": "medium"},
                {"id": "fal-ai/veo2", "name": "Veo 2", "max_duration": 8, "cost": "short"},
            ],
        },
        "max_duration_seconds": 60,
        "resolutions": ["720p", "1080p", "4k"],
        "cost_per_generation": {"image": 10, "video": 20},
        "failover_order": 1,
        "features": ["multi_key", "queue", "async"],
    },

    # -----------------------------------------------------------------
    # Stability AI — Direct API (image + video)
    # -----------------------------------------------------------------
    "stability_ai": {
        "name": "Stability AI",
        "type": ["image", "video"],
        "keys_env": "STABILITY_KEYS",
        "single_key_env": "STABILITY_API_KEY",
        "api_url": "https://api.stability.ai",
        "models": {
            "image": [
                {"id": "stable-diffusion-xl", "name": "SDXL", "max_res": "1K", "cost": "standard"},
                {"id": "stable-diffusion-3", "name": "SD3", "max_res": "1K", "cost": "hd"},
                {"id": "stable-image-core", "name": "SD Core", "max_res": "1K", "cost": "standard"},
            ],
            "video": [
                {"id": "stable-video-diffusion", "name": "SVD", "max_duration": 4, "cost": "short"},
                {"id": "stable-video-diffusion-img2vid", "name": "SVD Image-to-Video", "max_duration": 4, "cost": "short"},
            ],
        },
        "max_duration_seconds": 4,
        "resolutions": ["720p", "1080p"],
        "cost_per_generation": {"image": 10, "video": 20},
        "failover_order": 2,
        "features": ["direct_api"],
    },

    # -----------------------------------------------------------------
    # Runway Gen-3
    # -----------------------------------------------------------------
    "runway": {
        "name": "Runway Gen-3",
        "type": ["video"],
        "keys_env": "RUNWAY_KEYS",
        "single_key_env": "RUNWAY_API_KEY",
        "api_url": getattr(settings, "RUNWAY_API_URL", "https://api.dev.runwayml.com/v1"),
        "models": {
            "video": [
                {"id": "gen3a_turbo", "name": "Gen-3 Alpha Turbo", "max_duration": 10, "cost": "short"},
                {"id": "gen3a", "name": "Gen-3 Alpha", "max_duration": 10, "cost": "medium"},
                {"id": "gen2", "name": "Gen-2", "max_duration": 4, "cost": "short"},
            ],
        },
        "max_duration_seconds": 10,
        "resolutions": ["720p", "1080p"],
        "cost_per_generation": {"video": 20},
        "failover_order": 3,
        "features": ["multi_key", "task_polling"],
    },

    # -----------------------------------------------------------------
    # Kling AI (updated to kling-1.6)
    # -----------------------------------------------------------------
    "kling": {
        "name": "Kling AI",
        "type": ["video"],
        "keys_env": "KLING_KEYS",
        "single_key_env": "KLING_API_KEY",
        "api_url": getattr(settings, "KLING_API_URL", "https://api.klingai.com"),
        "models": {
            "video": [
                {"id": "kling-1.6", "name": "Kling 1.6", "max_duration": 10, "cost": "short"},
                {"id": "kling-v1", "name": "Kling v1 (legacy)", "max_duration": 5, "cost": "short"},
            ],
        },
        "default_model": "kling-1.6",
        "max_duration_seconds": 10,
        "resolutions": ["720p", "1080p"],
        "cost_per_generation": {"video": 20},
        "failover_order": 4,
        "features": ["multi_key", "task_polling"],
    },

    # -----------------------------------------------------------------
    # Luma Dream Machine
    # -----------------------------------------------------------------
    "luma": {
        "name": "Luma Dream Machine",
        "type": ["video"],
        "keys_env": "LUMA_KEYS",
        "single_key_env": "LUMA_API_KEY",
        "api_url": "https://api.lumalabs.ai",
        "models": {
            "video": [
                {"id": "dream-machine", "name": "Dream Machine", "max_duration": 5, "cost": "short"},
            ],
        },
        "max_duration_seconds": 5,
        "resolutions": ["720p", "1080p"],
        "cost_per_generation": {"video": 20},
        "failover_order": 5,
        "features": ["multi_key", "task_polling"],
    },

    # -----------------------------------------------------------------
    # Pika
    # -----------------------------------------------------------------
    "pika": {
        "name": "Pika",
        "type": ["video"],
        "keys_env": "PIKA_KEYS",
        "single_key_env": "PIKA_API_KEY",
        "api_url": "https://api.pika.art",
        "models": {
            "video": [
                {"id": "pika-1.0", "name": "Pika 1.0", "max_duration": 4, "cost": "short"},
            ],
        },
        "max_duration_seconds": 4,
        "resolutions": ["720p", "1080p"],
        "cost_per_generation": {"video": 20},
        "failover_order": 6,
        "features": ["multi_key", "task_polling"],
    },

    # -----------------------------------------------------------------
    # Hailuo MiniMax
    # -----------------------------------------------------------------
    "hailuo": {
        "name": "Hailuo MiniMax",
        "type": ["video"],
        "keys_env": "HAILUO_KEYS",
        "single_key_env": "HAILUO_API_KEY",
        "api_url": "https://api.minimax.chat",
        "models": {
            "video": [
                {"id": "hailuo-video", "name": "Hailuo Video", "max_duration": 6, "cost": "short"},
            ],
        },
        "max_duration_seconds": 6,
        "resolutions": ["720p", "1080p"],
        "cost_per_generation": {"video": 20},
        "failover_order": 7,
        "features": ["multi_key", "task_polling"],
    },

    # -----------------------------------------------------------------
    # Replicate — Backup images + video
    # -----------------------------------------------------------------
    "replicate": {
        "name": "Replicate",
        "type": ["image", "video", "animation"],
        "keys_env": "REPLICATE_KEYS",
        "single_key_env": "REPLICATE_API_KEY",
        "api_url": getattr(settings, "REPLICATE_API_URL", "https://api.replicate.com/v1"),
        "models": {
            "image": [
                {"id": "black-forest-labs/flux-dev", "name": "Flux Dev", "max_res": "2K", "cost": "standard"},
                {"id": "stability-ai/sdxl", "name": "SDXL", "max_res": "1K", "cost": "standard"},
                {"id": "playgroundai/playground-v2.5", "name": "Playground v2.5", "max_res": "1K", "cost": "standard"},
            ],
            "video": [
                {"id": "gen2", "name": "Runway Gen-2", "max_duration": 4, "cost": "short"},
                {"id": "pika/pika", "name": "Pika", "max_duration": 4, "cost": "short"},
            ],
            "animation": [
                {"id": "anotherjesse/zeroscope-v2-xl", "name": "Zeroscope v2 XL", "max_duration": 8, "cost": "medium"},
            ],
        },
        "max_duration_seconds": 30,
        "resolutions": ["720p", "1080p", "4k"],
        "cost_per_generation": {"image": 10, "video": 20, "animation": 15},
        "failover_order": 8,
        "features": ["multi_key", "task_polling"],
    },

    # -----------------------------------------------------------------
    # ElevenLabs — Voice Over (PRIMARY)
    # -----------------------------------------------------------------
    "elevenlabs": {
        "name": "ElevenLabs",
        "type": ["voice"],
        "keys_env": "ELEVENLABS_KEYS",
        "single_key_env": "ELEVENLABS_API_KEY",
        "api_url": "https://api.elevenlabs.io",
        "models": {
            "voice": [
                {"id": "eleven_multilingual_v2", "name": "Multilingual v2", "max_chars": 5000, "cost": "standard"},
                {"id": "eleven_turbo_v2_5", "name": "Turbo v2.5", "max_chars": 5000, "cost": "standard"},
            ],
        },
        "max_duration_seconds": 600,
        "cost_per_generation": {"voice": 5},
        "failover_order": 1,
        "features": ["multi_key", "voice_clone"],
    },

    # -----------------------------------------------------------------
    # Google Cloud TTS — Voice Over (BACKUP)
    # -----------------------------------------------------------------
    "google_tts": {
        "name": "Google Cloud TTS",
        "type": ["voice"],
        "keys_env": "GOOGLE_KEYS",
        "single_key_env": "GOOGLE_API_KEY",
        "api_url": "https://texttospeech.googleapis.com",
        "models": {
            "voice": [
                {"id": "en-US-Neural2-J", "name": "US English Male", "max_chars": 5000, "cost": "standard"},
                {"id": "en-US-Neural2-F", "name": "US English Female", "max_chars": 5000, "cost": "standard"},
                {"id": "en-GB-Neural2-A", "name": "UK English Male", "max_chars": 5000, "cost": "standard"},
            ],
        },
        "max_duration_seconds": 600,
        "cost_per_generation": {"voice": 5},
        "failover_order": 2,
        "features": ["multi_key"],
    },
}


# =====================================================================
# Failover Chains
# =====================================================================

FAILOVER_CHAINS: Dict[str, List[str]] = {
    "image": ["fal_ai", "stability_ai", "replicate"],
    "video": ["fal_ai", "runway", "kling", "luma", "pika", "hailuo", "replicate"],
    "poster": ["fal_ai", "stability_ai", "replicate"],
    "animation": ["fal_ai", "replicate"],
    "voice": ["elevenlabs", "google_tts"],
}


# =====================================================================
# Provider Registry
# =====================================================================

class MediaProviderRegistry:
    """
    Central registry for all media providers.
    Loads keys from comma-separated env vars. Empty keys are silently skipped.
    """

    def __init__(self):
        self._providers: Dict[str, Dict[str, Any]] = {}
        self._load_all()

    def _load_all(self):
        for pid, pconf in PROVIDERS.items():
            keys = _load_keys(pconf.get("keys_env", ""), pconf.get("single_key_env"))
            if not keys:
                continue
            self._providers[pid] = {
                **pconf,
                "keys": keys,
                "active_keys": len(keys),
            }

    @property
    def available_providers(self) -> List[str]:
        return [pid for pid, p in self._providers.items() if p.get("active_keys", 0) > 0]

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        return self._providers.get(provider_id)

    def get_failover_chain(self, media_type: str) -> List[str]:
        chain = FAILOVER_CHAINS.get(media_type, [])
        return [pid for pid in chain if pid in self._providers]

    def get_models(self, provider_id: str, media_type: str) -> List[Dict[str, Any]]:
        provider = self.get_provider(provider_id)
        if not provider:
            return []
        return provider.get("models", {}).get(media_type, [])

    def get_cost(self, provider_id: str, media_type: str, tier: str = "standard") -> int:
        provider = self.get_provider(provider_id)
        if not provider:
            return 10
        costs = provider.get("cost_per_generation", {})
        return costs.get(media_type, COSTS.get(media_type, {}).get(tier, 10))

    def get_resolutions(self, provider_id: str) -> List[str]:
        provider = self.get_provider(provider_id)
        if not provider:
            return list(RESOLUTIONS.keys())
        return provider.get("resolutions", list(RESOLUTIONS.keys()))

    def get_max_duration(self, provider_id: str) -> int:
        provider = self.get_provider(provider_id)
        if not provider:
            return 60
        return provider.get("max_duration_seconds", 60)

    def get_default_model(self, provider_id: str, media_type: str) -> Optional[str]:
        provider = self.get_provider(provider_id)
        if not provider:
            return None
        models = provider.get("models", {}).get(media_type, [])
        if models:
            return models[0]["id"]
        return provider.get("default_model")

    def get_status(self) -> Dict[str, Any]:
        return {
            "total_providers": len(PROVIDERS),
            "available_providers": len(self._providers),
            "providers": {
                pid: {
                    "name": p["name"],
                    "type": p["type"],
                    "keys": p.get("active_keys", 0),
                    "available": p.get("active_keys", 0) > 0,
                    "failover_order": p.get("failover_order", 999),
                }
                for pid, p in self._providers.items()
            },
            "failover_chains": {
                k: v for k, v in FAILOVER_CHAINS.items()
            },
        }


# Singleton
media_provider_registry = MediaProviderRegistry()
