"""
Professional AI - Offline Mode Routes
REST API endpoints for offline mode, voice, translation, sync, and cache management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import time
import io

from app.services.auth_service import AuthService, get_current_user
from app.services.connectivity import connectivity_service
from app.services.offline_engine import offline_engine
from app.services.ollama_client import ollama_client, OFFLINE_MODELS, OfflineModelType
from app.services.offline_voice import offline_voice_service
from app.services.offline_translation import offline_translation_service
from app.services.offline_cache import offline_cache
from app.services.sync_engine import cloud_sync_engine
from app.models.user import User

router = APIRouter(prefix="/api/offline", tags=["Offline Mode"])


# ===================================================================
# Schemas
# ===================================================================

class OfflineChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=100_000)
    mode: str = Field(default="chat", pattern="^(chat|code|security|bugfix)$")
    model: Optional[str] = Field(default=None, max_length=100)
    stream: bool = False


class OfflineVoiceRequest(BaseModel):
    audio_base64: Optional[str] = None
    language: str = Field(default="en", max_length=10)


class OfflineTranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000)
    source_lang: str = Field(default="en", max_length=10)
    target_lang: str = Field(..., max_length=10)


class OfflineSyncRequest(BaseModel):
    item_type: str = Field(..., max_length=50)
    data: Dict[str, Any]


# ===================================================================
# Offline Mode Status
# ===================================================================

@router.get("/status")
async def get_offline_status():
    """Get current offline mode status and capabilities."""
    return await offline_engine.get_status()


@router.get("/capabilities")
async def get_offline_capabilities(current_user: User = Depends(get_current_user)):
    """Get available offline capabilities."""
    return await offline_engine.get_capabilities()


# ===================================================================
# Offline AI Chat
# ===================================================================

@router.post("/chat")
async def offline_chat(
    request: Request,
    chat_request: OfflineChatRequest,
    current_user: User = Depends(get_current_user),
):
    """Send message using offline or online models based on connectivity."""
    if chat_request.stream:
        return StreamingResponse(
            offline_engine.stream_offline_response(
                prompt=chat_request.prompt,
                mode=chat_request.mode,
                model=chat_request.model,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    result = await offline_engine.generate_response(
        prompt=chat_request.prompt,
        mode=chat_request.mode,
        model=chat_request.model,
        stream=False,
    )
    return result


# ===================================================================
# Offline Voice (Vosk)
# ===================================================================

@router.post("/voice/transcribe")
async def offline_voice_transcribe(
    request: Request,
    voice_request: OfflineVoiceRequest,
    current_user: User = Depends(get_current_user),
):
    """Transcribe audio using offline Vosk (no internet required)."""
    import base64

    audio_data = None
    if voice_request.audio_base64:
        try:
            audio_data = base64.b64decode(voice_request.audio_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 audio data")

    if not audio_data:
        raise HTTPException(status_code=400, detail="No audio data provided")

    result = await offline_engine.transcribe_voice(
        audio_data=audio_data,
        language=voice_request.language,
    )
    return result


@router.get("/voice/languages")
async def get_voice_languages(current_user: User = Depends(get_current_user)):
    """Get supported languages for offline voice recognition."""
    return await offline_voice_service.get_supported_languages()


@router.post("/voice/models/download/{language_code}")
async def download_voice_model(
    language_code: str,
    current_user: User = Depends(get_current_user),
):
    """Download a Vosk model for offline voice recognition."""
    return await offline_voice_service.download_model(language_code)


@router.get("/voice/models/status")
async def get_voice_models_status(current_user: User = Depends(get_current_user)):
    """Get status of downloaded voice models."""
    return offline_voice_service.get_model_status()


# ===================================================================
# Offline Translation (Opus-MT)
# ===================================================================

@router.post("/translate")
async def offline_translate(
    request: Request,
    translation_request: OfflineTranslationRequest,
    current_user: User = Depends(get_current_user),
):
    """Translate text using offline opus-mt model."""
    result = await offline_engine.translate_text(
        text=translation_request.text,
        source_lang=translation_request.source_lang,
        target_lang=translation_request.target_lang,
    )
    return result


@router.get("/translate/languages")
async def get_translation_languages(current_user: User = Depends(get_current_user)):
    """Get supported translation language pairs."""
    return await offline_translation_service.get_supported_languages()


# ===================================================================
# Ollama Model Management
# ===================================================================

@router.get("/models")
async def list_offline_models(current_user: User = Depends(get_current_user)):
    """List available offline AI models."""
    available = await ollama_client.get_available_models()
    return {
        "available": available,
        "recommended": [
            {"name": m.name, "display_name": m.display_name, "type": m.model_type.value, "size_b": m.size_b}
            for m in OFFLINE_MODELS
        ],
    }


@router.post("/models/pull/{model_name}")
async def pull_offline_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Pull an Ollama model for offline use."""
    from app.middleware.security import InputSanitizer
    import re as _re
    # Validate model name to prevent path traversal / injection
    if not _re.match(r'^[a-z0-9][a-z0-9._:-]{1,100}$', model_name):
        raise HTTPException(status_code=400, detail="Invalid model name format")
    return await ollama_client.pull_model(model_name)


