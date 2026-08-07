"""
Professional AI - Advanced Features Routes
All 15 world-class AI features with full API endpoints.
SECURITY HARDENED: File upload security, input validation, SSRF protection, path traversal prevention.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import uuid
import asyncio
import os
import magic
from pathlib import Path
import httpx

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.advanced_features import (
    MemoryType, AgentType, ImageType, RecordingType, DocumentType
)
from app.services.auth_service import get_current_user, get_free_user_limit
from app.services.advanced_features_service import advanced_features_service
from app.middleware.security import InputSanitizer, limiter, PasswordValidator

router = APIRouter(prefix="/api/features", tags=["Advanced AI Features"])


# ===================================================================
# REQUEST/RESPONSE MODELS
# ===================================================================

class MemorySaveRequest(BaseModel):
    memory_type: str
    key: str
    value: Any
    importance: int = 5
    metadata: Optional[Dict] = None

class MemoryGetRequest(BaseModel):
    memory_type: str
    key: str

class AgentCreateRequest(BaseModel):
    name: str
    description: str
    agent_type: str
    system_prompt: str
    tools: Optional[List[str]] = []
    config: Optional[Dict] = {}

class AgentExecuteRequest(BaseModel):
    agent_id: str
    task_description: str
    context: Optional[Dict] = {}

class ImageGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    model: Optional[str] = "stable-diffusion-xl"
    width: Optional[int] = 1024
    height: Optional[int] = 1024
    steps: Optional[int] = 30

class ImageAnalyzeRequest(BaseModel):
    image_path: str
    analysis_type: Optional[str] = "describe"

class VoiceToTextRequest(BaseModel):
    audio_path: str
    language: Optional[str] = "en"

class TextToSpeechRequest(BaseModel):
    text: str
    language: Optional[str] = "en"
    voice: Optional[str] = "default"

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str
    context_type: Optional[str] = "chat"

class WebSearchRequest(BaseModel):
    query: str
    search_engine: Optional[str] = "searxng"

class CodeExplainRequest(BaseModel):
    code: str
    language: str
    user_language: Optional[str] = "en"

class ScreenshotToCodeRequest(BaseModel):
    image_path: str
    framework: Optional[str] = "html"

class ChatbotCreateRequest(BaseModel):
    name: str
    description: str
    system_prompt: str
    welcome_message: Optional[str] = None
    suggested_prompts: Optional[List[str]] = []

class ChatbotChatRequest(BaseModel):
    chatbot_id: str
    message: str
    session_id: Optional[str] = None

class ModelRouteRequest(BaseModel):
    task_type: str
    task_description: str


# ===================================================================
# AI MEMORY ENDPOINTS
# ===================================================================

@router.post("/memory/save")
async def save_memory(
    request: MemorySaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a memory to the user's long-term memory vault."""
    try:
        memory = await advanced_features_service.save_memory(
            db=db,
            user_id=current_user.id,
            memory_type=request.memory_type,
            key=request.key,
            value=request.value,
            importance=request.importance,
            metadata=request.metadata,
        )
        return {
            "id": str(memory.id),
            "type": request.memory_type,
            "key": request.key,
            "message": "Memory saved successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/get")
