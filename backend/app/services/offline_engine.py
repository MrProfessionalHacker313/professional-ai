"""
Professional AI - Offline Mode Engine (LIGHT MODE)
Main coordinator for offline/low-internet mode.

LIGHT MODE BEHAVIOR:
- Online: use cloud free-tier providers (Gemini → Groq → OpenRouter)
- Offline: show saved/cached answers + queue the question, answer when online
- NO heavy local models. Zero RAM usage for Ollama on normal PCs.
"""

import asyncio
import time
import json
import hashlib
from typing import Optional, Dict, Any, List, AsyncGenerator, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass
from loguru import logger

from app.config import settings
from app.services.connectivity import connectivity_service, ConnectionQuality
from app.services.offline_voice import offline_voice_service
from app.services.offline_translation import offline_translation_service
from app.services.offline_cache import offline_cache
from app.services.sync_engine import cloud_sync_engine
from app.services.ai_service import ai_service


class OfflineMode(Enum):
    ONLINE = "online"
    LOW_BANDWIDTH = "low_bandwidth"
    OFFLINE = "offline"


@dataclass
class OfflineCapabilities:
    mode: OfflineMode
    ollama_available: bool
    voice_available: bool
    translation_available: bool
    available_models: List[str]
    supported_languages: List[str]
    compression_enabled: bool
    streaming_enabled: bool


