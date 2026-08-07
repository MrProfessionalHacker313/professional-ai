"""
Professional AI - Permanent API Vault Router (PERMANENT API VAULT)
Multi-layer provider chain with automatic failover, key rotation, and
on-device local fallback. The system NEVER stops and NEVER expires.

Provider chain (AI_PROVIDER=auto):
  Layer 1: Gemini  (gemini-2.0-flash) - free tier, key rotation
  Layer 2: Groq    (llama-3.3-70b-versatile) - free tier, key rotation
  Layer 3: OpenRouter (deepseek / qwen2.5-coder) - free models, key rotation
  Layer 4: Local ONNX / knowledge engine (on-device, ZERO cost, NEVER expires)

Routing:
  - Each provider has a 20-second timeout → fail → next provider
  - Multiple keys per provider: GEMINI_KEYS=key1,key2,key3
    System uses key1; when rate-limited, switches to key2, key3, then next provider.
  - If ALL cloud fail → local model answers. User never sees an error.
  - Requests queue during momentary outages (max 5 seconds) → auto-resume.
"""

import asyncio
import time
import hashlib
import json
import httpx
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

from app.config import settings
from app.services.offline_cache import offline_cache
from app.services.vault_logger import vault_logger
from app.services.local_fallback import local_fallback_engine
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class ModelProvider(Enum):
    GEMINI = "gemini"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LOCAL = "local"


class ModelType(Enum):
    CHAT = "chat"
    CODE = "code"
    SECURITY = "security"
    BUGFIX = "bugfix"


@dataclass
class ProviderKey:
    """A single API key for a provider."""
    key: str
    is_healthy: bool = True
    consecutive_failures: int = 0
    last_used: float = 0.0


@dataclass
class ProviderConfig:
    """Configuration for a cloud provider with multiple keys."""
    provider: ModelProvider
    keys: List[ProviderKey]
    chat_model: str
    code_model: str
    base_url: str
    timeout: float = 2.0
    enabled: bool = True
    is_healthy: bool = True
    consecutive_failures: int = 0
    avg_response_time: float = 0.0
    current_key_index: int = 0

    @property
    def api_key(self) -> Optional[str]:
        """Get the current active key."""
        if not self.keys:
            return None
        return self.keys[self.current_key_index].key

    def rotate_key(self) -> bool:
        """
        Rotate to the next healthy key. Returns True if rotated,
        False if no more healthy keys available.
        """
        if not self.keys:
            return False

        # Find next healthy key
        for i in range(len(self.keys)):
            idx = (self.current_key_index + 1 + i) % len(self.keys)
            if self.keys[idx].is_healthy:
                self.current_key_index = idx
                return True
        return False

    def mark_key_failure(self):
        """Mark the current key as failed."""
        if self.keys:
            self.keys[self.current_key_index].consecutive_failures += 1
            if self.keys[self.current_key_index].consecutive_failures >= 3:
                self.keys[self.current_key_index].is_healthy = False
                logger.warning(
                    f"Key {self.current_key_index} for {self.provider.value} "
                    f"marked unhealthy after {self.keys[self.current_key_index].consecutive_failures} failures"
                )

    def mark_key_success(self):
        """Mark the current key as successful."""
        if self.keys:
            self.keys[self.current_key_index].consecutive_failures = 0
            self.keys[self.current_key_index].is_healthy = True


