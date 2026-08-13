"""
Professional AI - Vault Health Monitor (PERMANENT API VAULT)
Pings all providers every 60 seconds, marks dead ones inactive,
auto-revives when healthy. Runs as a background task.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)


class VaultHealthMonitor:
    """
    Background health monitor for the provider chain.
    - Pings all providers every VAULT_HEALTH_CHECK_INTERVAL_SECONDS (60s)
    - Marks dead providers inactive
    - Auto-revives providers when they respond healthy again
    """

    def __init__(self):
        self._interval = settings.VAULT_HEALTH_CHECK_INTERVAL_SECONDS
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._last_check: Optional[float] = None
        self._check_results: Dict[str, Dict[str, Any]] = {}
        self._provider_status: Dict[str, bool] = {}

    async def start(self):
        """Start the health monitor background task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Vault health monitor started (interval: {self._interval}s)")

    async def stop(self):
        """Stop the health monitor."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Vault health monitor stopped")

    async def _run_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self.check_all()
            except Exception as e:
                logger.warning(f"Vault health check failed: {e}")
            await asyncio.sleep(self._interval)

    async def check_all(self):
        """Ping all providers and update status."""
        self._last_check = time.time()
        logger.debug("Running vault health check...")

        results = {}

        # AI providers
        try:
            from app.services.ai_router import ai_router
            for provider in ai_router.providers:
                provider_name = provider.provider.value
                try:
                    healthy = await self._ping_provider(provider)
                    results[provider_name] = {
                        "healthy": healthy,
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                        "latency_ms": provider.avg_response_time * 1000,
                    }
                    self._provider_status[provider_name] = healthy
                    if healthy and not provider.is_healthy:
                        logger.info(f"Provider {provider_name} auto-revived!")
                    elif not healthy and provider.is_healthy:
                        logger.warning(f"Provider {provider_name} marked inactive")
                except Exception as e:
                    results[provider_name] = {
                        "healthy": False,
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                        "error": str(e),
                    }
                    self._provider_status[provider_name] = False
        except ImportError:
            pass

        # Media providers
        try:
            from app.services.media.provider_keys import media_key_vault
            media_providers = {
                "fal_ai": lambda: self._ping_url(f"{settings.FAL_AI_API_URL}/fal-ai/flux/dev", "GET"),
                "replicate": lambda: self._ping_url(f"{settings.REPLICATE_API_URL}/models", "GET"),
                "kling": lambda: self._ping_url(f"{settings.KLING_API_URL}/v1/status", "GET"),
                "runway": lambda: self._ping_url(f"{settings.RUNWAY_API_URL}/health", "GET"),
                "elevenlabs": lambda: self._ping_url("https://api.elevenlabs.io/v1/voices", "GET"),
                "comfyui": lambda: self._ping_url(f"{settings.COMFYUI_URL}/object_info", "GET"),
            }
            for name, ping_fn in media_providers.items():
                try:
                    healthy = await asyncio.wait_for(ping_fn(), timeout=5.0)
                    results[name] = {"healthy": healthy, "checked_at": datetime.now(timezone.utc).isoformat()}
                    self._provider_status[name] = healthy
                    if healthy:
                        logger.debug(f"Media provider {name} healthy")
                except Exception as e:
                    results[name] = {"healthy": False, "checked_at": datetime.now(timezone.utc).isoformat(), "error": str(e)}
                    self._provider_status[name] = False
        except ImportError:
            pass

        self._check_results = results
        logger.debug(f"Vault health check complete: {len(results)} providers checked")

    async def _ping_url(self, url: str, method: str = "GET") -> bool:
        """Ping a URL and return True if healthy."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                if method == "GET":
                    resp = await client.get(url)
                else:
                    resp = await client.post(url)
                return resp.status_code < 500
        except Exception:
            return False

    async def _ping_provider(self, provider) -> bool:
        """Ping a single provider with a lightweight request."""
        import httpx

        try:
            provider_name = provider.provider.value

            if provider_name == "gemini":
                url = f"{provider.base_url}/models"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(url, params={"key": provider.api_key})
                    return response.status_code == 200

            elif provider_name == "groq":
                url = f"{provider.base_url}/models"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {provider.api_key}"},
                    )
                    return response.status_code == 200

            elif provider_name == "openrouter":
                url = f"{provider.base_url}/models"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {provider.api_key}"},
                    )
                    return response.status_code == 200

            elif provider_name == "openai":
                url = f"{provider.base_url}/models"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {provider.api_key}"},
                    )
                    return response.status_code == 200

            elif provider_name == "anthropic":
                url = "https://api.anthropic.com/v1/messages"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(
                        url,
                        headers={
                            "x-api-key": provider.api_key,
                            "anthropic-version": "2023-06-01",
                        },
                    )
                    return response.status_code < 500

            elif provider_name == "deepseek":
                url = f"{provider.base_url}/models"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {provider.api_key}"},
                    )
                    return response.status_code == 200

            elif provider_name == "mistral":
                url = f"{provider.base_url}/models"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {provider.api_key}"},
                    )
                    return response.status_code == 200

            elif provider_name == "together":
                url = f"{provider.base_url}/models"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {provider.api_key}"},
                    )
                    return response.status_code == 200

            elif provider_name == "xai":
                url = f"{provider.base_url}/models"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {provider.api_key}"},
                    )
                    return response.status_code == 200

            elif provider_name == "stability":
                url = f"{provider.base_url}/engines/list"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {provider.api_key}"},
                    )
                    return response.status_code == 200

            elif provider_name == "ollama":
                url = f"{provider.base_url}/api/tags"
                async with httpx.AsyncClient(timeout=3.0) as client:
                    response = await client.get(url)
                    return response.status_code == 200

            return False
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get current health monitor status."""
        return {
            "running": self._running,
            "interval_seconds": self._interval,
            "last_check": self._last_check,
            "provider_status": self._provider_status,
            "check_results": self._check_results,
        }


# Global instance
vault_health_monitor = VaultHealthMonitor()