class OfflineEngine:
    """
    Main offline mode coordinator (LIGHT MODE).
    - Detects connectivity
    - Online: cloud free-tier providers
    - Offline: cached answers + queue for later
    - Syncs queued questions when back online
    """

    def __init__(self):
        self._current_mode: OfflineMode = OfflineMode.ONLINE
        self._last_connectivity_check = 0
        self._cache_enabled = True
        self._compression_enabled = True
        self._streaming_enabled = True
        self._background_task: Optional[asyncio.Task] = None
        self._listeners: List[Callable[[OfflineMode], Awaitable[None]]] = []

    async def initialize(self):
        """Initialize offline engine."""
        # Check initial connectivity
        await connectivity_service.check_connectivity()
        await self._update_mode()

        # Start background monitoring
        await connectivity_service.start()
        await cloud_sync_engine.start()

        # Listen for connectivity changes
        connectivity_service.add_listener(self._on_connectivity_change)

        logger.info(f"Offline engine initialized in mode: {self._current_mode.value}")

    async def shutdown(self):
        """Shutdown offline engine."""
        if self._background_task:
            self._background_task.cancel()
        await connectivity_service.stop()
        await cloud_sync_engine.stop()
        logger.info("Offline engine shutdown")

    def add_listener(self, callback: Callable[[OfflineMode], Awaitable[None]]):
        """Add listener for mode changes."""
        self._listeners.append(callback)

    async def _on_connectivity_change(self, state):
        """Handle connectivity change."""
        old_mode = self._current_mode
        await self._update_mode()

        if old_mode != self._current_mode:
            logger.info(f"Mode changed: {old_mode.value} -> {self._current_mode.value}")
            await self._notify_listeners()

            # Auto-sync when coming back online
            if self._current_mode == OfflineMode.ONLINE:
                pending = await cloud_sync_engine.get_pending_count()
                if pending > 0:
                    logger.info(f"Auto-syncing {pending} pending items...")
                    asyncio.create_task(cloud_sync_engine.sync_pending())

    async def _update_mode(self):
        """Update current mode based on connectivity."""
        quality = await connectivity_service.get_quality()
        if quality == ConnectionQuality.OFFLINE:
            self._current_mode = OfflineMode.OFFLINE
        elif quality == ConnectionQuality.LOW_BANDWIDTH:
            self._current_mode = OfflineMode.LOW_BANDWIDTH
        else:
            self._current_mode = OfflineMode.ONLINE

    async def _notify_listeners(self):
        """Notify listeners of mode change."""
        for listener in self._listeners:
            try:
                await listener(self._current_mode)
            except Exception as e:
                logger.debug(f"Offline mode listener notification failed: {e}")

    def get_mode(self) -> OfflineMode:
        """Get current offline mode."""
        return self._current_mode

    def is_online(self) -> bool:
        """Check if online mode is active."""
        return self._current_mode != OfflineMode.OFFLINE

    def is_low_bandwidth(self) -> bool:
        """Check if in low bandwidth mode."""
        return self._current_mode == OfflineMode.LOW_BANDWIDTH

    async def get_capabilities(self) -> OfflineCapabilities:
        """Get current offline capabilities."""
        return OfflineCapabilities(
            mode=self._current_mode,
            ollama_available=False,  # Light mode: no local models
            voice_available=offline_voice_service is not None,
            translation_available=offline_translation_service is not None,
            available_models=[],  # No local models in light mode
            supported_languages=[m.get("language_code", "") for m in await offline_voice_service.get_supported_languages()],
            compression_enabled=self._compression_enabled,
            streaming_enabled=self._streaming_enabled,
        )

    async def generate_response(
        self,
        prompt: str,
        mode: str = "chat",
        model: Optional[str] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate AI response with automatic online/offline switching.
        Online -> cloud free-tier providers (Gemini → Groq → OpenRouter)
        Offline -> cached answers + queue the question for later
        """
        if self._current_mode == OfflineMode.OFFLINE or not await connectivity_service.is_online():
            return await self._generate_offline(prompt, mode, model, stream)
        elif self._current_mode == OfflineMode.LOW_BANDWIDTH:
            return await self._generate_low_bandwidth(prompt, mode, model, stream)
        else:
            return await self._generate_online(prompt, mode, model, stream)

    async def _generate_online(
        self, prompt: str, mode: str, model: Optional[str], stream: bool
    ) -> Dict[str, Any]:
        """Generate using cloud free-tier providers."""
        from app.routes.chat import SYSTEM_PROMPTS
        system_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["chat"])

        result = await ai_service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            stream=stream,
        )
        return result.to_dict()

    async def _generate_low_bandwidth(
        self, prompt: str, mode: str, model: Optional[str], stream: bool
    ) -> Dict[str, Any]:
        """Low bandwidth: try cloud with shorter timeout, fall back to cache."""
        # Try cloud first with a short timeout
        try:
            return await self._generate_online(prompt, mode, model, stream)
        except Exception as e:
            logger.warning(f"Low bandwidth cloud call failed: {e}. Using cache.")
            return await self._generate_offline(prompt, mode, model, stream)

    async def _generate_offline(
        self, prompt: str, mode: str, model: Optional[str], stream: bool
    ) -> Dict[str, Any]:
        """
        Offline (LIGHT MODE): show cached answer if available, otherwise
        queue the question and return a friendly message.
        """
        # 1. Try to find a cached answer
        cache_key = self._make_offline_cache_key(prompt, mode)
        cached = await offline_cache.get(cache_key)
        if cached is not None:
            logger.info(f"Offline: serving cached answer for question")
            cached["offline"] = True
            cached["cached"] = True
            return cached

        # 2. No cache - queue the question for when we're back online
        queued = await self.queue_for_sync(
            user_id="anonymous",
            item_type="ai_question",
            data={
                "prompt": prompt,
                "mode": mode,
                "model": model,
                "timestamp": time.time(),
            },
        )

        return {
            "content": (
                "You are offline. This question has been saved and will be answered "
                "automatically when you are back online. (LIGHT MODE - no local models)"
            ),
            "model": "offline-queue",
            "provider": "offline",
            "tokens": 0,
            "execution_time_ms": 0,
            "offline": True,
            "queued": True,
            "queue_id": queued.get("item_id"),
        }

    def _make_offline_cache_key(self, prompt: str, mode: str) -> str:
        """Create a deterministic cache key for offline answers."""
        raw = f"offline:{mode}:{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _get_offline_system_prompt(self, mode: str) -> str:
        """Get system prompt optimized for offline models."""
        prompts = {
            "chat": "You are Professional AI (PRO AI) running offline. Answer questions accurately and concisely. If you cannot answer, say so honestly.",
            "code": "You are an offline code assistant. Write complete, working code. Include imports and comments.",
            "security": "You are a cybersecurity expert running offline. Provide accurate security information and best practices.",
            "bugfix": "You are a bug fixer running offline. Identify root causes and provide complete fixes.",
        }
        return prompts.get(mode, prompts["chat"])

    async def stream_offline_response(
        self, prompt: str, mode: str = "chat", model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream offline response (simulated streaming of cached/queued answer)."""
        result = await self._generate_offline(prompt, mode, model, stream=False)
        content = result.get("content", "")
        chunk_size = 10
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield f"data: {json.dumps({'token': chunk})}\n\n"
            await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'done': True})}\n\n"

    async def transcribe_voice(
        self, audio_data: bytes, language: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe voice - uses online Whisper if available,
        falls back to offline Vosk.
        """
        if self._current_mode != OfflineMode.OFFLINE and await self._is_whisper_available():
            # Use online Whisper
            return await self._transcribe_online(audio_data, language)
        else:
            # Use offline Vosk
            return await offline_voice_service.transcribe(audio_data, language)

    async def _transcribe_online(self, audio_data: bytes, language: str) -> Dict[str, Any]:
        """Transcribe using online Whisper service."""
        # This would call the existing Whisper endpoint
        return {"text": "[Online transcription placeholder]", "offline": False}

    async def _is_whisper_available(self) -> bool:
        """Check if Whisper service is available."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{settings.WHISPER_API_URL}/health")
                return response.status_code == 200
        except Exception:
            return False

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str
    ) -> Dict[str, Any]:
        """
        Translate text - uses cloud API if online,
        falls back to offline opus-mt model.
        """
        if self._current_mode == OfflineMode.OFFLINE or not await connectivity_service.is_online():
            return await offline_translation_service.translate(text, source_lang, target_lang)
        else:
            # Could use cloud translation API here
            return await offline_translation_service.translate(text, source_lang, target_lang)

    def _compress_text(self, text: str) -> str:
        """Compress text for low bandwidth (basic implementation)."""
        # For a real implementation, use proper compression
        return text

    async def queue_for_sync(self, user_id: str, item_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Queue data for cloud sync when online."""
        item = await cloud_sync_engine.add_item(user_id, item_type, data)
        return {
            "item_id": item.id,
            "status": item.status,
            "queued_at": item.created_at,
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get full offline mode status."""
        capabilities = await self.get_capabilities()
        sync_status = await cloud_sync_engine.get_sync_status()
        connectivity = connectivity_service.get_state()

        return {
            "mode": self._current_mode.value,
            "engine": "light",
            "capabilities": {
                "ollama_available": False,  # Light mode: no local models
                "voice_available": capabilities.voice_available,
                "translation_available": capabilities.translation_available,
                "compression_enabled": capabilities.compression_enabled,
                "streaming_enabled": capabilities.streaming_enabled,
            },
            "connectivity": {
                "is_online": connectivity.is_online,
                "quality": connectivity.quality.value,
                "latency_ms": round(connectivity.latency_ms, 1),
            },
            "sync": sync_status,
            "cache_stats": offline_cache.get_stats(),
            "available_models": [],
        }


offline_engine = OfflineEngine()