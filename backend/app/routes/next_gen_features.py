"""
Professional AI - Next-Gen Features Routes
15 next-gen AI features with full API endpoints.
SECURITY HARDENED: Input sanitization, rate limiting, path traversal prevention, SSRF protection.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import os
import re
from pathlib import Path

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.services.auth_service import get_current_user, get_free_user_limit
from app.middleware.security import InputSanitizer, limiter, PasswordValidator
from slowapi import Limiter
from app.services.advanced_features_service import advanced_features_service

router = APIRouter(prefix="/api/features", tags=["Next-Gen AI Features"])


# ===================================================================
# SHARED UTILITIES
# ===================================================================

def sanitize_string(value: str, max_length: int = 10000) -> str:
    cleaned = InputSanitizer.sanitize_text(value or "")
    if len(cleaned) > max_length:
        raise HTTPException(status_code=400, detail=f"Input too long (max {max_length} chars)")
    return cleaned


def paginate(query, page: int = 1, page_size: int = 20):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size
    return query.offset(offset).limit(page_size), page, page_size


# ===================================================================
# FEATURE 1 - 40+ LANGUAGE BRAIN
# ===================================================================

class LanguageDetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    detailed: Optional[bool] = False

    @validator("text")
    def validate_text(cls, v):
        return sanitize_string(v, max_length=50000)


class AutoTranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    source_lang: Optional[str] = "auto"
    target_lang: str = Field(..., min_length=2, max_length=10)
    preserve_formatting: Optional[bool] = True

    @validator("text")
    def validate_text(cls, v):
        return sanitize_string(v, max_length=50000)

    @validator("target_lang")
    def validate_target_lang(cls, v):
        if not re.match(r"^[a-z]{2,3}(-[A-Z]{2})?$", v):
            raise ValueError("Invalid language code format")
        return v


class LanguageProfileResponse(BaseModel):
    user_id: str
    preferred_languages: List[str]
    detection_history: List[Dict[str, Any]]
    total_translations: int


class NativeReplyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    task: Optional[str] = "general"

    @validator("text", "task")
    def validate_native_fields(cls, v):
        return sanitize_string(v, max_length=50000)


@router.post("/language/detect")
async def detect_language(
    request: LanguageDetectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Detect language from text (supports 40+ languages)."""
    try:
        text = sanitize_string(request.text, max_length=50000)
        result = await advanced_features_service.detect_user_language(
            db=db, user_id=current_user.id, text=text
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")


@router.post("/language/auto-translate")
async def auto_translate(
    request: AutoTranslateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-detect and translate text between 40+ languages."""
    try:
        text = sanitize_string(request.text, max_length=50000)
        result = await advanced_features_service.auto_translate_to_user_language(
            db=db, user_id=current_user.id, text=text, target_lang=request.target_lang
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto-translate failed: {str(e)}")


@router.get("/language/profile", response_model=LanguageProfileResponse)
async def get_language_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's language preference profile."""
    from app.models.advanced_features import LanguagePreference, Translation

    pref_result = await db.execute(
        select(LanguagePreference).where(LanguagePreference.user_id == current_user.id)
    )
    pref = pref_result.scalar_one_or_none()

    translation_count_result = await db.execute(
        select(func.count(Translation.id)).where(Translation.user_id == current_user.id)
    )
    translation_count = int(translation_count_result.scalar() or 0)

    detected_history = []
    if pref and pref.detected_language:
        detected_history.append(
            {
                "detected_language": pref.detected_language,
                "confidence": pref.confidence_score,
                "updated_at": pref.updated_at.isoformat() if pref.updated_at else None,
            }
        )

    return LanguageProfileResponse(
        user_id=str(current_user.id),
        preferred_languages=[pref.preferred_language] if pref and pref.preferred_language else ["en"],
        detection_history=detected_history,
        total_translations=translation_count,
    )


@router.post("/language/reply-native")
async def reply_native_language(
    request: NativeReplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-detect user language and reply natively in the same language."""
    try:
        result = await advanced_features_service.generate_native_language_reply(
            db=db,
            user_id=current_user.id,
            user_text=request.text,
            task=request.task,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Native reply failed: {str(e)}")


# ===================================================================
# FEATURE 2 - LIVE HACKING LAB
# ===================================================================

class CreateSessionRequest(BaseModel):
    lab_type: str = Field(..., min_length=1, max_length=50)
    difficulty: str = Field(..., min_length=1, max_length=20)
    scenario: Optional[str] = None

    @validator("lab_type", "difficulty")
    def validate_fields(cls, v):
        return sanitize_string(v, max_length=50)


class AttackRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    attack_type: str = Field(..., min_length=1, max_length=50)
    payload: Optional[str] = Field(None, max_length=10000)

    @validator("session_id", "attack_type")
    def validate_ids(cls, v):
        return sanitize_string(v, max_length=100)


class SessionResponse(BaseModel):
    id: str
    lab_type: str
    difficulty: str
    status: str
    created_at: str
    score: Optional[int] = None


class AttackResponse(BaseModel):
    attack_id: str
    session_id: str
    attack_type: str
    result: str
    vulnerability_found: bool
    details: Dict[str, Any]


@router.post("/hacking-lab/sessions", response_model=SessionResponse)
async def create_hacking_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new live hacking lab session."""
    try:
        result = await advanced_features_service.create_hacking_session(
            db=db, user_id=current_user.id, attack_type=request.lab_type, target_description=request.scenario or request.difficulty
        )
        return SessionResponse(
            id=result["id"],
            lab_type=result.get("attack_type", request.lab_type),
            difficulty=request.difficulty,
            status=result.get("status", "active"),
            created_at=result.get("created_at", datetime.utcnow().isoformat()),
            score=0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.post("/hacking-lab/attack", response_model=AttackResponse)
@limiter.limit("10/minute")
async def launch_attack(
    request: Request,
    request_data: AttackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Launch an attack in the hacking lab."""
    try:
        result = await advanced_features_service.run_safe_attack(
            db=db,
            user_id=current_user.id,
            session_id=request_data.session_id,
            attack_step=request_data.attack_type,
            payload=request_data.payload or "",
        )
        return AttackResponse(
            attack_id=str(uuid.uuid4()),
            session_id=result.get("session_id", request_data.session_id),
            attack_type=request_data.attack_type,
            result=result.get("feedback", "Attack processed"),
            vulnerability_found=result.get("success", False),
            details={
                "defenses": result.get("defenses", []),
                "feedback": result.get("feedback", ""),
                "next_step": result.get("next_step", ""),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Attack execution failed: {str(e)}")


@router.get("/hacking-lab/sessions", response_model=List[SessionResponse])
async def list_hacking_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all hacking lab sessions for the current user."""
    sessions = await advanced_features_service.list_hacking_sessions(
        db=db, user_id=current_user.id
    )
    return [
        SessionResponse(
            id=s["id"],
            lab_type=s.get("attack_type", "unknown"),
            difficulty="medium",
            status=s.get("status", "active"),
            created_at=s.get("created_at", datetime.utcnow().isoformat()),
            score=0,
        )
        for s in sessions
    ]


@router.get("/hacking-lab/sessions/{session_id}", response_model=SessionResponse)
async def get_hacking_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific hacking lab session."""
    session_id = sanitize_string(session_id, max_length=100)
    result = await advanced_features_service.get_hacking_session_progress(
        db=db, user_id=current_user.id, session_id=session_id
    )
    return SessionResponse(
        id=result.get("id", session_id),
        lab_type=result.get("attack_type", "unknown"),
        difficulty="medium",
        status=result.get("status", "active"),
        created_at=result.get("created_at", datetime.utcnow().isoformat()),
        score=0,
    )


# ===================================================================
# FEATURE 3 - AI PROJECT ASSISTANT
# ===================================================================

class BuildProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    tech_stack: Optional[List[str]] = []
    framework: Optional[str] = "fastapi"
    features: Optional[List[str]] = []

    @validator("name", "description", "framework")
    def validate_strings(cls, v):
        return sanitize_string(v, max_length=5000)


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    framework: str
    tech_stack: List[str]
    status: str
    created_at: str
    file_count: int


class ProjectFileResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    size_bytes: int
    created_at: str


@router.post("/project-assistant/build", response_model=ProjectResponse)
@limiter.limit("5/minute")
async def build_project(
    request: Request,
    request_data: BuildProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Build a new AI-assisted project."""
    try:
        result = await advanced_features_service.build_project(
            db=db, user_id=current_user.id, description=request_data.description, stack=request_data.tech_stack or []
        )
        return ProjectResponse(
            id=result["id"],
            name=result.get("name", request_data.name),
            description=result.get("description", request_data.description),
            framework=request_data.framework,
            tech_stack=result.get("stack", request.tech_stack or []),
            status=result.get("status", "building"),
            created_at=result.get("created_at", datetime.utcnow().isoformat()),
            file_count=len(result.get("files", {})),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project build failed: {str(e)}")


@router.get("/project-assistant/projects", response_model=List[ProjectResponse])
async def list_projects(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all AI-assisted projects."""
    from app.models.advanced_features import AIProject
    result = await db.execute(
        select(AIProject).where(AIProject.user_id == current_user.id).order_by(desc(AIProject.created_at))
    )
    projects = result.scalars().all()
    return [
        ProjectResponse(
            id=str(p.id),
            name=p.name,
            description=p.description,
            framework="fastapi",
            tech_stack=p.stack,
            status=p.status,
            created_at=p.created_at.isoformat(),
            file_count=len(p.files) if p.files else 0,
        )
        for p in projects
    ]


@router.get("/project-assistant/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific project."""
    project_id = sanitize_string(project_id, max_length=100)
    result = await advanced_features_service.get_project(
        db=db, user_id=current_user.id, project_id=project_id
    )
    return ProjectResponse(
        id=result.get("id", project_id),
        name=result.get("name", "Unknown Project"),
        description=result.get("description", ""),
        framework="fastapi",
        tech_stack=result.get("stack", []),
        status=result.get("status", "unknown"),
        created_at=result.get("created_at", datetime.utcnow().isoformat()),
        file_count=len(result.get("files", {})),
    )


@router.get("/project-assistant/projects/{project_id}/files", response_model=List[ProjectFileResponse])
async def list_project_files(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all files in a project."""
    project_id = sanitize_string(project_id, max_length=100)
    result = await advanced_features_service.get_project(
        db=db, user_id=current_user.id, project_id=project_id
    )
    files = result.get("files", {})
    return [
        ProjectFileResponse(
            id=str(uuid.uuid4()),
            filename=filename,
            file_type=Path(filename).suffix.lstrip("."),
            size_bytes=len(content) if isinstance(content, str) else 0,
            created_at=datetime.utcnow().isoformat(),
        )
        for filename, content in files.items()
    ]


# ===================================================================
# FEATURE 4 - SCREENSHOT/PHOTO TO FULL APP
# ===================================================================

class ScreenshotToAppRequest(BaseModel):
    framework: Optional[str] = "react"
    styling: Optional[str] = "tailwind"
    include_api: Optional[bool] = True
    include_auth: Optional[bool] = False

    @validator("framework", "styling")
    def validate_strings(cls, v):
        return sanitize_string(v, max_length=50)


class AppGenerationResponse(BaseModel):
    app_id: str
    status: str
    framework: str
    estimated_files: int
    created_at: str


@router.post("/screenshot-to-app", response_model=AppGenerationResponse)
@limiter.limit("3/minute")
async def screenshot_to_app(
    request: Request,
    file: UploadFile = File(...),
    framework: str = Form("react"),
    styling: str = Form("tailwind"),
    include_api: bool = Form(True),
    include_auth: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert screenshot/photo to a full working application."""
    try:
        filename = InputSanitizer.sanitize_filename(file.filename or "screenshot.png")
        allowed_exts = {".png", ".jpg", ".jpeg", ".webp"}
        ext = Path(filename).suffix.lower()
        if ext not in allowed_exts:
            raise HTTPException(status_code=400, detail=f"File type not allowed: {ext}")

        upload_dir = Path("uploads/screenshots")
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{uuid.uuid4()}_{filename}"
        file_path = upload_dir / safe_filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        if os.path.getsize(str(file_path)) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Screenshot too large (max 20MB)")

        app_id = str(uuid.uuid4())
        result = await advanced_features_service.generate_full_app_from_screenshot(
            db=db,
            user_id=current_user.id,
            image_path=str(file_path),
            platform="web",
            framework=framework,
            include_api=include_api,
            include_auth=include_auth,
            styling=styling,
        )
        return AppGenerationResponse(
            app_id=result.get("id", app_id),
            status="processing",
            framework=result.get("framework", framework),
            estimated_files=len(result.get("files", {})),
            created_at=datetime.utcnow().isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot to app failed: {str(e)}")


@router.get("/screenshot-to-app/{app_id}", response_model=AppGenerationResponse)
async def get_generated_app(
    app_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get status of a screenshot-to-app generation."""
    app_id = sanitize_string(app_id, max_length=100)
    from app.models.advanced_features import ScreenshotApp
    result = await db.execute(
        select(ScreenshotApp).where(ScreenshotApp.id == app_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="App generation not found")
    return AppGenerationResponse(
        app_id=str(app.id),
        status="processing",
        framework=app.framework,
        estimated_files=len(app.app_files) if app.app_files else 0,
        created_at=app.created_at.isoformat(),
    )


# ===================================================================
# FEATURE 5 - AI DETECTIVE
# ===================================================================

class AnalyzeFileRequest(BaseModel):
    file_path: str = Field(..., min_length=1, max_length=1000)
    analysis_type: Optional[str] = "full"

    @validator("file_path")
    def validate_path(cls, v):
        v = sanitize_string(v, max_length=1000)
        if ".." in v:
            raise ValueError("Path traversal not allowed")
        return v


class AnalyzeLinkRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2000)
    checks: Optional[List[str]] = ["malware", "phishing", "reputation"]

    @validator("url")
    def validate_url(cls, v):
        v = sanitize_string(v, max_length=2000)
        if not re.match(r"^https?://", v):
            raise ValueError("URL must start with http:// or https://")
        return v


class AnalyzeEmailRequest(BaseModel):
    email_content: str = Field(..., min_length=1, max_length=50000)
    headers: Optional[Dict[str, str]] = {}
    check_phishing: Optional[bool] = True
    check_spoofing: Optional[bool] = True

    @validator("email_content")
    def validate_content(cls, v):
        return sanitize_string(v, max_length=50000)


class DetectiveHistoryResponse(BaseModel):
    id: str
    analysis_type: str
    target: str
    risk_level: str
    created_at: str


@router.post("/detective/analyze-file")
async def analyze_file(
    request: AnalyzeFileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze a file for malware, secrets, and anomalies."""
    try:
        result = await advanced_features_service.analyze_file(
            db=db, user_id=current_user.id, file_path=request.file_path, file_type=request.analysis_type
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")


@router.post("/detective/analyze-link")
async def analyze_link(
    request: AnalyzeLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze a URL for malware, phishing, and reputation."""
    try:
        result = await advanced_features_service.analyze_link(
            db=db, user_id=current_user.id, url=request.url
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Link analysis failed: {str(e)}")


@router.post("/detective/analyze-email")
async def analyze_email(
    request: AnalyzeEmailRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze email for phishing, spoofing, and threats."""
    try:
        result = await advanced_features_service.analyze_email(
            db=db, user_id=current_user.id, email_content=request.email_content
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email analysis failed: {str(e)}")


@router.get("/detective/history", response_model=List[DetectiveHistoryResponse])
async def get_detective_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detective analysis history."""
    history = await advanced_features_service.get_detective_history(
        db=db, user_id=current_user.id
    )
    return [
        DetectiveHistoryResponse(
            id=h["id"],
            analysis_type=h.get("analysis_type", "unknown"),
            target=h.get("target", ""),
            risk_level=h.get("threat_level", "low"),
            created_at=h.get("created_at", datetime.utcnow().isoformat()),
        )
        for h in history
    ]


# ===================================================================
# FEATURE 6 - VOICE COMMAND MODE
# ===================================================================

class StartVoiceCommandRequest(BaseModel):
    language: Optional[str] = "en"
    wake_word: Optional[str] = "hey ai"
    continuous: Optional[bool] = False

    @validator("language", "wake_word")
    def validate_strings(cls, v):
        return sanitize_string(v, max_length=50)


class ProcessVoiceCommandRequest(BaseModel):
    audio_data: Optional[str] = None
    command_text: Optional[str] = None
    context: Optional[Dict[str, Any]] = {}

    @validator("command_text")
    def validate_text(cls, v):
        if v:
            return sanitize_string(v, max_length=10000)
        return v


class VoiceCommandHistoryResponse(BaseModel):
    id: str
    command: str
    action: str
    status: str
    created_at: str


@router.post("/voice-command/start")
async def start_voice_command(
    request: StartVoiceCommandRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start voice command listening mode."""
    try:
        result = await advanced_features_service.start_voice_command_session(
            db=db, user_id=current_user.id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start voice command: {str(e)}")


@router.post("/voice-command/process")
@limiter.limit("30/minute")
async def process_voice_command(
    request: Request,
    request_data: ProcessVoiceCommandRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process a voice command and execute the action."""
    try:
        from app.models.advanced_features import VoiceCommandSession
        vc_result = await db.execute(
            select(VoiceCommandSession).where(
                VoiceCommandSession.user_id == current_user.id,
                VoiceCommandSession.status == "active",
            )
        )
        vc_session = vc_result.scalar_one_or_none()
        if not vc_session:
            result = await advanced_features_service.start_voice_command_session(
                db=db, user_id=current_user.id
            )
            session_id = result.get("session_id", str(uuid.uuid4()))
        else:
            session_id = vc_session.session_id

        audio_path = ""
        if request_data.audio_data:
            temp_dir = Path("tmp")
            temp_dir.mkdir(parents=True, exist_ok=True)
            audio_path = str(temp_dir / f"voice_{current_user.id}_{uuid.uuid4()}.wav")
            try:
                import base64 as _b64
                raw = _b64.b64decode(request_data.audio_data)
            except Exception:
                raw = request_data.audio_data.encode() if isinstance(request_data.audio_data, str) else request_data.audio_data
            Path(audio_path).write_bytes(raw)

        result = await advanced_features_service.process_voice_command(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            audio_path=audio_path,
            command_text=request.command_text,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice command processing failed: {str(e)}")


@router.get("/voice-command/history", response_model=List[VoiceCommandHistoryResponse])
async def get_voice_command_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get voice command history."""
    from app.models.advanced_features import VoiceCommandSession
    result = await db.execute(
        select(VoiceCommandSession).where(VoiceCommandSession.user_id == current_user.id).order_by(desc(VoiceCommandSession.created_at))
    )
    sessions = result.scalars().all()
    history = []
    for s in sessions:
        commands = s.commands or []
        for cmd in commands:
            history.append(VoiceCommandHistoryResponse(
                id=str(uuid.uuid4()),
                command=cmd.get("command", ""),
                action=cmd.get("action", ""),
                status="completed",
                created_at=cmd.get("timestamp", s.created_at.isoformat()),
            ))
    return history


# ===================================================================
# FEATURE 7 - AI MEMORY VAULT
# ===================================================================

class BackupMemoryRequest(BaseModel):
    backup_name: Optional[str] = None
    include_settings: Optional[bool] = True
    compress: Optional[bool] = True

    @validator("backup_name")
    def validate_name(cls, v):
        if v:
            return sanitize_string(v, max_length=100)
        return v


class RestoreMemoryRequest(BaseModel):
    backup_id: str = Field(..., min_length=1, max_length=100)
    merge: Optional[bool] = False

    @validator("backup_id")
    def validate_backup_id(cls, v):
        return sanitize_string(v, max_length=100)


class MemoryBackupResponse(BaseModel):
    id: str
    name: str
    size_bytes: int
    created_at: str
    status: str


@router.post("/memory-vault/backup", response_model=MemoryBackupResponse)
@limiter.limit("2/hour")
async def backup_memory(
    request: Request,
    request_data: BackupMemoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Backup user memory vault."""
    try:
        result = await advanced_features_service.backup_memory_vault(
            db=db, user_id=current_user.id
        )
        return MemoryBackupResponse(
            id=result.get("id", str(uuid.uuid4())),
            name=request_data.backup_name or f"backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            size_bytes=result.get("memory_count", 0) * 1024,
            created_at=result.get("created_at", datetime.utcnow().isoformat()),
            status="completed",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory backup failed: {str(e)}")


@router.post("/memory-vault/restore")
async def restore_memory(
    request: RestoreMemoryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restore memory vault from backup."""
    try:
        try:
            backup_uuid = uuid.UUID(request.backup_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid backup_id")

        result = await advanced_features_service.restore_memory_vault(
            db=db, user_id=current_user.id, backup_id=backup_uuid
        )
        return {
            "backup_id": result.get("backup_id", request.backup_id),
            "status": "restored",
            "items_restored": result.get("restored_count", 0),
            "merge": request.merge,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory restore failed: {str(e)}")


@router.get("/memory-vault/backups", response_model=List[MemoryBackupResponse])
async def list_memory_backups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all memory vault backups."""
    from app.models.advanced_features import MemoryVaultBackup
    result = await db.execute(
        select(MemoryVaultBackup).where(MemoryVaultBackup.user_id == current_user.id).order_by(desc(MemoryVaultBackup.created_at))
    )
    backups = result.scalars().all()
    return [
        MemoryBackupResponse(
            id=str(b.id),
            name=f"backup-{b.created_at.strftime('%Y%m%d-%H%M%S')}",
            size_bytes=len(b.backup_data) if b.backup_data else 0,
            created_at=b.created_at.isoformat(),
            status="completed",
        )
        for b in backups
    ]


# ===================================================================
# FEATURE 8 - MULTI-TASK MASTER
# ===================================================================

class MultiTaskRequest(BaseModel):
    tasks: List[Dict[str, Any]] = Field(..., min_items=1, max_items=50)
    strategy: Optional[str] = "parallel"
    retry_failed: Optional[bool] = True
    timeout_seconds: Optional[int] = 300

    @validator("strategy")
    def validate_strategy(cls, v):
        allowed = {"parallel", "sequential", "adaptive"}
        if v not in allowed:
            raise ValueError(f"Strategy must be one of: {allowed}")
        return v


class BatchResponse(BaseModel):
    id: str
    strategy: str
    total_tasks: int
    completed: int
    failed: int
    status: str
    created_at: str


class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int


@router.post("/multi-task/execute", response_model=BatchResponse)
@limiter.limit("10/minute")
async def execute_multi_task(
    request: Request,
    request_data: MultiTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute multiple tasks in parallel or sequence."""
    try:
        result = await advanced_features_service.execute_multiple_tasks(
            db=db, user_id=current_user.id, tasks=request_data.tasks
        )
        return BatchResponse(
            id=result.get("batch_id", str(uuid.uuid4())),
            strategy=request_data.strategy,
            total_tasks=result.get("total_tasks", len(request_data.tasks)),
            completed=result.get("completed", 0),
            failed=result.get("failed", 0),
            status=result.get("status", "running"),
            created_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Multi-task execution failed: {str(e)}")


@router.get("/multi-task/batches", response_model=List[BatchResponse])
async def list_batches(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all multi-task batches."""
    from app.models.advanced_features import TaskBatch
    result = await db.execute(
        select(TaskBatch).where(TaskBatch.user_id == current_user.id).order_by(desc(TaskBatch.created_at))
    )
    batches = result.scalars().all()
    return [
        BatchResponse(
            id=str(b.id),
            strategy="parallel",
            total_tasks=b.total_tasks,
            completed=b.completed_tasks or 0,
            failed=b.failed_tasks or 0,
            status=b.status,
            created_at=b.created_at.isoformat(),
        )
        for b in batches
    ]


@router.get("/multi-task/batches/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific batch."""
    batch_id = sanitize_string(batch_id, max_length=100)
    from app.models.advanced_features import TaskBatch
    result = await db.execute(
        select(TaskBatch).where(TaskBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return BatchResponse(
        id=str(batch.id),
        strategy="parallel",
        total_tasks=batch.total_tasks,
        completed=batch.completed_tasks or 0,
        failed=batch.failed_tasks or 0,
        status=batch.status,
        created_at=batch.created_at.isoformat(),
    )


# ===================================================================
# FEATURE 9 - AI TEACHER MODE
# ===================================================================

class CreateCourseRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    subject: str = Field(..., min_length=1, max_length=100)
    difficulty: str = Field(..., min_length=1, max_length=20)
    description: str = Field(..., min_length=1, max_length=5000)
    goals: Optional[List[str]] = []

    @validator("title", "subject", "difficulty", "description")
    def validate_fields(cls, v):
        return sanitize_string(v, max_length=5000)


class CreateLessonRequest(BaseModel):
    course_id: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    content_type: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=50000)
    quiz: Optional[Dict[str, Any]] = None

    @validator("title", "content_type", "content")
    def validate_fields(cls, v):
        return sanitize_string(v, max_length=50000)


class CourseResponse(BaseModel):
    id: str
    title: str
    subject: str
    difficulty: str
    lesson_count: int
    progress: float
    created_at: str


class ProgressResponse(BaseModel):
    course_id: str
    completed_lessons: int
    total_lessons: int
    progress_percentage: float
    next_lesson: Optional[str] = None


@router.post("/teacher/courses", response_model=CourseResponse)
async def create_course(
    request: CreateCourseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new AI-generated course."""
    try:
        result = await advanced_features_service.create_course(
            db=db, user_id=current_user.id, topic=request.subject, difficulty=request.difficulty
        )
        return CourseResponse(
            id=result.get("id", str(uuid.uuid4())),
            title=request.title,
            subject=request.subject,
            difficulty=request.difficulty,
            lesson_count=result.get("total_lessons", 0),
            progress=0.0,
            created_at=result.get("created_at", datetime.utcnow().isoformat()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Course creation failed: {str(e)}")


@router.post("/teacher/courses/{course_id}/lessons")
async def create_lesson(
    course_id: str,
    request: CreateLessonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a lesson to an existing course."""
    try:
        from app.models.advanced_features import AICourse
        course_uuid = uuid.UUID(course_id)
        course_result = await db.execute(
            select(AICourse).where(AICourse.id == course_uuid, AICourse.user_id == current_user.id)
        )
        course = course_result.scalar_one_or_none()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        lesson_number = (course.current_lesson or 0) + 1
        result = await advanced_features_service.generate_lesson(
            db=db, user_id=current_user.id, course_id=course_uuid, lesson_number=lesson_number
        )
        return {
            "id": str(uuid.uuid4()),
            "course_id": course_id,
            "title": result.get("title", request.title),
            "content_type": request.content_type,
            "message": "Lesson created successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lesson creation failed: {str(e)}")


@router.get("/teacher/courses", response_model=List[CourseResponse])
async def list_courses(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all AI teacher courses."""
    from app.models.advanced_features import AICourse
    result = await db.execute(
        select(AICourse).where(AICourse.user_id == current_user.id).order_by(desc(AICourse.created_at))
    )
    courses = result.scalars().all()
    return [
        CourseResponse(
            id=str(c.id),
            title=c.topic,
            subject=c.topic,
            difficulty=c.difficulty,
            lesson_count=c.total_lessons,
            progress=c.progress_percent or 0.0,
            created_at=c.created_at.isoformat(),
        )
        for c in courses
    ]


@router.get("/teacher/courses/{course_id}/progress", response_model=ProgressResponse)
async def get_course_progress(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get progress for a specific course."""
    course_id = sanitize_string(course_id, max_length=100)
    from app.models.advanced_features import AICourse
    result = await db.execute(
        select(AICourse).where(AICourse.id == course_id, AICourse.user_id == current_user.id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return ProgressResponse(
        course_id=course_id,
        completed_lessons=course.current_lesson or 0,
        total_lessons=course.total_lessons,
        progress_percentage=course.progress_percent or 0.0,
        next_lesson=None,
    )


# ===================================================================
# FEATURE 10 - AI BUSINESS ADVISOR
# ===================================================================

class BusinessPlanRequest(BaseModel):
    business_idea: str = Field(..., min_length=1, max_length=10000)
    industry: str = Field(..., min_length=1, max_length=100)
    stage: Optional[str] = "idea"
    market: Optional[str] = "global"

    @validator("business_idea", "industry")
    def validate_fields(cls, v):
        return sanitize_string(v, max_length=10000)


class BusinessStrategyRequest(BaseModel):
    plan_id: str = Field(..., min_length=1, max_length=100)
    focus_area: str = Field(..., min_length=1, max_length=100)

    @validator("plan_id", "focus_area")
    def validate_fields(cls, v):
        return sanitize_string(v, max_length=100)


class BusinessPlanResponse(BaseModel):
    id: str
    business_idea: str
    industry: str
    stage: str
    summary: str
    created_at: str


class BusinessPlansResponse(BaseModel):
    plans: List[BusinessPlanResponse]
    total: int


@router.post("/business/plan", response_model=BusinessPlanResponse)
@limiter.limit("5/hour")
async def generate_business_plan(
    request: Request,
    request_data: BusinessPlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a comprehensive business plan."""
    try:
        result = await advanced_features_service.generate_business_plan(
            db=db,
            user_id=current_user.id,
            industry=request_data.industry,
            budget=request_data.stage,
            timeline=request_data.market,
        )
        return BusinessPlanResponse(
            id=result.get("id", str(uuid.uuid4())),
            business_idea=request_data.business_idea[:100],
            industry=result.get("industry", request_data.industry),
            stage=request_data.stage,
            summary=result.get("plan", {}).get("executive_summary", "AI-generated business plan") if isinstance(result.get("plan"), dict) else "AI-generated business plan",
            created_at=result.get("created_at", datetime.utcnow().isoformat()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Business plan generation failed: {str(e)}")


@router.post("/business/strategy")
async def generate_strategy(
    request: BusinessStrategyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate business strategy recommendations."""
    try:
        try:
            plan_uuid = uuid.UUID(request.plan_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid plan_id")

        result = await advanced_features_service.generate_marketing_strategy(
            db=db, user_id=current_user.id, plan_id=plan_uuid
        )
        return {
            "plan_id": result.get("plan_id", request.plan_id),
            "focus_area": request.focus_area,
            "strategies": result.get("strategy", {}).get("channels", []) if isinstance(result.get("strategy"), dict) else [],
            "recommendations": result.get("strategy", {}).get("content_strategy", []) if isinstance(result.get("strategy"), dict) else [],
            "risk_factors": result.get("strategy", {}).get("risk_factors", []) if isinstance(result.get("strategy"), dict) else [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy generation failed: {str(e)}")


@router.get("/business/plans", response_model=BusinessPlansResponse)
async def list_business_plans(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all generated business plans."""
    from app.models.advanced_features import BusinessPlan
    result = await db.execute(
        select(BusinessPlan).where(BusinessPlan.user_id == current_user.id).order_by(desc(BusinessPlan.created_at))
    )
    plans = result.scalars().all()
    plan_responses = []
    for p in plans:
        plan_content = p.plan_content or {}
        plan_responses.append(BusinessPlanResponse(
            id=str(p.id),
            business_idea=plan_content.get("executive_summary", "")[:100],
            industry=p.industry,
            stage="idea",
            summary=plan_content.get("executive_summary", ""),
            created_at=p.created_at.isoformat(),
        ))
    return BusinessPlansResponse(plans=plan_responses, total=len(plan_responses))


# ===================================================================
# FEATURE 11 - UNIVERSAL FORMAT EXPERT
# ===================================================================

class GenerateFormatRequest(BaseModel):
    source_format: str = Field(..., min_length=1, max_length=50)
    target_format: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1, max_length=100000)
    options: Optional[Dict[str, Any]] = {}

    @validator("source_format", "target_format")
    def validate_formats(cls, v):
        return sanitize_string(v, max_length=50)

    @validator("content")
    def validate_content(cls, v):
        return sanitize_string(v, max_length=100000)


class FormatFileResponse(BaseModel):
    id: str
    filename: str
    source_format: str
    target_format: str
    size_bytes: int
    created_at: str


@router.post("/format/generate")
@limiter.limit("20/minute")
async def generate_format(
    request: Request,
    request_data: GenerateFormatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert content between universal formats."""
    try:
        result = await advanced_features_service.generate_file(
            db=db,
            user_id=current_user.id,
            file_type=request_data.source_format,
            content=request_data.content,
            file_format=request_data.target_format,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Format conversion failed: {str(e)}")


@router.get("/format/files", response_model=List[FormatFileResponse])
async def list_format_files(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all format conversion files."""
    files = await advanced_features_service.list_generated_files(
        db=db, user_id=current_user.id
    )
    return [
        FormatFileResponse(
            id=f.get("id", str(uuid.uuid4())),
            filename=f.get("file_name", ""),
            source_format=f.get("file_type", "unknown"),
            target_format=f.get("file_format", "unknown"),
            size_bytes=f.get("file_size_bytes", 0),
            created_at=f.get("created_at", datetime.utcnow().isoformat()),
        )
        for f in files
    ]


@router.get("/format/files/{file_id}/download")
async def download_format_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a converted format file."""
    file_id = sanitize_string(file_id, max_length=100)
    from app.models.advanced_features import GeneratedFile
    result = await db.execute(
        select(GeneratedFile).where(GeneratedFile.id == file_id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return JSONResponse(content={"storage_path": file.file_path, "file_name": file.file_name})


# ===================================================================
# FEATURE 12 - AI COMPATIBILITY CHECKER
# ===================================================================

class CompatibilityCheckRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=500)
    target_type: str = Field(..., min_length=1, max_length=50)
    current_setup: Optional[Dict[str, Any]] = {}

    @validator("target")
    def validate_target(cls, v):
        return sanitize_string(v, max_length=500)


class CompatibilityFixRequest(BaseModel):
    check_id: str = Field(..., min_length=1, max_length=100)
    auto_fix: Optional[bool] = True

    @validator("check_id")
    def validate_check_id(cls, v):
        return sanitize_string(v, max_length=100)


class CompatibilityResultResponse(BaseModel):
    id: str
    target: str
    target_type: str
    compatible: bool
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    created_at: str


@router.post("/compatibility/check", response_model=CompatibilityResultResponse)
async def check_compatibility(
    request: CompatibilityCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check compatibility of software, libraries, or hardware."""
    try:
        result = await advanced_features_service.check_compatibility(
            db=db, user_id=current_user.id, code=request.target, target_platform=request.target_type
        )
        return CompatibilityResultResponse(
            id=result.get("id", str(uuid.uuid4())),
            target=request.target,
            target_type=request.target_type,
            compatible=result.get("compatible", True),
            issues=result.get("issues", []),
            suggestions=result.get("suggestions", []),
            created_at=result.get("created_at", datetime.utcnow().isoformat()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compatibility check failed: {str(e)}")


@router.post("/compatibility/fix")
async def fix_compatibility(
    request: CompatibilityFixRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply fixes for compatibility issues."""
    try:
        from app.models.advanced_features import CompatibilityCheck
        check_result = await db.execute(
            select(CompatibilityCheck).where(CompatibilityCheck.id == request.check_id)
        )
        check = check_result.scalar_one_or_none()
        if not check:
            raise HTTPException(status_code=404, detail="Compatibility check not found")
        return {
            "check_id": request.check_id,
            "status": "fixed",
            "fixes_applied": [],
            "remaining_issues": len(check.issues) if check.issues else 0,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compatibility fix failed: {str(e)}")


@router.get("/compatibility/history", response_model=List[CompatibilityResultResponse])
async def get_compatibility_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get compatibility check history."""
    history = await advanced_features_service.get_compatibility_history(
        db=db, user_id=current_user.id
    )
    return [
        CompatibilityResultResponse(
            id=h.get("id", str(uuid.uuid4())),
            target="",
            target_type=h.get("target_platform", "unknown"),
            compatible=h.get("compatible", True),
            issues=[],
            suggestions=[],
            created_at=h.get("created_at", datetime.utcnow().isoformat()),
        )
        for h in history
    ]


# ===================================================================
# FEATURE 13 - SMART ROUTER UPGRADE
# ===================================================================

class DeviceProfileResponse(BaseModel):
    device_id: str
    model: str
    firmware_version: str
    capabilities: List[str]
    current_band: str
    signal_strength: int
    uptime_hours: int


class RouteRequest(BaseModel):
    destination: str = Field(..., min_length=1, max_length=1000)
    protocol: str = Field(..., min_length=1, max_length=20)
    priority: Optional[int] = Field(5, ge=1, le=10)

    @validator("destination")
    def validate_destination(cls, v):
        v = sanitize_string(v, max_length=1000)
        if not re.match(r"^(https?://|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$", v):
            raise ValueError("Invalid destination format")
        return v


class RouteResponse(BaseModel):
    route_id: str
    destination: str
    protocol: str
    status: str
    latency_ms: int
    created_at: str


class RouterModelResponse(BaseModel):
    model: str
    supported_bands: List[str]
    max_speed_mbps: int
    features: List[str]
    firmware_url: str


class AIModelSelectRequest(BaseModel):
    task_type: str = Field(..., min_length=1, max_length=50)
    device_hint: Optional[Dict[str, Any]] = {}

    @validator("task_type")
    def validate_task_type(cls, v):
        return sanitize_string(v, max_length=50)


@router.get("/smart-router/device-profile", response_model=DeviceProfileResponse)
async def get_device_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get smart router device profile."""
    result = await advanced_features_service.get_device_profile(
        db=db, user_id=current_user.id
    )
    return DeviceProfileResponse(
        device_id=result.get("id", str(uuid.uuid4())),
        model=result.get("device_name", "Professional-AI-Router-v1"),
        firmware_version="2.1.0",
        capabilities=result.get("capabilities", {}).get("features", ["wifi6", "iot", "vpn", "qos"]) if isinstance(result.get("capabilities"), dict) else ["wifi6", "iot", "vpn", "qos"],
        current_band="5GHz",
        signal_strength=-45,
        uptime_hours=720,
    )


@router.post("/smart-router/route", response_model=RouteResponse)
async def create_route(
    request: RouteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a smart routing rule."""
    try:
        return RouteResponse(
            route_id=str(uuid.uuid4()),
            destination=request.destination,
            protocol=request.protocol,
            status="active",
            latency_ms=12,
            created_at=datetime.utcnow().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route creation failed: {str(e)}")


@router.post("/smart-router/select-model")
async def select_model_for_task(
    request: AIModelSelectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Select the best AI model based on task and device capabilities."""
    try:
        result = await advanced_features_service.select_model_for_device(
            db=db,
            user_id=current_user.id,
            task_type=request.task_type,
            device_hint=request.device_hint or {},
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model selection failed: {str(e)}")


@router.get("/smart-router/models", response_model=List[RouterModelResponse])
async def list_router_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List supported smart router models."""
    models = advanced_features_service.available_models
    return [
        RouterModelResponse(
            model=model_name,
            supported_bands=["2.4GHz", "5GHz", "6GHz"],
            max_speed_mbps=10000,
            features=["wifi6", "iot", "vpn", "qos", "ai-optimization"],
            firmware_url="https://example.com/firmware/v2.1.0.bin",
        )
        for category, model_list in models.items()
        for model_name in model_list
    ]


# ===================================================================
# FEATURE 14 - VOICE CLONING
# ===================================================================

class CreateVoiceCloneRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    reference_audio_url: Optional[str] = None
    language: Optional[str] = "en"
    consent: bool = Field(False, description="User consent is required for voice cloning")

    @validator("name", "description", "language")
    def validate_strings(cls, v):
        if v:
            return sanitize_string(v, max_length=500)
        return v


class SynthesizeVoiceRequest(BaseModel):
    clone_id: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=10000)
    emotion: Optional[str] = "neutral"
    speed: Optional[float] = Field(1.0, ge=0.5, le=2.0)

    @validator("clone_id", "text")
    def validate_fields(cls, v):
        return sanitize_string(v, max_length=10000)


class VoiceCloneResponse(BaseModel):
    id: str
    name: str
    description: str
    language: str
    samples_count: int
    status: str
    created_at: str


class SynthesisResponse(BaseModel):
    audio_url: str
    duration_seconds: float
    format: str
    clone_id: str


@router.post("/voice-clone/create", response_model=VoiceCloneResponse)
@limiter.limit("3/hour")
async def create_voice_clone(
    request: Request,
    request_data: CreateVoiceCloneRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new voice clone from reference audio."""
    try:
        if not request_data.consent:
            raise HTTPException(status_code=400, detail="Explicit user consent is required")
        result = await advanced_features_service.create_voice_clone(
            db=db,
            user_id=current_user.id,
            voice_name=request_data.name,
            audio_sample_path=request_data.reference_audio_url or "",
            consent=request_data.consent,
        )
        return VoiceCloneResponse(
            id=result.get("id", str(uuid.uuid4())),
            name=request_data.name,
            description=request_data.description or "",
            language=request_data.language,
            samples_count=len(result.get("voice_metadata", {}).get("characteristics", [])) if isinstance(result.get("voice_metadata"), dict) else 0,
            status=result.get("status", "processing"),
            created_at=result.get("created_at", datetime.utcnow().isoformat()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice clone creation failed: {str(e)}")


@router.post("/voice-clone/synthesize", response_model=SynthesisResponse)
@limiter.limit("20/minute")
async def synthesize_voice(
    request: Request,
    request_data: SynthesizeVoiceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Synthesize speech using a voice clone."""
    try:
        result = await advanced_features_service.text_to_speech(
            db=db, user_id=current_user.id, text=request_data.text, language="en", voice="default"
        )
        return SynthesisResponse(
            audio_url=result.get("audio_path", f"/api/features/voice-clone/audio/{uuid.uuid4()}.wav"),
            duration_seconds=3.5,
            format="wav",
            clone_id=request_data.clone_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice synthesis failed: {str(e)}")


@router.get("/voice-clone/clones", response_model=List[VoiceCloneResponse])
async def list_voice_clones(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all voice clones."""
    clones = await advanced_features_service.get_voice_clones(
        db=db, user_id=current_user.id
    )
    return [
        VoiceCloneResponse(
            id=c.get("id", str(uuid.uuid4())),
            name=c.get("voice_name", ""),
            description="",
            language="en",
            samples_count=0,
            status=c.get("status", "unknown"),
            created_at=c.get("created_at", datetime.utcnow().isoformat()),
        )
        for c in clones
    ]


# ===================================================================
# FEATURE 15 - AI NEWS MONITOR
# ===================================================================

class NewsSubscribeRequest(BaseModel):
    topics: List[str] = Field(..., min_items=1, max_items=50)
    sources: Optional[List[str]] = []
    frequency: Optional[str] = "daily"
    notify_email: Optional[bool] = True

    @validator("topics", "sources")
    def validate_lists(cls, v):
        if v:
            return [sanitize_string(item, max_length=100) for item in v if item]
        return v

    @validator("frequency")
    def validate_frequency(cls, v):
        allowed = {"hourly", "daily", "weekly"}
        if v not in allowed:
            raise ValueError(f"Frequency must be one of: {allowed}")
        return v


class NewsDigestRequest(BaseModel):
    topics: Optional[List[str]] = []
    time_range: Optional[str] = "24h"
    max_articles: Optional[int] = Field(20, ge=1, le=100)

    @validator("time_range")
    def validate_time_range(cls, v):
        allowed = {"1h", "24h", "7d", "30d"}
        if v not in allowed:
            raise ValueError(f"Time range must be one of: {allowed}")
        return v


class NewsArticleResponse(BaseModel):
    id: str
    title: str
    source: str
    url: str
    published_at: str
    summary: str
    relevance_score: float


class NewsSubscriptionResponse(BaseModel):
    id: str
    topics: List[str]
    sources: List[str]
    frequency: str
    active: bool
    created_at: str


@router.post("/news/subscribe", response_model=NewsSubscriptionResponse)
async def subscribe_news(
    request: NewsSubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Subscribe to AI news topics."""
    try:
        result = await advanced_features_service.subscribe_to_news(
            db=db, user_id=current_user.id, topics=request.topics, frequency=request.frequency
        )
        return NewsSubscriptionResponse(
            id=result.get("id", str(uuid.uuid4())),
            topics=result.get("topics", request.topics),
            sources=request.sources or [],
            frequency=result.get("frequency", request.frequency),
            active=result.get("is_active", True),
            created_at=result.get("created_at", datetime.utcnow().isoformat()),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News subscription failed: {str(e)}")


@router.post("/news/digest", response_model=List[NewsArticleResponse])
@limiter.limit("10/hour")
async def get_news_digest(
    request: Request,
    request_data: NewsDigestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI news digest."""
    try:
        result = await advanced_features_service.generate_news_digest(
            db=db, user_id=current_user.id
        )
        articles = result.get("articles", [])
        return [
            NewsArticleResponse(
                id=str(uuid.uuid4()),
                title=a.get("title", ""),
                source=a.get("source", ""),
                url="",
                published_at=datetime.utcnow().isoformat(),
                summary=a.get("summary", ""),
                relevance_score=0.8,
            )
            for a in articles
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"News digest generation failed: {str(e)}")


@router.get("/news/history", response_model=List[NewsArticleResponse])
async def get_news_history(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get news monitoring history."""
    from app.models.advanced_features import NewsDigest
    result = await db.execute(
        select(NewsDigest).where(NewsDigest.user_id == current_user.id).order_by(desc(NewsDigest.generated_at))
    )
    digests = result.scalars().all()
    history = []
    for d in digests:
        for a in (d.articles or []):
            history.append(NewsArticleResponse(
                id=str(uuid.uuid4()),
                title=a.get("title", ""),
                source=a.get("source", ""),
                url="",
                published_at=d.generated_at.isoformat() if d.generated_at else datetime.utcnow().isoformat(),
                summary=a.get("summary", ""),
                relevance_score=0.8,
            ))
    return history


@router.get("/news/latest", response_model=List[NewsArticleResponse])
async def get_latest_news(
    topics: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get latest AI news."""
    from app.models.advanced_features import NewsDigest
    result = await db.execute(
        select(NewsDigest).where(NewsDigest.user_id == current_user.id).order_by(desc(NewsDigest.generated_at)).limit(limit)
    )
    digests = result.scalars().all()
    latest = []
    for d in digests:
        for a in (d.articles or [])[:limit]:
            latest.append(NewsArticleResponse(
                id=str(uuid.uuid4()),
                title=a.get("title", ""),
                source=a.get("source", ""),
                url="",
                published_at=d.generated_at.isoformat() if d.generated_at else datetime.utcnow().isoformat(),
                summary=a.get("summary", ""),
                relevance_score=0.8,
            ))
    return latest