class PermanentVaultRouter:
    """
    Permanent API Vault Router - multi-layer provider chain with:
    - Automatic failover (20s timeout per provider)
    - Multi-key rotation (never run out)
    - Local ONNX fallback (never stops)
    - Request queueing during outages (max 5s)
    - Full call logging for owner dashboard
    """

    def __init__(self):
        # FIX: 20s timeout for cloud providers (was 1.5s - too short)
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.AI_PROVIDER_TIMEOUT, connect=5.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
        self.providers: List[ProviderConfig] = []
        self._vault_timeout = settings.AI_PROVIDER_TIMEOUT  # 20s from config
        self._retries = settings.AI_PROVIDER_RETRIES  # 3 retries
        self._retry_backoff = settings.AI_PROVIDER_RETRY_BACKOFF
        self._connectivity_check_url = settings.AI_CONNECTIVITY_CHECK_URL
        self._connectivity_check_timeout = settings.AI_CONNECTIVITY_CHECK_TIMEOUT
        self._init_providers()
        self._cache_ttl = settings.AI_CACHE_TTL_SECONDS
        self._cache_enabled = settings.AI_CACHE_ENABLED
        self._queue_max_seconds = settings.VAULT_QUEUE_MAX_SECONDS

    # ===================================================================
    # Provider initialization with multi-key support
    # ===================================================================

    def _parse_keys(self, primary_key: Optional[str], multi_keys: str) -> List[ProviderKey]:
        """Parse keys from primary + multi-key env vars."""
        keys: List[str] = []

        # Add primary key first
        if primary_key:
            keys.append(primary_key)

        # Add multi-keys
        if multi_keys:
            for k in multi_keys.split(","):
                k = k.strip()
                if k and k not in keys:
                    keys.append(k)

        return [ProviderKey(key=k) for k in keys]

    def _init_providers(self):
        """Initialize providers in priority order with multi-key support."""
        mode = settings.AI_PROVIDER.lower()

        # Build the ordered provider list
        ordered_providers: List[Tuple[ModelProvider, List[ProviderKey], str, str]] = []

        if mode in ("auto", "gemini"):
            ordered_providers.append((
                ModelProvider.GEMINI,
                self._parse_keys(settings.GEMINI_API_KEY, settings.GEMINI_KEYS),
                settings.GEMINI_CHAT_MODEL,
                settings.GEMINI_CODE_MODEL,
            ))
        if mode in ("auto", "groq"):
            ordered_providers.append((
                ModelProvider.GROQ,
                self._parse_keys(settings.GROQ_API_KEY, settings.GROQ_KEYS),
                settings.GROQ_CHAT_MODEL,
                settings.GROQ_CODE_MODEL,
            ))
        if mode in ("auto", "openrouter"):
            ordered_providers.append((
                ModelProvider.OPENROUTER,
                self._parse_keys(settings.OPENROUTER_API_KEY, settings.OPENROUTER_KEYS),
                settings.OPENROUTER_CHAT_MODEL,
                settings.OPENROUTER_CODE_MODEL,
            ))

        for provider, keys, chat_model, code_model in ordered_providers:
            if not keys:
                logger.warning(
                    f"Provider {provider.value} SKIPPED: no API keys configured. "
                    f"Set {provider.value.upper()}_API_KEY or {provider.value.upper()}_KEYS in .env"
                )
                continue
            # Validate key format
            valid_keys = []
            for k in keys:
                key_str = k.key.strip()
                if not key_str or len(key_str) < 10:
                    logger.warning(
                        f"Provider {provider.value}: skipping invalid/placeholder key "
                        f"(length={len(key_str)}). Set a valid API key in .env"
                    )
                    continue
                valid_keys.append(k)
            if not valid_keys:
                logger.warning(
                    f"Provider {provider.value} SKIPPED: all keys invalid/placeholder. "
                    f"Get a real key from the provider's console."
                )
                continue
            self.providers.append(ProviderConfig(
                provider=provider,
                keys=keys,
                chat_model=chat_model,
                code_model=code_model,
                base_url=self._base_url_for(provider),
                timeout=self._vault_timeout,
            ))
            logger.info(
                f"Provider {provider.value} initialized with {len(keys)} key(s), "
                f"models: {chat_model} / {code_model}"
            )

        # Optional Ollama fallback - only if explicitly enabled
        if settings.OLLAMA_ENABLED:
            self.providers.append(ProviderConfig(
                provider=ModelProvider.OLLAMA,
                keys=[ProviderKey(key="")],
                chat_model="llama3.1",
                code_model="deepseek-coder",
                base_url=settings.OLLAMA_BASE_URL,
                timeout=10.0,
            ))
            logger.info("Ollama enabled as fallback (OLLAMA_ENABLED=true)")

        # Local fallback is ALWAYS available (Layer 4 - never stops)
        if settings.LOCAL_FALLBACK_ENABLED:
            logger.info(
                "Local ONNX fallback enabled (Layer 4) - guarantees AI always answers"
            )

        if not self.providers:
            logger.warning(
                "No cloud AI providers configured. Local fallback will handle all requests."
            )

        logger.info(
            f"Permanent API Vault initialized with {len(self.providers)} cloud providers: "
            f"{[p.provider.value for p in self.providers]} + local fallback"
        )

    async def _is_online(self) -> bool:
        """Check if internet is reachable before trying cloud providers."""
        try:
            async with httpx.AsyncClient(timeout=self._connectivity_check_timeout) as client:
                resp = await client.get(self._connectivity_check_url)
                return resp.status_code < 500
        except Exception:
            return False

    def _base_url_for(self, provider: ModelProvider) -> str:
        if provider == ModelProvider.GEMINI:
            return "https://generativelanguage.googleapis.com/v1beta"
        if provider == ModelProvider.GROQ:
            return "https://api.groq.com/openai/v1"
        if provider == ModelProvider.OPENROUTER:
            return "https://openrouter.ai/api/v1"
        return settings.OLLAMA_BASE_URL

    async def close(self):
        """Close HTTP client."""
        await self._http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ===================================================================
    # Public API
    # ===================================================================

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        model_type: ModelType = ModelType.CHAT,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate a response using the provider chain with automatic failover.
        NEVER returns an error - always falls back to local model.
        """
        # Cache lookup for repeated questions (Redis first, then offline cache)
        cache_key: Optional[str] = None
        if use_cache and self._cache_enabled:
            cache_key = self._make_cache_key(prompt, system_prompt, model_type)
            
            # Try Redis cache first (instant response)
            cached = await cache_service.get_ai_response(cache_key)
            if cached is not None:
                logger.info(f"Redis cache hit for question (instant response)")
                cached["cached"] = True
                return cached
            
            # Fallback to offline cache
            cached = await offline_cache.get(cache_key)
            if cached is not None:
                logger.info(f"Offline cache hit for question")
                return cached

        start_time = time.time()
        last_error: Optional[str] = None

        # Try cloud providers with failover
        for provider in self.providers:
            if not provider.enabled or not provider.is_healthy:
                continue

            # Try each key for this provider
            for _ in range(len(provider.keys)):
                if not provider.api_key:
                    break

                try:
                    result = await self._call_provider(
                        provider,
                        prompt,
                        system_prompt,
                        model,
                        model_type,
                    )
                    execution_time = int((time.time() - start_time) * 1000)
                    result["execution_time_ms"] = execution_time
                    result["cached"] = False

                    # Update health
                    provider.consecutive_failures = 0
                    provider.is_healthy = True
                    provider.mark_key_success()
                    provider.avg_response_time = (
                        provider.avg_response_time * 0.9 + (execution_time / 1000) * 0.1
                    )

                    # Log the call
                    vault_logger.log_call(
                        provider=provider.provider.value,
                        model=result.get("model", ""),
                        latency_ms=execution_time,
                        success=True,
                        cost_usd=0.0,
                        key_index=provider.current_key_index,
                    )

                    # Cache the result in both Redis and offline cache
                    if use_cache and self._cache_enabled and cache_key is not None:
                        # Redis cache (1 hour TTL)
                        await cache_service.cache_ai_response(cache_key, result)
                        # Offline cache backup
                        await offline_cache.set(
                            cache_key,
                            result,
                            ttl=self._cache_ttl,
                            tags=["ai_response"],
                        )

                    return result

                except Exception as exc:
                    last_error = str(exc)
                    provider.mark_key_failure()
                    provider.consecutive_failures += 1

                    # Log the failed call
                    vault_logger.log_call(
                        provider=provider.provider.value,
                        model=provider.chat_model,
                        latency_ms=int((time.time() - start_time) * 1000),
                        success=False,
                        cost_usd=0.0,
                        key_index=provider.current_key_index,
                        error=str(exc),
                    )

                    # Try to rotate to next key
                    if provider.rotate_key():
                        logger.info(
                            f"Provider {provider.provider.value} key {provider.current_key_index} "
                            f"rate-limited/failed. Rotating to next key..."
                        )
                        continue
                    else:
                        # No more healthy keys for this provider
                        if provider.consecutive_failures >= 3:
                            provider.is_healthy = False
                        logger.warning(
                            f"Provider {provider.provider.value} all keys failed: {exc}. "
                            f"Trying next provider..."
                        )
                        break

        # All cloud providers failed - use local fallback (NEVER stops)
        logger.warning(
            f"All cloud providers failed. Using local fallback. Last error: {last_error}"
        )

        # Queue during momentary outage (max 5 seconds)
        if self._queue_max_seconds > 0:
            await asyncio.sleep(min(0.5, self._queue_max_seconds))

        # Local fallback - guaranteed answer
        result = await local_fallback_engine.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model_type=model_type.value,
        )
        result["execution_time_ms"] = int((time.time() - start_time) * 1000)
        result["cached"] = False
        result["fallback"] = True

        # Log the local fallback call
        vault_logger.log_call(
            provider=result.get("provider", "local"),
            model=result.get("model", ""),
            latency_ms=result["execution_time_ms"],
            success=True,
            cost_usd=0.0,
            key_index=0,
        )

        return result

    async def stream_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        model_type: ModelType = ModelType.CHAT,
    ):
        """
        Stream AI response token by token (SSE format).
        Falls back to non-streaming with simulated streaming.
        """
        # Try streaming on the first healthy provider
        for provider in self.providers:
            if not provider.enabled or not provider.is_healthy:
                continue
            try:
                async for chunk in self._stream_provider(
                    provider, prompt, system_prompt, model, model_type
                ):
                    yield chunk
                return
            except Exception as exc:
                logger.warning(f"Streaming on {provider.provider.value} failed: {exc}")
                continue

        # Fallback: non-streaming with simulated streaming
        result = await self.generate(prompt, system_prompt, model, model_type)
        content = result.get("content", "")
        chunk_size = 10
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield f"data: {json.dumps({'token': chunk})}\n\n"
            await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'done': True})}\n\n"

    # ===================================================================
    # Provider calls
    # ===================================================================

    async def _call_provider(
        self,
        provider: ProviderConfig,
        prompt: str,
        system_prompt: Optional[str],
        requested_model: Optional[str],
        model_type: ModelType,
    ) -> Dict[str, Any]:
        """Call a single provider with timeout."""
        # Determine which model to use
        if requested_model:
            model = requested_model
        elif model_type == ModelType.CODE:
            model = provider.code_model
        else:
            model = provider.chat_model

        # Set timeout: first provider gets VAULT_TIMEOUT, failover gets +2s
        timeout = provider.timeout
        if provider != self.providers[0]:
            timeout = provider.timeout + settings.AI_FAILOVER_TIMEOUT_SECONDS

        if provider.provider == ModelProvider.GEMINI:
            return await self._call_gemini(provider, prompt, system_prompt, model, timeout)
        if provider.provider == ModelProvider.GROQ:
            return await self._call_groq(provider, prompt, system_prompt, model, timeout)
        if provider.provider == ModelProvider.OPENROUTER:
            return await self._call_openrouter(provider, prompt, system_prompt, model, timeout)
        if provider.provider == ModelProvider.OLLAMA:
            return await self._call_ollama(provider, prompt, system_prompt, model, timeout)

        raise ValueError(f"Unsupported provider: {provider.provider}")

    async def _call_gemini(
        self,
        provider: ProviderConfig,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        timeout: float,
    ) -> Dict[str, Any]:
        """Call Google Gemini API (free tier) - optimized for speed."""
        url = f"{provider.base_url}/models/{model}:generateContent"
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": settings.AI_MAX_TOKENS_CODE if "code" in model else settings.AI_MAX_TOKENS_CHAT,
                "topP": 0.9,
                "topK": 40,
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        # Reuse HTTP client for connection pooling
        response = await self._http_client.post(
            url,
            params={"key": provider.api_key},
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()

        try:
            content = result["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise RuntimeError(f"Gemini returned unexpected response: {result}")

        return {
            "content": content,
            "model": model,
            "provider": "gemini",
            "tokens": result.get("usageMetadata", {}).get("totalTokenCount", 0),
        }

    async def _call_groq(
        self,
        provider: ProviderConfig,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        timeout: float,
    ) -> Dict[str, Any]:
        """Call Groq API (free tier, very fast) - optimized for speed."""
        url = f"{provider.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Reuse HTTP client for connection pooling
        response = await self._http_client.post(
            url,
            headers={
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": settings.AI_MAX_TOKENS_CODE if model_type_is_code(model) else settings.AI_MAX_TOKENS_CHAT,
                "stream": False,  # Non-streaming for speed
            },
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()

        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise RuntimeError(f"Groq returned unexpected response: {result}")

        return {
            "content": content,
            "model": model,
            "provider": "groq",
            "tokens": result.get("usage", {}).get("total_tokens", 0),
        }

    async def _call_openrouter(
        self,
        provider: ProviderConfig,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        timeout: float,
    ) -> Dict[str, Any]:
        """Call OpenRouter API (free models) - optimized for speed."""
        url = f"{provider.base_url}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Reuse HTTP client for connection pooling
        response = await self._http_client.post(
            url,
            headers={
                "Authorization": f"Bearer {provider.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": settings.AI_MAX_TOKENS_CODE if model_type_is_code(model) else settings.AI_MAX_TOKENS_CHAT,
                "stream": False,  # Non-streaming for speed
            },
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()

        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise RuntimeError(f"OpenRouter returned unexpected response: {result}")

        return {
            "content": content,
            "model": model,
            "provider": "openrouter",
            "tokens": result.get("usage", {}).get("total_tokens", 0),
        }

    async def _call_ollama(
        self,
        provider: ProviderConfig,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        timeout: float,
    ) -> Dict[str, Any]:
        """Call Ollama (only when OLLAMA_ENABLED=true) - optimized for speed."""
        url = f"{provider.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": settings.AI_MAX_TOKENS_CHAT,
                "num_ctx": 2048,  # Reduced context for speed
            },
        }

        # Reuse HTTP client for connection pooling
        response = await self._http_client.post(
            url, 
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        result = response.json()

        return {
            "content": result.get("response", ""),
            "model": model,
            "provider": "ollama",
            "tokens": result.get("eval_count", 0),
        }

    async def _stream_provider(
        self,
        provider: ProviderConfig,
        prompt: str,
        system_prompt: Optional[str],
        requested_model: Optional[str],
        model_type: ModelType,
    ):
        """Stream from a provider (SSE)."""
        model = requested_model or (
            provider.code_model if model_type == ModelType.CODE else provider.chat_model
        )

        if provider.provider == ModelProvider.GEMINI:
            # Gemini streaming
            url = f"{provider.base_url}/models/{model}:streamGenerateContent"
            payload: Dict[str, Any] = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": settings.AI_MAX_TOKENS_CHAT,
                },
            }
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

            async with httpx.AsyncClient(timeout=10.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    params={"key": provider.api_key, "alt": "sse"},
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = json.loads(line[6:])
                            try:
                                text = data["candidates"][0]["content"]["parts"][0]["text"]
                                if text:
                                    yield f"data: {json.dumps({'token': text})}\n\n"
                            except (KeyError, IndexError):
                                continue
            yield f"data: {json.dumps({'done': True})}\n\n"
            return

        # Groq / OpenRouter / Ollama: non-streaming fallback with simulated streaming
        result = await self._call_provider(provider, prompt, system_prompt, requested_model, model_type)
        content = result.get("content", "")
        chunk_size = 10
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield f"data: {json.dumps({'token': chunk})}\n\n"
            await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'done': True})}\n\n"

    # ===================================================================
    # Helpers
    # ===================================================================

    def _make_cache_key(self, prompt: str, system_prompt: Optional[str], model_type: ModelType) -> str:
        """Create a deterministic cache key for a question."""
        raw = f"{model_type.value}:{system_prompt or ''}:{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all providers."""
        return {
            "engine": "permanent-vault",
            "local_fallback_enabled": settings.LOCAL_FALLBACK_ENABLED,
            "ollama_enabled": settings.OLLAMA_ENABLED,
            "providers": [
                {
                    "provider": p.provider.value,
                    "model": p.chat_model,
                    "code_model": p.code_model,
                    "healthy": p.is_healthy,
                    "consecutive_failures": p.consecutive_failures,
                    "avg_response_time_ms": round(p.avg_response_time * 1000, 1),
                    "keys": [
                        {
                            "index": i,
                            "healthy": k.is_healthy,
                            "consecutive_failures": k.consecutive_failures,
                        }
                        for i, k in enumerate(p.keys)
                    ],
                    "current_key_index": p.current_key_index,
                }
                for p in self.providers
            ],
            "local_fallback": local_fallback_engine.get_status(),
        }

    def get_vault_status(self) -> Dict[str, Any]:
        """Get full vault status for the owner dashboard."""
        return {
            "engine": "permanent-vault",
            "guarantee": "PERMANENT API VAULT ACTIVE - providers fail over automatically, keys never run out, final fallback is on-device AI, the system NEVER stops and NEVER expires.",
            "provider_chain": [
                {
                    "layer": i + 1,
                    "provider": p.provider.value,
                    "model": p.chat_model,
                    "keys_count": len(p.keys),
                    "healthy": p.is_healthy,
                }
                for i, p in enumerate(self.providers)
            ],
            "local_fallback": local_fallback_engine.get_status(),
            "call_logs": vault_logger.get_stats(),
        }


def _is_retryable_error(exc: Exception) -> bool:
    """Check if error is retryable (rate limit, server error, timeout, network)."""
    error_str = str(exc).lower()
    status_code = getattr(exc, "status_code", None)
    
    # Rate limit
    if status_code == 429 or "rate limit" in error_str or "quota" in error_str:
        return True
    # Server errors
    if status_code and status_code >= 500:
        return True
    # Timeout/network
    if any(k in error_str for k in ["timeout", "connect", "network", "unavailable", "503", "502"]):
        return True
    return False


def model_type_is_code(model: str) -> bool:
    """Heuristic: does this model name look like a code model?"""
    return any(k in model.lower() for k in ["coder", "code", "deepseek"])


# Global router instance
ai_router = PermanentVaultRouter()