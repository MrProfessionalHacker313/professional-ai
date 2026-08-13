"""
Professional AI - Auto Video Editor Routes
API endpoints for professional automatic video editing:
- Upload raw clips → AI auto-edits → export professional video
- Platform presets: TikTok, YouTube, Reels, Instagram, Story
- Manual editor tools: trim, cut, merge, rotate, filters, text, stickers, music
- PAID ONLY feature (PRO users only)
"""

from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

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
from app.models.media_engine import AutoEditorJob, AutoEditStatus, AutoEditPreset
from app.services.auth_service import get_current_user
from app.services.media.limits import MediaLimitsService
from app.services.unlimited_mode import subscription_access
from app.services.media.auto_editor import auto_editor_service, PLATFORM_PRESETS

router = APIRouter(prefix="/api/media/auto-edit", tags=["Auto Video Editor"])


# ===================================================================
# SCHEMAS
# ===================================================================

class AutoEditStartRequest(BaseModel):
    preset: str = Field(default="custom", pattern="^(tiktok|youtube|reels|instagram|story|custom)$")
    raw_files: List[str] = Field(default_factory=list)
    add_transitions: bool = True
    add_captions: bool = True
    color_grade: bool = True
    stabilize: bool = True
    ken_burns: bool = True
    add_intro_outro: bool = True
    adjust_speed: bool = True
    background_music: bool = True
    watermark_toggle: bool = True
    caption_language: str = Field(default="en", max_length=10)
    output_aspect_ratio: str = Field(default="16:9", pattern="^(16:9|9:16|1:1)$")
    output_resolution: str = Field(default="1080p", pattern="^(720p|1080p|4k|8k)$")
    trim_start: Optional[float] = None
    trim_end: Optional[float] = None
    speed_factor: Optional[float] = Field(None, ge=0.25, le=4.0)
    custom_transition: Optional[str] = Field(None, max_length=30)
    text_overlays: List[Dict[str, Any]] = Field(default_factory=list)
    stickers: List[str] = Field(default_factory=list)
    voice_over_id: Optional[str] = None


class AutoEditManualRequest(BaseModel):
    action: str = Field(..., pattern="^(trim|cut|merge|rotate|filter|text_overlay|sticker|speed|watermark|export_resolution)$")
    params: Dict[str, Any] = Field(default_factory=dict)


# ===================================================================
# HELPERS
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


def _job_to_dict(job: AutoEditorJob) -> Dict[str, Any]:
    return {
        "id": str(job.id),
        "status": job.status.value if job.status else "uploading",
        "preset": job.preset.value if job.preset else "custom",
        "progress": job.progress or 0.0,
        "progress_stage": job.progress_stage,
        "raw_file_count": job.raw_file_count or 0,
        "scene_analysis": job.scene_analysis,
        "best_moments": job.best_moments,
        "cuts_made": job.cuts_made or 0,
        "add_transitions": job.add_transitions,
        "add_captions": job.add_captions,
        "color_grade": job.color_grade,
        "stabilize": job.stabilize,
        "ken_burns": job.ken_burns,
        "add_intro_outro": job.add_intro_outro,
        "adjust_speed": job.adjust_speed,
        "background_music": job.background_music,
        "watermark_toggle": job.watermark_toggle,
        "caption_language": job.caption_language or "en",
        "output_aspect_ratio": job.output_aspect_ratio or "16:9",
        "output_resolution": job.output_resolution or "1080p",
        "output_path": job.output_path,
        "output_url": job.output_url,
        "output_size_bytes": job.output_size_bytes,
        "thumbnail_path": job.thumbnail_path,
        "duration_seconds": job.duration_seconds,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


async def _check_pro_access(user: User, plan: str, status: str) -> bool:
    """Check if user has PRO access (auto-editor is PRO-only). Owners and admins always pass."""
    if settings.is_owner_email(user.email) or user.is_admin:
        return True
    if not settings.AUTO_EDITOR_REQUIRES_PRO:
        return True
    decision = subscription_access.check_access(
        user_id=str(user.id),
        plan=plan,
        status=status,
    )
    return decision.unlimited


# ===================================================================
# PLATFORM PRESETS
# ===================================================================

@router.get("/presets")
async def get_presets():
    """Get available platform presets for video export."""
    return {
        "success": True,
        "presets": {
            key: {
                "name": cfg.name,
                "aspect_ratio": cfg.aspect_ratio,
                "width": cfg.width,
                "height": cfg.height,
                "max_duration": cfg.max_duration,
                "recommended_bitrate": cfg.recommended_bitrate,
            }
            for key, cfg in PLATFORM_PRESETS.items()
        },
        "message": "TikTok (9:16), YouTube (16:9), Reels (9:16), Instagram (1:1), Story (9:16), Custom",
    }


# ===================================================================
# UPLOAD RAW CLIPS
# ===================================================================

@router.post("/upload")
async def upload_raw_clip(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
):
    """
    Upload a raw video clip for auto-editing.
    Returns a job_id to use when starting the auto-edit.
    """
    sub = await _get_subscription(db, str(current_user.id))
    if not await _check_pro_access(current_user, sub.plan, sub.status):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professional editing available on PRO. Upgrade to use this feature.",
        )

    allowed_video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
    ext = Path(file.filename or "clip.mp4").suffix.lower()
    if ext not in allowed_video_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {ext}. Allowed: {', '.join(sorted(allowed_video_exts))}",
        )

    content = await file.read()
    max_size = settings.AUTO_EDITOR_MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max: {settings.AUTO_EDITOR_MAX_UPLOAD_SIZE_MB}MB",
        )

    job = AutoEditorJob(
        user_id=current_user.id,
        status=AutoEditStatus.UPLOADING,
        preset=AutoEditPreset.CUSTOM,
        raw_files=[],
        raw_file_count=0,
    )
    db.add(job)
    await db.flush()

    file_path = auto_editor_service.save_uploaded_file(
        str(current_user.id), content, file.filename or "clip.mp4"
    )

    job.raw_files = [file_path]
    job.raw_file_count = 1
    await db.commit()

    return {
        "success": True,
        "job_id": str(job.id),
        "message": "Clip uploaded. Use /start to begin auto-editing.",
    }


