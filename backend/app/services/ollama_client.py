"""
Professional AI - Ollama Client for Offline Mode
Integrates small local models: phi3-mini, qwen2.5:3b, llama3.2:3b, gemma2:2b,
qwen2.5-coder:3b for offline code generation.
"""

import asyncio
import time
import json
import hashlib
import httpx
from typing import Optional, Dict, Any, List, AsyncGenerator
from enum import Enum
from dataclasses import dataclass
from loguru import logger
from fastapi import HTTPException

from app.config import settings
from app.services.connectivity import connectivity_service, ConnectionQuality
from app.services.offline_cache import offline_cache


class OfflineModelType(Enum):
    CHAT = "chat"
    CODE = "code"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"


@dataclass
class OfflineModel:
    name: str
    display_name: str
    model_type: OfflineModelType
    size_b: int
    description: str
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


OFFLINE_MODELS = [
    OfflineModel(
        name="phi3:mini",
        display_name="Phi-3 Mini (1.8B)",
        model_type=OfflineModelType.CHAT,
        size_b=2,
        description="Lightweight chat model, excellent for general Q&A on any device.",
        tags=["chat", "fast", "low-resource"],
    ),
    OfflineModel(
        name="qwen2.5:3b",
        display_name="Qwen 2.5 (3B)",
        model_type=OfflineModelType.CHAT,
        size_b=3,
        description="Balanced chat model with good reasoning and instruction following.",
        tags=["chat", "reasoning", "balanced"],
    ),
    OfflineModel(
        name="llama3.2:3b",
        display_name="Llama 3.2 (3B)",
        model_type=OfflineModelType.CHAT,
        size_b=3,
        description="Meta's efficient 3B model with strong general-purpose chat.",
        tags=["chat", "meta", "efficient"],
    ),
    OfflineModel(
        name="gemma2:2b",
        display_name="Gemma 2 (2B)",
        model_type=OfflineModelType.CHAT,
        size_b=2,
        description="Google's compact model, runs well on phones and laptops.",
        tags=["chat", "google", "lightweight"],
    ),
    OfflineModel(
        name="qwen2.5-coder:3b",
        display_name="Qwen Coder 2.5 (3B)",
        model_type=OfflineModelType.CODE,
        size_b=3,
        description="Specialized for code generation, explanation, and debugging.",
        tags=["code", "programming", "fast"],
    ),
    OfflineModel(
        name="llama3.2:1b",
        display_name="Llama 3.2 (1B)",
        model_type=OfflineModelType.CHAT,
        size_b=1,
        description="Ultra-lightweight model for very low-resource devices.",
        tags=["chat", "ultra-light", "phone"],
    ),
]


class OllamaOfflineClient:
    """
    Client for Ollama with offline model support.
    Automatically switches to small local models when offline.
    """

    def __init__(self, base_url: Optional[str] = None):
        self._base_url = base_url or settings.OLLAMA_BASE_URL
        self._http_client: Optional[httpx.AsyncClient] = None
        self._available_models: List[str] = []
        self._default_chat_model = "qwen2.5:3b"
        self._default_code_model = "qwen2.5-coder:3b"
        self._default_translation_model = "qwen2.5:3b"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=10.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._http_client

    async def close(self):
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def check_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self._base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                self._available_models = [m["name"] for m in data.get("models", [])]
                return True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
        return False

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available offline models."""
        if not self._available_models:
            await self.check_available()
        return [
            {
                "name": m,
                "display_name": next(
                    (om.display_name for om in OFFLINE_MODELS if om.name == m),
                    m,
                ),
                "available": True,
            }
            for m in self._available_models
        ]

    async def ensure_model_available(self, model_name: str) -> bool:
        """Ensure model is pulled, pull if missing."""
        if model_name in self._available_models:
            return True

        try:
            client = await self._get_client()
            logger.info(f"Pulling Ollama model: {model_name}")
            response = await client.post(
                f"{self._base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=600.0,
            )
            if response.status_code == 200:
                self._available_models.append(model_name)
                return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
        return False

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_type: OfflineModelType = OfflineModelType.CHAT,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate response using offline Ollama model.
        Automatically selects best available model for the task type.
        """
        # Select appropriate model
        if not model:
            if model_type == OfflineModelType.CODE:
                model = self._default_code_model
            elif model_type == OfflineModelType.TRANSLATION:
                model = self._default_translation_model
            else:
                model = self._default_chat_model

        # Check cache first
        cache_key = f"ollama:{model}:{hashlib.md5((prompt + (system_prompt or '')).encode()).hexdigest()}"
        if not stream:
            cached = await offline_cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Offline cache hit for model {model}")
                return cached

        # Ensure model is available
        if not await self.ensure_model_available(model):
            raise HTTPException(
                status_code=503,
                detail=f"Model {model} not available. Please pull it first: ollama pull {model}",
            )

        client = await self._get_client()
        start_time = time.time()

        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "num_predict": 2048 if model_type == OfflineModelType.CODE else 1024,
                "top_p": 0.9,
                "num_ctx": 4096,
                **(options or {}),
            },
        }

        response = await client.post(
            f"{self._base_url}/api/generate",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()
        result = response.json()

        execution_time = int((time.time() - start_time) * 1000)
        tokens = result.get("eval_count", 0)

        response_data = {
            "content": result.get("response", ""),
            "model": model,
            "provider": "ollama-offline",
            "tokens": tokens,
            "execution_time_ms": execution_time,
            "offline": True,
        }

        # Cache the result
        if not stream:
            await offline_cache.set(
                cache_key,
                response_data,
                ttl=86400,  # 24 hours
                tags=["ollama", "offline", model],
            )

        return response_data

    async def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_type: OfflineModelType = OfflineModelType.CHAT,
    ) -> AsyncGenerator[str, None]:
        """Stream response from offline model."""
        if not model:
            model = self._default_chat_model

        if not await self.ensure_model_available(model):
            raise HTTPException(
                status_code=503,
                detail=f"Model {model} not available",
            )

        client = await self._get_client()
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": True,
            "options": {
                "temperature": 0.7,
                "num_predict": 2048,
                "top_p": 0.9,
                "num_ctx": 4096,
            },
        }

        response = await client.post(
            f"{self._base_url}/api/generate",
            json=payload,
            timeout=120.0,
        )
        response.raise_for_status()

        async for line in response.aiter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    if "response" in chunk:
                        yield chunk["response"]
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

    async def pull_model(self, model_name: str) -> Dict[str, Any]:
        """Pull a model from Ollama registry."""
        client = await self._get_client()
        start_time = time.time()

        try:
            response = await client.post(
                f"{self._base_url}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=600.0,
            )
            response.raise_for_status()
            result = response.json()

            if model_name not in self._available_models:
                self._available_models.append(model_name)

            return {
                "success": True,
                "model": model_name,
                "status": result.get("status", "pulled"),
                "time_ms": int((time.time() - start_time) * 1000),
            }
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return {
                "success": False,
                "model": model_name,
                "error": str(e),
                "time_ms": int((time.time() - start_time) * 1000),
            }

    async def delete_model(self, model_name: str) -> Dict[str, Any]:
        """Delete a model from local storage."""
        client = await self._get_client()
        try:
            response = await client.delete(
                f"{self._base_url}/api/delete",
                json={"name": model_name},
                timeout=30.0,
            )
            response.raise_for_status()
            if model_name in self._available_models:
                self._available_models.remove(model_name)
            return {"success": True, "model": model_name}
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            return {"success": False, "model": model_name, "error": str(e)}


ollama_client = OllamaOfflineClient()