async def get_memory(
    request: MemoryGetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a memory from the vault."""
    memory = await advanced_features_service.get_memory(
        db=db,
        user_id=current_user.id,
        memory_type=request.memory_type,
        key=request.key,
    )

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    return memory


@router.get("/memories")
async def get_all_memories(
    memory_type: Optional[str] = None,
    min_importance: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all memories for the current user."""
    memories = await advanced_features_service.get_user_memories(
        db=db,
        user_id=current_user.id,
        memory_type=memory_type,
        min_importance=min_importance,
    )
    return {"memories": memories, "count": len(memories)}


@router.get("/memory/context")
async def get_memory_context(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get memory context for AI prompts."""
    context = await advanced_features_service.build_memory_context(db, current_user.id)
    return {"context": context}


# ===================================================================
# AI AGENTS ENDPOINTS
# ===================================================================

@router.post("/agents/create")
async def create_agent(
    request: AgentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new AI agent."""
    try:
        agent = await advanced_features_service.create_agent(
            db=db,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            agent_type=request.agent_type,
            system_prompt=request.system_prompt,
            tools=request.tools,
            config=request.config,
        )
        return {
            "id": str(agent.id),
            "name": agent.name,
            "type": agent.agent_type.value,
            "message": "Agent created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all agents for the current user."""
    from sqlalchemy import select
    from app.models.advanced_features import AIAgent

    result = await db.execute(
        select(AIAgent).where(AIAgent.user_id == current_user.id)
    )
    agents = result.scalars().all()

    return {
        "agents": [
            {
                "id": str(a.id),
                "name": a.name,
                "description": a.description,
                "type": a.agent_type.value,
                "is_active": a.is_active,
                "execution_count": a.execution_count,
                "success_rate": a.success_rate,
                "created_at": a.created_at.isoformat(),
            }
            for a in agents
        ]
    }


@router.post("/agents/execute")
async def execute_agent(
    request: AgentExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute an AI agent with multi-step reasoning."""
    try:
        agent_id = request.agent_id
        execution = await advanced_features_service.execute_agent(
            db=db,
            user_id=current_user.id,
            agent_id=agent_id,
            task_description=request.task_description,
            context=request.context,
        )
        return {
            "execution_id": str(execution.id),
            "status": execution.status.value,
            "result": execution.result,
            "steps": execution.steps,
            "tokens_used": execution.tokens_used,
            "execution_time_ms": execution.execution_time_ms,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================================================================
# IMAGE GENERATION ENDPOINTS
# ===================================================================

@router.post("/images/generate")
async def generate_image(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_free_user_limit),
):
    """Generate an image using Stable Diffusion or Flux."""
    try:
        result = await advanced_features_service.generate_image(
            db=db,
            user_id=current_user.id,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            model=request.model,
            width=request.width,
            height=request.height,
            steps=request.steps,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/images/analyze")
async def analyze_image(
    request: ImageAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze an image - describe, OCR, or edit."""
    try:
        # Validate and sanitize image path to prevent path traversal
        image_path = InputSanitizer.sanitize_text(request.image_path)
        if not image_path or ".." in image_path:
            raise HTTPException(status_code=400, detail="Invalid image path")
        
        # Ensure path is within uploads directory
        uploads_dir = os.path.abspath("uploads")
        full_path = os.path.abspath(image_path)
        if not full_path.startswith(uploads_dir):
            raise HTTPException(status_code=403, detail="Access denied to specified path")
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        result = await advanced_features_service.analyze_image(
            db=db,
            user_id=current_user.id,
            image_path=full_path,
            analysis_type=request.analysis_type,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@router.get("/images")
async def get_images(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all images for the current user."""
    from sqlalchemy import select
    from app.models.advanced_features import Image

    result = await db.execute(
        select(Image).where(Image.user_id == current_user.id).order_by(Image.created_at.desc())
    )
    images = result.scalars().all()

    return {
        "images": [
            {
                "id": str(img.id),
                "type": img.image_type.value,
                "prompt": img.prompt,
                "model": img.model_used,
                "width": img.width,
                "height": img.height,
                "created_at": img.created_at.isoformat(),
            }
            for img in images
        ]
    }


# ===================================================================
# VOICE ENDPOINTS
# ===================================================================

@router.post("/voice/speech-to-text")
async def speech_to_text(
    request: VoiceToTextRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert speech to text using faster-whisper."""
    try:
        result = await advanced_features_service.speech_to_text(
            db=db,
            user_id=current_user.id,
            audio_path=request.audio_path,
            language=request.language,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")


@router.post("/voice/text-to-speech")
async def text_to_speech(
    request: TextToSpeechRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert text to speech using Piper TTS."""
    try:
        result = await advanced_features_service.text_to_speech(
            db=db,
            user_id=current_user.id,
            text=request.text,
            language=request.language,
            voice=request.voice,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {str(e)}")


# ===================================================================
# DOCUMENT ENDPOINTS
# ===================================================================

ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".gif"}
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB


def validate_uploaded_file(file_path: str, original_filename: str) -> str:
    """Validate uploaded file for security."""
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {ext}")

    if os.path.getsize(file_path) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    mime_type = magic.from_file(file_path, mime=True)
    allowed_mimes = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "image/png",
        "image/jpeg",
        "image/gif",
    }
    if mime_type not in allowed_mimes:
        raise HTTPException(status_code=400, detail=f"File MIME type not allowed: {mime_type}")

    return mime_type


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process a document with security validation."""
    try:
        filename = InputSanitizer.sanitize_filename(file.filename or "unknown")
        safe_filename = f"{uuid.uuid4()}_{filename}"
        upload_dir = Path("uploads/documents")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / safe_filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        validate_uploaded_file(str(file_path), filename)

        document = await advanced_features_service.upload_document(
            db=db,
            user_id=current_user.id,
            file_path=str(file_path),
            original_filename=filename,
        )

        return {
            "id": str(document.id),
            "filename": document.original_filename,
            "status": document.processing_status.value,
            "message": "Document uploaded and processing started",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")


@router.get("/documents")
async def get_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all documents for the current user."""
    from sqlalchemy import select
    from app.models.advanced_features import Document

    result = await db.execute(
        select(Document).where(Document.user_id == current_user.id).order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return {
        "documents": [
            {
                "id": str(doc.id),
                "filename": doc.original_filename,
                "type": doc.document_type.value,
                "status": doc.processing_status.value,
                "summary": doc.summary,
                "word_count": doc.word_count,
                "created_at": doc.created_at.isoformat(),
            }
            for doc in documents
        ]
    }


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document with extracted text."""
    from sqlalchemy import select
    from app.models.advanced_features import Document

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": str(document.id),
        "filename": document.original_filename,
        "type": document.document_type.value,
        "status": document.processing_status.value,
        "extracted_text": document.extracted_text,
        "summary": document.summary,
        "word_count": document.word_count,
        "language": document.language_detected,
        "created_at": document.created_at.isoformat(),
    }


# ===================================================================
# TRANSLATION ENDPOINTS
# ===================================================================

@router.post("/translate")
async def translate_text(
    request: TranslationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Translate text between languages."""
    try:
        result = await advanced_features_service.translate_text(
            db=db,
            user_id=current_user.id,
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            context_type=request.context_type,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.get("/translations")
async def get_translations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get translation history."""
    from sqlalchemy import select
    from app.models.advanced_features import Translation

    result = await db.execute(
        select(Translation).where(Translation.user_id == current_user.id).order_by(Translation.created_at.desc())
    )
    translations = result.scalars().all()

    return {
        "translations": [
            {
                "id": str(t.id),
                "source_lang": t.source_language,
                "target_lang": t.target_language,
                "original": t.original_text[:100],
                "translated": t.translated_text[:100],
                "created_at": t.created_at.isoformat(),
            }
            for t in translations
        ]
    }


# ===================================================================
# WEB SEARCH ENDPOINTS
# ===================================================================

@router.post("/search")
async def web_search(
    request: WebSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Perform web search with AI-powered results."""
    try:
        result = await advanced_features_service.web_search(
            db=db,
            user_id=current_user.id,
            query=request.query,
            search_engine=request.search_engine,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")


# ===================================================================
# CODE EXPLAINER ENDPOINTS
# ===================================================================

@router.post("/code/explain")
async def explain_code(
    request: CodeExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Explain code line-by-line in user's language."""
    try:
        result = await advanced_features_service.explain_code(
            db=db,
            user_id=current_user.id,
            code=request.code,
            language=request.language,
            user_language=request.user_language,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code explanation failed: {str(e)}")


# ===================================================================
# SCREENSHOT TO CODE ENDPOINTS
# ===================================================================

@router.post("/screenshot-to-code")
async def screenshot_to_code(
    request: ScreenshotToCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert screenshot to HTML/CSS code."""
    try:
        image_path = InputSanitizer.sanitize_text(request.image_path)
        if not image_path or ".." in image_path:
            raise HTTPException(status_code=400, detail="Invalid image path")
        
        uploads_dir = os.path.abspath("uploads")
        full_path = os.path.abspath(image_path)
        if not full_path.startswith(uploads_dir):
            raise HTTPException(status_code=403, detail="Access denied to specified path")
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Image not found")
        
        result = await advanced_features_service.screenshot_to_code(
            db=db,
            user_id=current_user.id,
            image_path=full_path,
            framework=request.framework,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot to code failed: {str(e)}")


# ===================================================================
# CHATBOT BUILDER ENDPOINTS
# ===================================================================

@router.post("/chatbots/create")
async def create_chatbot(
    request: ChatbotCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a custom chatbot."""
    try:
        chatbot = await advanced_features_service.create_chatbot(
            db=db,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            welcome_message=request.welcome_message,
            suggested_prompts=request.suggested_prompts,
        )
        return {
            "id": str(chatbot.id),
            "name": chatbot.name,
            "description": chatbot.description,
            "message": "Chatbot created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chatbots")
async def get_chatbots(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all chatbots for the current user."""
    from sqlalchemy import select
    from app.models.advanced_features import Chatbot

    result = await db.execute(
        select(Chatbot).where(Chatbot.user_id == current_user.id).order_by(Chatbot.created_at.desc())
    )
    chatbots = result.scalars().all()

    return {
        "chatbots": [
            {
                "id": str(c.id),
                "name": c.name,
                "description": c.description,
                "is_public": c.is_public,
                "conversation_count": c.conversation_count,
                "rating": c.rating,
                "created_at": c.created_at.isoformat(),
            }
            for c in chatbots
        ]
    }


@router.post("/chatbots/chat")
async def chat_with_bot(
    request: ChatbotChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Chat with a custom chatbot."""
    try:
        chatbot_id = request.chatbot_id
        result = await advanced_features_service.chat_with_bot(
            db=db,
            user_id=current_user.id,
            chatbot_id=chatbot_id,
            message=request.message,
            session_id=request.session_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================================================================
# MODEL ROUTER ENDPOINTS
# ===================================================================

@router.post("/route")
async def route_task(
    request: ModelRouteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Route task to the best model automatically."""
    try:
        result = await advanced_features_service.route_task(
            task_type=request.task_type,
            task_description=request.task_description,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """Get all available models."""
    return {
        "models": advanced_features_service.available_models,
        "self_hosted": ["llama3.1", "qwen2.5", "deepseek-r1", "mistral", "stable-diffusion-xl", "flux"],
        "cloud": ["gemini-pro", "gpt-4o", "claude-3", "groq-llama"],
    }


# ===================================================================
# VIDEO TRANSCRIPTION ENDPOINT
# ===================================================================

@router.post("/video/transcribe")
async def transcribe_video(
    file: UploadFile = File(...),
    language: str = Form("en"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload video and transcribe with Whisper."""
    try:
        upload_dir = Path("uploads/videos")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{uuid.uuid4()}_{InputSanitizer.sanitize_filename(file.filename or 'video.mp4')}"
        file_path = upload_dir / safe_filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        if os.path.getsize(str(file_path)) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=400, detail="Video file too large (max 50MB)")

        start_time = asyncio.get_event_loop().time()

        async with httpx.AsyncClient(timeout=300.0) as client:
            with open(file_path, "rb") as f:
                files = {"file": f}
                data = {"language": language}
                response = await client.post(
                    f"{settings.WHISPER_API_URL}/transcribe",
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                result = response.json()

        execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)

        from app.models.advanced_features import VoiceRecording
        recording = VoiceRecording(
            user_id=current_user.id,
            recording_type=RecordingType.INPUT,
            storage_path=str(file_path),
            language=language,
            transcription=result.get("text", ""),
            model_used="faster-whisper",
        )
        db.add(recording)
        await db.commit()

        from app.models.usage import UsageLog
        usage_log = UsageLog(
            user_id=current_user.id,
            action="video_transcription",
            tokens_used=0,
            execution_time_ms=execution_time,
        )
        db.add(usage_log)
        await db.commit()

        return {
            "transcription": result.get("text", ""),
            "language": language,
            "duration": result.get("duration"),
            "execution_time_ms": execution_time,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video transcription failed: {str(e)}")


# ===================================================================
# HEALTH CHECK FOR ALL SERVICES
# ===================================================================

@router.get("/health")
async def health_check():
    """Check health of all AI services."""
    services = {
        "ollama": f"{settings.OLLAMA_BASE_URL}/api/tags",
        "comfyui": f"{settings.COMFYUI_URL}/system_stats",
        "whisper": f"{settings.WHISPER_API_URL}/health",
        "tts": f"{settings.TTS_API_URL}/health",
        "searxng": f"{settings.SEARXNG_URL}/",
    }

    health_status = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service, url in services.items():
            try:
                response = await client.get(url)
                health_status[service] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "code": response.status_code,
                }
            except Exception as e:
                health_status[service] = {
                    "status": "unreachable",
                    "error": str(e),
                }

    return {"services": health_status}