# ===================================================================
# START AUTO-EDIT
# ===================================================================

@router.post("/start")
async def start_auto_edit(
    request: AutoEditStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start the professional auto-editing pipeline. All processing on server."""
    sub = await _get_subscription(db, str(current_user.id))
    if not await _check_pro_access(current_user, sub.plan, sub.status):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professional editing available on PRO. Upgrade to use this feature.",
        )

    limits_service = MediaLimitsService(db)
    allowed, limit_info = await limits_service.check_limit(
        user_id=str(current_user.id),
        media_type="auto_edit",
        plan=sub.plan,
        status=sub.status,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=limit_info.get("message", "Auto-edit limit reached. Upgrade for more."),
        )

    if not request.raw_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide raw_files (list of file paths from /upload).",
        )

    job = AutoEditorJob(
        user_id=current_user.id,
        status=AutoEditStatus.ANALYZING,
        preset=AutoEditPreset(request.preset),
        raw_files=request.raw_files,
        raw_file_count=len(request.raw_files),
        add_transitions=request.add_transitions,
        add_captions=request.add_captions,
        color_grade=request.color_grade,
        stabilize=request.stabilize,
        ken_burns=request.ken_burns,
        add_intro_outro=request.add_intro_outro,
        adjust_speed=request.adjust_speed,
        background_music=request.background_music,
        watermark_toggle=request.watermark_toggle,
        caption_language=request.caption_language,
        output_aspect_ratio=request.output_aspect_ratio,
        output_resolution=request.output_resolution,
        trim_start=request.trim_start,
        trim_end=request.trim_end,
        speed_factor=request.speed_factor,
        custom_transition=request.custom_transition,
        text_overlays=request.text_overlays or [],
        stickers=request.stickers or [],
    )
    db.add(job)
    await db.flush()

    await limits_service.increment_auto_edit_usage(str(current_user.id))
    await db.commit()

    asyncio.create_task(_process_auto_edit_job(str(job.id)))

    return {
        "success": True,
        "job_id": str(job.id),
        "status": "analyzing",
        "message": "Auto-editing started — AI will cut, transition, caption, color-grade, and export.",
        "limits": limit_info,
    }


# ===================================================================
# JOB STATUS
# ===================================================================

@router.get("/jobs/{job_id}")
async def get_auto_edit_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get live progress of an auto-edit job."""
    result = await db.execute(
        select(AutoEditorJob).where(
            AutoEditorJob.id == job_id, AutoEditorJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Auto-edit job not found")
    return _job_to_dict(job)


@router.get("/jobs")
async def list_auto_edit_jobs(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the user's auto-edit jobs."""
    result = await db.execute(
        select(AutoEditorJob)
        .where(AutoEditorJob.user_id == current_user.id)
        .order_by(AutoEditorJob.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    jobs = result.scalars().all()
    return {"jobs": [_job_to_dict(j) for j in jobs], "count": len(jobs)}


# ===================================================================
# DOWNLOAD
# ===================================================================

@router.get("/jobs/{job_id}/download")
async def download_auto_edit_result(
    job_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the professionally edited video."""
    result = await db.execute(
        select(AutoEditorJob).where(
            AutoEditorJob.id == job_id, AutoEditorJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Auto-edit job not found")

    if job.status != AutoEditStatus.COMPLETED or not job.output_path:
        raise HTTPException(status_code=400, detail="Output not ready")

    if not os.path.exists(job.output_path):
        raise HTTPException(status_code=404, detail="Output file missing")

    from app.models.media_engine import MediaDownload
    db.add(MediaDownload(
        job_id=job.id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    ))
    await db.commit()

    return FileResponse(
        job.output_path,
        filename=f"proai_autoedit_{job.preset.value}_{job.id}.mp4",
        media_type="video/mp4",
    )


# ===================================================================
# MANUAL EDIT CONTROLS
# ===================================================================

@router.post("/jobs/{job_id}/manual-edit")
async def apply_manual_edit(
    job_id: str,
    request: AutoEditManualRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Apply a manual editor action to an existing completed auto-edit job."""
    sub = await _get_subscription(db, str(current_user.id))
    if not await _check_pro_access(current_user, sub.plan, sub.status):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manual editing tools available on PRO.",
        )

    result = await db.execute(
        select(AutoEditorJob).where(
            AutoEditorJob.id == job_id, AutoEditorJob.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Auto-edit job not found")

    if job.status != AutoEditStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job must be completed first")

    if not job.output_path or not Path(job.output_path).exists():
        raise HTTPException(status_code=400, detail="Output file not available")

    work_dir = Path(settings.AUTO_EDITOR_TEMP_DIR) / f"manual_{job_id}"
    work_dir.mkdir(parents=True, exist_ok=True)

    current_file = job.output_path
    action = request.action
    params = request.params or {}
    result_msg = "No changes made"

    try:
        if action == "trim":
            job.trim_start = params.get("start", job.trim_start)
            job.trim_end = params.get("end", job.trim_end)
            result_msg = f"Trim updated"

        elif action == "cut":
            cut_start = params.get("start", 0)
            cut_end = params.get("end", 0)
            analysis = job.scene_analysis or []
            analysis = [s for s in analysis if not (cut_start <= s.get("start", 0) and s.get("end", 0) <= cut_end)]
            job.scene_analysis = analysis
            job.cuts_made = (job.cuts_made or 0) + 1
            result_msg = f"Removed segment {cut_start}s–{cut_end}s"

        elif action == "merge":
            other_job_id = params.get("job_id")
            if other_job_id:
                other_result = await db.execute(
                    select(AutoEditorJob).where(
                        AutoEditorJob.id == other_job_id,
                        AutoEditorJob.user_id == current_user.id,
                        AutoEditorJob.status == AutoEditStatus.COMPLETED,
                    )
                )
                other = other_result.scalar_one_or_none()
                if other and other.output_path and Path(other.output_path).exists():
                    merged = await auto_editor_service.merge_videos(
                        [current_file, other.output_path],
                        str(work_dir / "merged.mp4"),
                    )
                    if merged != current_file:
                        job.output_path = merged
                        result_msg = "Videos merged"

        elif action == "rotate":
            degrees = params.get("degrees", 0)
            rotated = await auto_editor_service.rotate_video(current_file, degrees)
            if rotated != current_file:
                job.output_path = rotated
                result_msg = f"Rotated {degrees}°"

        elif action == "filter":
            filter_name = params.get("filter", "cinematic")
            intensity = params.get("intensity", 1.0)
            filtered = await auto_editor_service.apply_filter(current_file, filter_name, intensity)
            if filtered != current_file:
                job.output_path = filtered
                result_msg = f"Filter '{filter_name}' applied"

        elif action == "text_overlay":
            overlay = params.get("overlay", {})
            if overlay:
                text_file = await auto_editor_service.apply_text_overlay(
                    current_file, overlay, work_dir
                )
                if text_file != current_file:
                    job.output_path = text_file
                    job.text_overlays = (job.text_overlays or []) + [overlay]
                    result_msg = "Text overlay added"

        elif action == "sticker":
            sticker_path = params.get("sticker_path", "")
            if sticker_path and Path(sticker_path).exists():
                stickered = await auto_editor_service.add_sticker_overlay(
                    current_file, sticker_path, work_dir
                )
                if stickered != current_file:
                    job.output_path = stickered
                    job.stickers = (job.stickers or []) + [sticker_path]
                    result_msg = "Sticker added"

        elif action == "speed":
            factor = params.get("factor", 1.0)
            speed_file = await auto_editor_service._adjust_speed(current_file, work_dir, factor)
            if speed_file != current_file:
                job.output_path = speed_file
                job.speed_factor = factor
                result_msg = f"Speed set to {factor}x"

        elif action == "watermark":
            watermark_path = params.get("watermark_path", "")
            if watermark_path and Path(watermark_path).exists():
                watermarked = await auto_editor_service.apply_watermark(
                    current_file, watermark_path, work_dir
                )
                if watermarked != current_file:
                    job.output_path = watermarked
                    job.watermark_toggle = True
                    result_msg = "Watermark applied"

        elif action == "export_resolution":
            res = params.get("resolution", "1080p")
            fmt = params.get("format", "mp4")
            exp_path = str(work_dir / f"export_{res}.{fmt}")
            exported = await auto_editor_service.export_resolution(current_file, exp_path, res, fmt)
            job.output_path = exported
            job.output_resolution = res
            result_msg = f"Exported as {res}"

        if job.output_path and Path(job.output_path).exists():
            job.output_size_bytes = Path(job.output_path).stat().st_size
            job.duration_seconds = auto_editor_service._get_video_duration(job.output_path)

        await db.commit()
    except Exception as e:
        logger.error(f"Manual edit failed for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Manual edit failed: {str(e)}")

    return {
        "success": True,
        "message": result_msg,
        "output_path": job.output_path,
        "output_size_bytes": job.output_size_bytes,
    }


# ===================================================================
# BACKGROUND PROCESSING
# ===================================================================

async def _process_auto_edit_job(job_id: str):
    """Background task: runs the full auto-editing pipeline on the server."""
    from app.database import _get_session_factory

    factory = _get_session_factory()
    async with factory() as db:
        result = await db.execute(
            select(AutoEditorJob).where(AutoEditorJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return

        try:
            job.status = AutoEditStatus.ANALYZING
            job.started_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            job.progress = 5.0
            job.progress_stage = "Analyzing scenes"
            await db.commit()

            raw_files = job.raw_files or []
            if not raw_files:
                raise ValueError("No raw files to edit")

            # Analyze scenes
            segments = await auto_editor_service.analyze_scenes(raw_files[0])
            job.scene_analysis = [
                {
                    "start": s.start, "end": s.end,
                    "score": round(s.score, 3), "keep": s.keep, "reason": s.reason,
                }
                for s in segments
            ]
            job.best_moments = [
                {"start": s.start, "end": s.end, "score": round(s.score, 3)}
                for s in segments if s.keep
            ]
            job.cuts_made = sum(1 for s in segments if not s.keep)
            job.progress = 15.0
            job.progress_stage = f"Scene analysis: {job.cuts_made} cuts"
            await db.commit()

            editing_options = {
                "add_transitions": job.add_transitions,
                "add_captions": job.add_captions,
                "color_grade": job.color_grade,
                "stabilize": job.stabilize,
                "ken_burns": job.ken_burns,
                "add_intro_outro": job.add_intro_outro,
                "adjust_speed": job.adjust_speed,
                "background_music": job.background_music,
                "caption_language": job.caption_language or "en",
            }

            manual_overrides = {
                "trim_start": job.trim_start,
                "trim_end": job.trim_end,
                "speed_factor": job.speed_factor,
                "aspect_ratio": job.output_aspect_ratio,
            }

            job.status = AutoEditStatus.EDITING
            job.progress = 20.0
            job.progress_stage = "Editing"
            await db.commit()

            async def progress_cb(pct: float, stage: str):
                job.progress = float(pct)
                job.progress_stage = stage
                await db.commit()

            result_data = await auto_editor_service.run_edit_pipeline(
                job_id=str(job.id),
                raw_files=raw_files,
                segments=segments,
                preset=job.preset.value if job.preset else "custom",
                editing_options=editing_options,
                manual_overrides=manual_overrides,
                progress_callback=progress_cb,
            )

            if result_data.get("success"):
                job.status = AutoEditStatus.COMPLETED
                job.progress = 100.0
                job.progress_stage = "Completed"
                job.output_path = result_data.get("output_path")
                job.output_size_bytes = result_data.get("output_size_bytes")
                job.duration_seconds = result_data.get("duration_seconds")
                job.completed_at = __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc
                )
            else:
                job.status = AutoEditStatus.FAILED
                job.error_message = result_data.get("error", "Unknown error")
                job.progress_stage = "Failed"

            await db.commit()
        except Exception as e:
            logger.error(f"Auto-edit pipeline error for {job_id}: {e}")
            job.status = AutoEditStatus.FAILED
            job.error_message = str(e)[:500]
            job.progress_stage = "Failed"
            try:
                await db.commit()
            except Exception:
                pass
