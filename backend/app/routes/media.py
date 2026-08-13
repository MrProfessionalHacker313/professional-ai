"""
Professional AI - Media Engine Routes
API endpoints for videos, pictures, posters, animations, voice over,
scene control, subtitle verification, and limits enforcement.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.media_engine import (
    MediaJob, MediaType, MediaStatus, VoiceStyle,
    MediaResolution, MediaVoiceClone, MediaDownload,
)
from app.services.auth_service import get_current_user
from app.services.media.bullmq_queue import media_queue_service
from app.services.media.limits import MediaLimitsService
from app.services.media.voice_over import voice_over_service
from app.services.media.voice_catalog import get_voice_catalog, VOICE_STYLES, SUPPORTED_LANGUAGES
from app.services.media.tts_router import tts_router
from app.services.media.forced_alignment import forced_alignment_service
from app.services.media.subtitle_verify import subtitle_verification_service
from app.services.media.provider_keys import media_key_vault
from app.services.media.media_providers import media_provider_registry
from app.services.media.thumbnail_maker import thumbnail_maker_service
from app.services.media.meme_maker import meme_maker_service
from app.services.ai_service import ai_service
from app.services.ai_router import ModelType
from app.services.credit_service import CreditService
from app.services.unlimited_mode import subscription_access
import redis.asyncio as redis
from datetime import datetime, timezone

router = APIRouter(prefix="/api/media", tags=["Media Engine"])

# Internal secret for worker → backend callbacks
INTERNAL_WORKER_SECRET = os.getenv("INTERNAL_WORKER_SECRET", "change-this-internal-secret")


# ===================================================================
# Schemas
# ===================================================================

class MediaCreateRequest(BaseModel):
    media_type: str = Field(..., pattern="^(video|picture|poster|animation)$")
    topic: str = Field(..., min_length=1, max_length=5000)
    script: Optional[str] = Field(None, max_length=50000)
    scenes_text: Optional[str] = Field(None, max_length=20000)
    voice_style: str = Field(default="adult_female", pattern="^(?:young_girl|young_boy|adult_male|adult_female|news_anchor|teacher|robot|cartoon|villain|hero|whisper|angry|happy|sad|excited|robotic|custom|clone)$")
    voice_prompt: Optional[str] = Field(None, max_length=500)
    language: str = Field(default="en", max_length=10)
    duration_seconds: int = Field(default=15, ge=1, le=600)
    resolution: str = Field(default="8k", pattern="^(720p|1080p|4k|8k)$")
    format: str = Field(default="mp4", pattern="^(mp4|png|gif|webp|mov)$")
    aspect_ratio: str = Field(default="16:9", pattern="^(16:9|9:16|1:1)$")
    model: Optional[str] = Field(None, max_length=100)
    negative_prompt: Optional[str] = Field(None, max_length=2000)
    voice_clone_id: Optional[str] = None
    voice_consent: bool = False


class VoiceCloneRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="en", max_length=10)
    consent: bool = Field(..., description="MUST be true to clone voice")


class ScriptGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=2000)
    duration_seconds: int = Field(default=30, ge=5, le=600)
    style: str = Field(default="professional", max_length=100)
    language: str = Field(default="en", max_length=10)


class PromptGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=2000)
    media_type: str = Field(default="video", pattern="^(video|picture|poster|animation)$")
    style: str = Field(default="cinematic", max_length=100)
    mood: str = Field(default="dramatic", max_length=100)
    camera_angle: str = Field(default="wide", max_length=100)
    lighting: str = Field(default="golden_hour", max_length=100)
    aspect_ratio: str = Field(default="16:9", max_length=20)


# ===================================================================
# Helpers
# ===================================================================

async def _get_subscription(db: AsyncSession, user_id: str) -> Subscription:
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        sub = Subscription(user_id=user_id, plan="free")
        db.add(sub)
        await db.flush()
    return sub


async def _is_owner_user(user: User) -> bool:
    """Check if the user is the platform owner or admin (bypasses all paid feature checks)."""
    return settings.is_owner_email(user.email) or user.is_admin


async def _enforce_trial_expiry(db: AsyncSession, sub: Subscription) -> Subscription:
    """
    If the user is on a trial plan and trial_end_at has passed,
    automatically downgrade to free plan and block paid-only features.
    """
    if sub.plan == "trial" and sub.trial_end_at:
        now = datetime.now(timezone.utc)
        trial_end = sub.trial_end_at
        if trial_end.tzinfo is None:
            trial_end = trial_end.replace(tzinfo=timezone.utc)
        if now >= trial_end:
            sub.plan = "free"
            sub.status = "active"
            sub.trial_start_at = None
            sub.trial_end_at = None
            await db.flush()
    return sub


def _is_paid_tier(plan: str) -> bool:
    """Check if the user is on a paid tier (PRO/MAX/BUSINESS/ENTERPRISE)."""
    return plan.lower() in ("pro", "pro_yearly", "max", "business", "enterprise")


def _is_paid_or_trial(plan: str) -> bool:
    """Check if the user is on a paid tier or active trial."""
    return plan.lower() in ("pro", "pro_yearly", "max", "business", "enterprise", "trial")


def _job_to_dict(job: MediaJob) -> Dict[str, Any]:
    return {
        "id": str(job.id),
        "media_type": job.job_type.value if job.job_type else "video",
        "status": job.status.value if job.status else "queued",
        "progress": job.progress or 0.0,
        "progress_stage": job.progress_stage,
        "topic": job.topic,
        "script": job.script,
        "scenes_text": job.scenes_text,
        "voice_style": job.voice_style.value if job.voice_style else None,
        "voice_prompt": job.voice_prompt,
        "language": job.language or "en",
        "duration_seconds": job.duration_seconds or 15,
        "resolution": job.resolution.value if job.resolution else "8k",
        "format": job.format or "mp4",
        "aspect_ratio": job.aspect_ratio or "16:9",
        "storyboard": job.storyboard,
        "scene_count": job.scene_count or 0,
        "voice_over_path": job.voice_over_path,
        "subtitles_path": job.subtitles_path,
        "accuracy_verified": job.accuracy_verified or False,
        "verification_report": job.verification_report,
        "output_path": job.output_path,
        "output_url": job.output_url,
        "output_resolution": job.output_resolution,
        "output_size_bytes": job.output_size_bytes,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


# ===================================================================
# Create Media Job
# ===================================================================

@router.post("/generate")
async def create_media_job(
    request: MediaCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a media generation job (video, picture, poster, animation)."""
    try:
        sub = await _get_subscription(db, str(current_user.id))

        is_owner = _is_owner_user(current_user)

        if not is_owner:
            sub = await _enforce_trial_expiry(db, sub)

            limits_service = MediaLimitsService(db)
            allowed, limit_info = await limits_service.check_limit(
                user_id=str(current_user.id),
                media_type=request.media_type,
                plan=sub.plan,
                status=sub.status,
            )
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=limit_info.get("message", "Daily limit reached"),
                )

            if not limits_service.validate_duration(request.duration_seconds, sub.plan, sub.status):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duration {request.duration_seconds}s not available on {sub.plan} plan",
                )

            if sub.plan == "free" and request.media_type == "video" and request.duration_seconds > 30:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Videos above 30 seconds require a PRO plan. Upgrade to unlock longer videos.",
                )

            if request.resolution in ("4k", "8k") and not _is_paid_tier(sub.plan):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"{request.resolution.upper()} resolution requires a PRO plan. Upgrade to unlock ultra-max resolution.",
                )

            voice_consent = request.voice_consent
        else:
            limits_service = MediaLimitsService(db)
            limit_info = {}
            voice_consent = request.voice_consent

        if request.media_type == "video":
            has_keys = (
                media_key_vault.kling.total_keys > 0 or
                media_key_vault.runway.total_keys > 0 or
                media_key_vault.fal.total_keys > 0
            )
            if not has_keys:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Video provider not configured. Please add video provider keys to continue.",
                )

        # Consume credits for media generation (paid plans only)
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)
        credit_service = CreditService(db, redis_client)
        credit_cost = CreditService.CREDIT_COSTS.get("image_generation", 10)
        if request.media_type == "video":
            credit_cost = 20
        elif request.media_type == "animation":
            credit_cost = 15

        if not is_owner and _is_paid_or_trial(sub.plan):
            decision = subscription_access.check_access(
                user_id=str(current_user.id),
                plan=sub.plan,
                status=sub.status,
                user_email=current_user.email,
            )
            if not decision.unlimited:
                can_use, reason = await credit_service.can_use_feature(
                    user_id=str(current_user.id),
                    feature="image_generation",
                    subscription=sub,
                    user_email=current_user.email,
                )
                if not can_use:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=f"Insufficient credits. You need {credit_cost} credits for this {request.media_type}.",
                    )

        # Create job
        job = MediaJob(
            user_id=current_user.id,
            job_type=MediaType(request.media_type),
            status=MediaStatus.QUEUED,
            topic=request.topic,
            script=request.script,
            scenes_text=request.scenes_text,
            voice_style=VoiceStyle(request.voice_style),
            voice_prompt=request.voice_prompt,
            language=request.language,
            duration_seconds=request.duration_seconds,
            resolution=MediaResolution(request.resolution),
            format=request.format,
            aspect_ratio=request.aspect_ratio,
            model=request.model,
            negative_prompt=request.negative_prompt,
            voice_clone_id=uuid.UUID(request.voice_clone_id) if request.voice_clone_id else None,
            voice_consent=request.voice_consent,
            progress=0.0,
            progress_stage="Queued",
        )
        db.add(job)
        await db.flush()

        # Increment usage
        await limits_service.increment_usage(str(current_user.id), request.media_type)

        # Consume credits after successful job creation (paid plans only)
        if not is_owner and _is_paid_or_trial(sub.plan):
            decision = subscription_access.check_access(
                user_id=str(current_user.id),
                plan=sub.plan,
                status=sub.status,
                user_email=current_user.email,
            )
            if not decision.unlimited:
                success, msg, remaining = await credit_service.consume_credits(
                    user_id=str(current_user.id),
                    amount=credit_cost,
                    action=f"media_{request.media_type}",
                    description=f"Generated {request.media_type} ({request.duration_seconds}s, {request.resolution})",
                    reference_id=str(job.id),
                )
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail=f"Insufficient credits. You need {credit_cost} credits for this {request.media_type}.",
                    )

        await db.commit()

        # Enqueue for processing
        await media_queue_service.enqueue(str(job.id))

        return {
            "success": True,
            "job_id": str(job.id),
            "status": "queued",
            "message": f"{request.media_type} generation started",
            "limits": limit_info,
            "credits_consumed": 0 if is_owner else (credit_cost if _is_paid_or_trial(sub.plan) else 0),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[media/generate] Unexpected error for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during media generation")


# ===================================================================
# AI SCRIPT GENERATOR - Generate professional narration scripts
# ===================================================================

@router.post("/generate-script")
async def generate_script(
    request: ScriptGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI generates a full professional narration script + cinematic prompt
    based on topic, duration, and style.
    """
    sub = await _get_subscription(db, str(current_user.id))
    sub = await _enforce_trial_expiry(db, sub)

    # Build the AI prompt
    system_prompt = (
        "You are a professional video scriptwriter and cinematographer. "
        "Generate a complete, professional narration script for the given topic, "
        "duration, and style. Also provide a cinematic visual prompt for each scene. "
        "Return JSON with 'script' (the full narration text) and 'cinematic_prompt' "
        "(a detailed visual description for the video generation)."
    )

    user_prompt = (
        f"Topic: {request.topic}\n"
        f"Duration: {request.duration_seconds} seconds\n"
        f"Style: {request.style}\n"
        f"Language: {request.language}\n\n"
        f"Generate a professional narration script that fits exactly {request.duration_seconds} seconds "
        f"of spoken audio (roughly 2.5 words per second). "
        f"Also provide a cinematic prompt describing the visual style, camera angles, lighting, and mood. "
        f"Return as JSON: {{\"script\": \"...\", \"cinematic_prompt\": \"...\"}}"
    )

    try:
        result = await ai_service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model_type=ModelType.CHAT,
        )
        content = result.content.strip()

        # Try to parse JSON from the response
        import json as json_lib
        try:
            # Find JSON in the response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json_lib.loads(content[start:end])
                script = parsed.get("script", content)
                cinematic_prompt = parsed.get("cinematic_prompt", "")
            else:
                script = content
                cinematic_prompt = ""
        except Exception:
            script = content
            cinematic_prompt = ""

        return {
            "success": True,
            "script": script,
            "cinematic_prompt": cinematic_prompt,
            "topic": request.topic,
            "duration_seconds": request.duration_seconds,
            "style": request.style,
            "language": request.language,
            "provider": result.provider,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {str(e)}")


# ===================================================================
# PROFESSIONAL PROMPT GENERATOR - Cinematography-grade prompts
# ===================================================================

@router.post("/generate-prompt")
async def generate_prompt(
    request: PromptGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI generates professional cinematography-grade prompts for images/videos
    based on topic, style, mood, camera angle, and lighting.
    """
    sub = await _get_subscription(db, str(current_user.id))
    sub = await _enforce_trial_expiry(db, sub)

    system_prompt = (
        "You are a professional cinematographer and AI prompt engineer. "
        "Generate detailed, professional prompts for AI image/video generation. "
        "Include camera angle, lens type, lighting setup, color grading, mood, "
        "composition, and technical details like a professional film director would."
    )

    user_prompt = (
        f"Topic: {request.topic}\n"
        f"Media Type: {request.media_type}\n"
        f"Style: {request.style}\n"
        f"Mood: {request.mood}\n"
        f"Camera Angle: {request.camera_angle}\n"
        f"Lighting: {request.lighting}\n"
        f"Aspect Ratio: {request.aspect_ratio}\n\n"
        f"Generate a professional, detailed prompt for AI {request.media_type} generation. "
        f"Include: camera angle, lens, lighting, color palette, mood, composition, "
        f"and any technical cinematography details. Make it specific and vivid."
    )

    try:
        result = await ai_service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model_type=ModelType.CHAT,
        )

        return {
            "success": True,
            "prompt": result.content.strip(),
            "topic": request.topic,
            "media_type": request.media_type,
            "style": request.style,
            "mood": request.mood,
            "camera_angle": request.camera_angle,
            "lighting": request.lighting,
            "aspect_ratio": request.aspect_ratio,
            "provider": result.provider,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prompt generation failed: {str(e)}")


# ===================================================================
# Get Job Status (live progress)
# ===================================================================

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get live progress and status of a media job."""
    result = await db.execute(
        select(MediaJob).where(MediaJob.id == job_id, MediaJob.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return _job_to_dict(job)


# ===================================================================
# List User's Jobs
# ===================================================================

@router.get("/jobs")
async def list_jobs(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the user's media jobs."""
    result = await db.execute(
        select(MediaJob)
        .where(MediaJob.user_id == current_user.id)
        .order_by(MediaJob.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    jobs = result.scalars().all()
    return {"jobs": [_job_to_dict(j) for j in jobs], "count": len(jobs)}


# ===================================================================
# Cancel Job
# ===================================================================

@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a queued or in-progress job."""
    result = await db.execute(
        select(MediaJob).where(MediaJob.id == job_id, MediaJob.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in (MediaStatus.COMPLETED, MediaStatus.FAILED, MediaStatus.CANCELLED):
        raise HTTPException(status_code=400, detail="Job already finished")

    job.status = MediaStatus.CANCELLED
    job.progress_stage = "Cancelled"
    await db.commit()

    return {"success": True, "message": "Job cancelled"}


# ===================================================================
# Download Output
# ===================================================================

@router.get("/jobs/{job_id}/download")
async def download_job(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the generated media file."""
    result = await db.execute(
        select(MediaJob).where(MediaJob.id == job_id, MediaJob.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != MediaStatus.COMPLETED or not job.output_path:
        raise HTTPException(status_code=400, detail="Output not ready")

    if not os.path.exists(job.output_path):
        raise HTTPException(status_code=404, detail="Output file missing")

    # Log download
    db.add(MediaDownload(
        job_id=job.id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    ))
    await db.commit()

    return FileResponse(
        job.output_path,
        filename=f"proai_{job.job_type.value}_{job.id}.{job.format or 'mp4'}",
        media_type="application/octet-stream",
    )


# ===================================================================
# Voice Cloning
# ===================================================================

@router.post("/voice-clone")
async def create_voice_clone(
    name: str = Form(..., min_length=1, max_length=100),
    language: str = Form("en", max_length=10),
    consent: bool = Form(False),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a 30-second voice sample for cloning (requires consent)."""
    if not consent:
        raise HTTPException(status_code=400, detail="Voice cloning requires explicit consent")

    # Validate file type
    if not file.filename or not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".ogg")):
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    # Save audio file
    voice_dir = Path(settings.MEDIA_OUTPUT_DIR) / "voice_clones"
    voice_dir.mkdir(parents=True, exist_ok=True)
    audio_path = voice_dir / f"clone_{current_user.id}_{uuid.uuid4().hex[:8]}{Path(file.filename).suffix}"

    content = await file.read()
    with open(audio_path, "wb") as f:
        f.write(content)

    # Process clone
    result = await voice_over_service.clone_voice(
        audio_path=str(audio_path),
        name=name,
        language=language,
        consent=consent,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Voice clone failed"))

    # Save to DB
    clone = MediaVoiceClone(
        user_id=current_user.id,
        name=name,
        audio_path=str(audio_path),
        duration_seconds=result.get("duration_seconds", 0),
        language=language,
        consent_given=consent,
        status="ready",
    )
    db.add(clone)
    await db.commit()

    return {
        "success": True,
        "id": str(clone.id),
        "name": name,
        "language": language,
        "duration_seconds": clone.duration_seconds,
        "consent_given": True,
        "status": "ready",
    }


@router.get("/voice-clones")
async def list_voice_clones(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the user's voice clones."""
    result = await db.execute(
        select(MediaVoiceClone).where(MediaVoiceClone.user_id == current_user.id).order_by(MediaVoiceClone.created_at.desc())
    )
    clones = result.scalars().all()
    return {
        "clones": [
            {
                "id": str(c.id),
                "name": c.name,
                "language": c.language,
                "duration_seconds": c.duration_seconds,
                "consent_given": c.consent_given,
                "status": c.status,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in clones
        ]
    }


# ===================================================================
# Limits & Usage
# ===================================================================

@router.get("/limits")
async def get_media_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the user's media limits and current usage."""
    sub = await _get_subscription(db, str(current_user.id))
    limits_service = MediaLimitsService(db)

    usage = await limits_service.get_usage_summary(str(current_user.id))
    is_owner = _is_owner_user(current_user)

    if is_owner:
        durations = limits_service.get_available_durations("max", "active")
        return {
            "plan": sub.plan,
            "videos_used": usage["videos_used"],
            "pictures_used": usage["pictures_used"],
            "animations_used": usage["animations_used"],
            "video_limit": -1,
            "picture_limit": -1,
            "animation_limit": -1,
            "available_durations": durations["durations"],
            "unlimited": True,
        }

    durations = limits_service.get_available_durations(sub.plan, sub.status)

    if sub.plan == "free":
        video_limit = settings.MEDIA_FREE_VIDEO_LIMIT
        picture_limit = settings.MEDIA_FREE_PICTURE_LIMIT
        animation_limit = settings.MEDIA_FREE_ANIMATION_LIMIT
        unlimited = False
    elif sub.plan in ("max", "enterprise") and sub.status == "active":
        video_limit = -1
        picture_limit = -1
        animation_limit = -1
        unlimited = True
    else:
        video_limit = settings.MEDIA_PAID_VIDEO_LIMIT
        picture_limit = settings.MEDIA_PAID_PICTURE_LIMIT
        animation_limit = settings.MEDIA_PAID_ANIMATION_LIMIT
        unlimited = False

    return {
        "plan": sub.plan,
        "videos_used": usage["videos_used"],
        "pictures_used": usage["pictures_used"],
        "animations_used": usage["animations_used"],
        "video_limit": video_limit,
        "picture_limit": picture_limit,
        "animation_limit": animation_limit,
        "available_durations": durations["durations"],
        "unlimited": unlimited,
    }


# ===================================================================
# Verify Subtitle Accuracy (manual check)
# ===================================================================

@router.post("/verify-subtitles")
async def verify_subtitles(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-run the word-for-word subtitle verification for a job."""
    result = await db.execute(
        select(MediaJob).where(MediaJob.id == job_id, MediaJob.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.script or not job.subtitles_path:
        raise HTTPException(status_code=400, detail="No subtitles to verify")

    verify = await subtitle_verification_service.verify_subtitles(
        script=job.script,
        subtitle_path=job.subtitles_path,
        language=job.language or "en",
    )

    job.verification_report = verify
    job.accuracy_verified = verify.get("passed", False)
    await db.commit()

    return verify


# ===================================================================
# Engine Status
# ===================================================================

@router.get("/status")
async def media_engine_status():
    """Get media engine status."""
    return {
        "enabled": settings.MEDIA_ENGINE_ENABLED,
        "queue_workers": settings.MEDIA_QUEUE_MAX_WORKERS,
        "default_resolution": settings.MEDIA_DEFAULT_RESOLUTION,
        "upscaler_enabled": settings.MEDIA_UPSCALER_ENABLED,
        "subtitle_verify_enabled": settings.MEDIA_SUBTITLE_VERIFY_ENABLED,
        "auto_editor": {
            "enabled": settings.AUTO_EDITOR_ENABLED,
            "requires_pro": settings.AUTO_EDITOR_REQUIRES_PRO,
            "max_upload_mb": settings.AUTO_EDITOR_MAX_UPLOAD_SIZE_MB,
            "max_clips": settings.AUTO_EDITOR_MAX_CLIPS,
            "max_duration": settings.AUTO_EDITOR_MAX_DURATION_SECONDS,
            "presets": ["tiktok", "youtube", "reels", "instagram", "story", "custom"],
            "whisper_model": settings.AUTO_EDITOR_WHISPER_MODEL,
        },
        "engines": media_provider_registry.get_status()["providers"],
        "key_vault": media_key_vault.get_status() if "media_key_vault" in dir() else {},
        "voice_styles": settings.MEDIA_VOICE_STYLES.split(","),
        "script_languages": settings.MEDIA_SCRIPT_LANGUAGES.split(","),
        "free_durations": [int(d) for d in settings.MEDIA_FREE_DURATIONS.split(",") if d.strip()],
        "paid_durations": [int(d) for d in settings.MEDIA_PAID_DURATIONS.split(",") if d.strip()],
    }


# ===================================================================
# VOICE ENGINE — Voice Catalog & Provider Status
# ===================================================================

@router.get("/voice-catalog")
async def get_voice_catalog_endpoint():
    """
    Get the full voice catalog: 14 voice styles × 40+ languages.
    Each voice works in every language.
    """
    catalog = get_voice_catalog()
    return {
        "success": True,
        "voices": catalog["voices"],
        "languages": catalog["languages"],
        "total_voices": catalog["total_voices"],
        "total_languages": catalog["total_languages"],
        "combinations": catalog["combinations"],
        "message": "14 voices × 40+ languages — each voice works in every language",
    }


@router.get("/voice-engine/status")
async def voice_engine_status():
    """
    Get voice engine status: permanent provider chain + key rotation +
    forced alignment. Confirms the voice system is active.
    """
    return {
        "success": True,
        "voice_engine_active": True,
        "provider_chain": tts_router.get_provider_status(),
        "forced_alignment": forced_alignment_service.get_status(),
        "voice_catalog": {
            "total_voices": len(VOICE_STYLES),
            "total_languages": len(SUPPORTED_LANGUAGES),
        },
        "voice_clone": {
            "max_seconds": settings.MEDIA_VOICE_CLONE_MAX_SECONDS,
            "encrypted_storage": True,
            "consent_required": True,
        },
        "message": "VOICE ENGINE ACTIVE — girl/boy/custom voices in 40+ languages, "
                   "permanent providers, word-perfect sync",
    }


@router.post("/voice-engine/preview")
async def preview_voice(
    text: str = "",
    voice_style: str = "adult_female",
    language: str = "en",
    voice_prompt: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Preview a voice by generating a short audio sample.
    Uses the permanent TTS provider chain.
    """
    sample_text = text.strip() if text.strip() else "Hello, this is a voice preview sample."
    if len(sample_text) > 500:
        sample_text = sample_text[:500]

    result = await voice_over_service.generate_voice_over(
        script=sample_text,
        voice_style=voice_style,
        voice_prompt=voice_prompt,
        language=language,
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Voice preview failed"))

    return {
        "success": True,
        "path": result.get("path"),
        "provider": result.get("provider"),
        "voice_style": result.get("voice_style"),
        "language": result.get("language"),
    }


# ===================================================================
# AI THUMBNAIL MAKER - Auto-generate 5 clickable thumbnails
# ===================================================================

class ThumbnailGenerateRequest(BaseModel):
    language: str = Field(default="en", max_length=10)


class ThumbnailSelectRequest(BaseModel):
    thumbnail_id: str = Field(..., min_length=1)


@router.post("/thumbnails/generate/{job_id}")
async def generate_thumbnails(
    job_id: str,
    request: ThumbnailGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate 5 clickable thumbnails for a completed video."""
    # Verify job exists and belongs to user
    result = await db.execute(
        select(MediaJob).where(MediaJob.id == job_id, MediaJob.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Generate thumbnails
    thumbnails = await thumbnail_maker_service.generate_thumbnails(
        db=db,
        job_id=job_id,
        user_id=str(current_user.id),
        video_topic=job.topic or "Video",
        language=request.language or job.language or "en",
        count=5,
    )
    
    return thumbnails


@router.post("/thumbnails/select/{job_id}")
async def select_thumbnail(
    job_id: str,
    request: ThumbnailSelectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """User selects their preferred thumbnail for a video."""
    result = await thumbnail_maker_service.select_thumbnail(
        db=db,
        thumbnail_id=request.thumbnail_id,
        user_id=str(current_user.id),
        job_id=job_id,
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to select thumbnail"))
    
    return result


@router.get("/thumbnails/{job_id}")
async def get_thumbnails(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all thumbnails for a video job."""
    # Verify job exists and belongs to user
    result = await db.execute(
        select(MediaJob).where(MediaJob.id == job_id, MediaJob.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    thumbnails = await thumbnail_maker_service.get_thumbnails(
        db=db,
        job_id=job_id,
        user_id=str(current_user.id),
    )
    
    return thumbnails


# ===================================================================
# MEME MAKER - Generate funny memes from text
# ===================================================================

class MemeGenerateRequest(BaseModel):
    meme_text: str = Field(..., min_length=1, max_length=500)
    meme_type: str = Field(default="image", pattern="^(image|video)$")
    template: Optional[str] = Field(None, max_length=100)


@router.post("/memes/generate")
async def generate_meme(
    request: MemeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a meme from user text."""
    result = await meme_maker_service.generate_meme(
        user_id=str(current_user.id),
        meme_text=request.meme_text,
        meme_type=request.meme_type,
        template=request.template,
    )
    
    if not result.get("success"):
        if result.get("limit_reached"):
            raise HTTPException(status_code=429, detail=result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error", "Meme generation failed"))
    
    return result


@router.get("/memes")
async def list_memes(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's meme history."""
    memes = await meme_maker_service.get_user_memes(
        user_id=str(current_user.id),
        limit=limit,
        offset=offset,
    )
    
    return memes


@router.get("/memes/{meme_id}")
async def get_meme(
    meme_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific meme."""
    meme = await meme_maker_service.get_meme(
        meme_id=meme_id,
        user_id=str(current_user.id),
    )
    
    if not meme.get("success"):
        raise HTTPException(status_code=404, detail=meme.get("error", "Meme not found"))
    
    return meme


# ===================================================================
# INTERNAL: Media Worker Callback (BullMQ worker → Backend)
# ===================================================================

class WorkerCompleteRequest(BaseModel):
    job_id: str
    success: bool
    output_url: Optional[str] = None
    output_path: Optional[str] = None
    gcs_path: Optional[str] = None
    engine: Optional[str] = None
    error: Optional[str] = None
    gcs_warning: Optional[str] = None
    worker_secret: str


@router.post("/internal/worker-complete")
async def worker_complete(
    payload: WorkerCompleteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Called by the Node.js BullMQ media worker when a job completes.
    Updates the PostgreSQL job record with the result.
    """
    if payload.worker_secret != INTERNAL_WORKER_SECRET:
        raise HTTPException(status_code=403, detail="Invalid worker secret")

    result = await db.execute(
        select(MediaJob).where(MediaJob.id == payload.job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if payload.success:
        job.status = MediaStatus.COMPLETED
        job.output_url = payload.output_url
        job.output_path = payload.output_path or job.output_path
        if payload.gcs_path:
            job.output_url = f"https://storage.googleapis.com/{settings.GOOGLE_CLOUD_STORAGE_BUCKET}/{payload.gcs_path}"
        job.progress = 100.0
        job.progress_stage = "Completed"
        job.completed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        if payload.gcs_warning:
            job.error_message = (job.error_message or "") + f"GCS: {payload.gcs_warning}"
    else:
        job.status = MediaStatus.FAILED
        job.error_message = payload.error or "Worker failed"
        job.progress_stage = "Failed"

    await db.commit()
    return {"success": True, "job_id": payload.job_id}

