"""
Professional AI - AI Engine Service (PERMANENT API VAULT)
Thin wrapper around the Permanent Vault Router.
Multi-layer provider chain: Gemini → Groq → OpenRouter → Local ONNX.
The system NEVER stops and NEVER expires.
"""

import time
from typing import Optional, Dict, Any
from loguru import logger

from app.config import settings
from app.services.ai_router import ai_router, ModelType
from app.services.vault_health_monitor import vault_health_monitor
from app.services.unlimited_mode import accuracy_double_check


class AIResponse:
    """Structured AI response wrapper."""

    def __init__(self, content: str, model: str, provider: str, tokens: int, execution_time_ms: int):
        self.content = content
        self.model = model
        self.provider = provider
        self.tokens = tokens
        self.execution_time_ms = execution_time_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "provider": self.provider,
            "tokens": self.tokens,
            "execution_time_ms": self.execution_time_ms,
        }


class AIService:
    """
    Permanent Vault AI Service - routes through the provider chain with
    automatic failover, key rotation, and local fallback.
    """

    def __init__(self):
        self._router = ai_router

    async def close(self):
        """Close HTTP client."""
        await self._router.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start_health_monitor(self):
        """Start the vault health monitor (pings all providers every 60s)."""
        await vault_health_monitor.start()

    async def stop_health_monitor(self):
        """Stop the vault health monitor."""
        await vault_health_monitor.stop()

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        stream: bool = False,
        model_type: ModelType = ModelType.CHAT,
        use_cache: bool = True,
    ) -> AIResponse:
        """
        Generate AI response using the light provider chain with automatic failover.
        Includes accuracy double-check for accuracy-critical requests.
        """
        start_time = time.time()
        result = await self._router.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            model_type=model_type,
            use_cache=use_cache,
        )

        # UNLIMITED MODE: Accuracy double-check for accuracy-critical requests
        if accuracy_double_check.should_double_check(prompt, model_type.value):
            result = await accuracy_double_check.double_check(
                primary_result=result,
                prompt=prompt,
                system_prompt=system_prompt,
                model_type=model_type.value,
            )

        execution_time = int((time.time() - start_time) * 1000)
        return AIResponse(
            content=result.get("content", ""),
            model=result.get("model", "unknown"),
            provider=result.get("provider", "unknown"),
            tokens=result.get("tokens", 0),
            execution_time_ms=result.get("execution_time_ms", execution_time),
        )

    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        model_type: ModelType = ModelType.CHAT,
    ):
        """
        Stream AI response token by token (SSE format).
        """
        async for chunk in self._router.stream_response(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            model_type=model_type,
        ):
            yield chunk


# Singleton instance
ai_service = AIService()