@router.delete("/models/{model_name}")
async def delete_offline_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
):
    """Delete an Ollama model from local storage."""
    from app.middleware.security import InputSanitizer
    import re as _re
    # Validate model name to prevent path traversal / injection
    if not _re.match(r'^[a-z0-9][a-z0-9._:-]{1,100}$', model_name):
        raise HTTPException(status_code=400, detail="Invalid model name format")
    # Only allow deleting known models
    allowed = {m.name for m in OFFLINE_MODELS}
    if model_name not in allowed:
        raise HTTPException(status_code=403, detail="Model deletion not permitted")
    return await ollama_client.delete_model(model_name)


# ===================================================================
# Cache Management
# ===================================================================

@router.get("/cache/stats")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    """Get offline cache statistics."""
    return offline_cache.get_stats()


@router.delete("/cache/clear")
async def clear_offline_cache(
    request: Request,
    tags: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
):
    """Clear offline cache, optionally filtered by tags."""
    tag_list = tags.split(",") if tags else None
    count = await offline_cache.clear(tags=tag_list)
    return {"cleared": count}


@router.post("/cache/cleanup")
async def cleanup_expired_cache(current_user: User = Depends(get_current_user)):
    """Remove expired cache entries."""
    count = await offline_cache.cleanup_expired()
    return {"cleaned": count}


# ===================================================================
# Sync Engine
# ===================================================================

@router.post("/sync/queue")
async def queue_for_sync(
    request: Request,
    sync_request: OfflineSyncRequest,
    current_user: User = Depends(get_current_user),
):
    """Queue data for cloud sync when internet returns."""
    result = await offline_engine.queue_for_sync(
        user_id=str(current_user.id),
        item_type=sync_request.item_type,
        data=sync_request.data,
    )
    return result


@router.post("/sync/now")
async def sync_now(current_user: User = Depends(get_current_user)):
    """Manually trigger sync of pending items."""
    if not await connectivity_service.is_online():
        raise HTTPException(status_code=400, detail="No internet connection available")
    return await cloud_sync_engine.sync_pending()


@router.get("/sync/status")
async def get_sync_status(current_user: User = Depends(get_current_user)):
    """Get sync status and pending item count."""
    return await cloud_sync_engine.get_sync_status()


# ===================================================================
# Low Bandwidth Mode
# ===================================================================

@router.post("/compress")
async def compress_response(
    request: Request,
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Compress API response for low bandwidth."""
    import gzip
    content = json.dumps(body)
    compressed = gzip.compress(content.encode("utf-8"))
    return {
        "compressed": True,
        "original_size": len(content),
        "compressed_size": len(compressed),
        "compression_ratio": round(len(compressed) / len(content), 3),
    }


@router.get("/ping")
async def ping_offline(current_user: User = Depends(get_current_user)):
    """Lightweight ping for connectivity check."""
    return {"status": "ok", "timestamp": time.time()}
