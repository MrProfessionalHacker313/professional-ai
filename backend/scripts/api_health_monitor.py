#!/usr/bin/env python3
"""
API Health Monitor
Checks AI providers every 30 seconds and reports active/inactive transitions.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Tuple

import httpx


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api_health_monitor")


@dataclass
class ProviderState:
    name: str
    active: bool = True
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None


class APIHealthMonitor:
    """Monitors self-hosted and optional cloud AI APIs."""

    def __init__(self) -> None:
        self.interval_seconds = 30
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

        self.providers: Dict[str, ProviderState] = {
            "ollama": ProviderState(name="ollama", active=True),
        }

        if self.gemini_api_key:
            self.providers["gemini"] = ProviderState(name="gemini", active=True)
        if self.openai_api_key:
            self.providers["openai"] = ProviderState(name="openai", active=True)
        if self.groq_api_key:
            self.providers["groq"] = ProviderState(name="groq", active=True)

    async def run(self) -> None:
        logger.info("API health monitor started with %s-second interval", self.interval_seconds)
        while True:
            await self._check_all_providers()
            await asyncio.sleep(self.interval_seconds)

    async def _check_all_providers(self) -> None:
        tasks = [self._check_provider(name) for name in self.providers.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for idx, result in enumerate(results):
            name = list(self.providers.keys())[idx]
            if isinstance(result, Exception):
                self._update_state(name, False, str(result))
                continue
            is_active, error = result
            self._update_state(name, is_active, error)

    def _update_state(self, name: str, is_active: bool, error: Optional[str]) -> None:
        state = self.providers[name]
        previous = state.active

        state.active = is_active
        state.last_check = datetime.utcnow()
        state.last_error = error

        if previous and not is_active:
            logger.warning("Provider %s is now inactive: %s", name, error)
        elif not previous and is_active:
            logger.info("Provider %s recovered and is active", name)
        else:
            logger.info("Provider %s status: %s", name, "active" if is_active else "inactive")

    async def _check_provider(self, name: str) -> Tuple[bool, Optional[str]]:
        timeout = httpx.Timeout(8.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if name == "ollama":
                response = await client.get(f"{self.ollama_base_url}/api/tags")
                return response.status_code == 200, None if response.status_code == 200 else f"HTTP {response.status_code}"

            if name == "gemini" and self.gemini_api_key:
                response = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": self.gemini_api_key},
                )
                return response.status_code == 200, None if response.status_code == 200 else f"HTTP {response.status_code}"

            if name == "openai" and self.openai_api_key:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.openai_api_key}"},
                )
                return response.status_code == 200, None if response.status_code == 200 else f"HTTP {response.status_code}"

            if name == "groq" and self.groq_api_key:
                response = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {self.groq_api_key}"},
                )
                return response.status_code == 200, None if response.status_code == 200 else f"HTTP {response.status_code}"

        return False, "Provider is not configured"


async def main() -> None:
    monitor = APIHealthMonitor()
    await monitor.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("API health monitor stopped")
