"""
Professional AI - Media Engine Models
SQLAlchemy models for videos, pictures, posters, animations, voice clones,
storyboard scenes, subtitle verification, and media usage tracking.
"""

from __future__ import annotations

from datetime import datetime
import uuid
import enum
from typing import Optional, Any

from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Enum, JSON, Index, UniqueConstraint, UUID
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


# ===================================================================
# ENUMS
# ===================================================================

class MediaType(str, enum.Enum):
    VIDEO = "video"
    PICTURE = "picture"
    POSTER = "poster"
    ANIMATION = "animation"


class MediaStatus(str, enum.Enum):
    QUEUED = "queued"
    STORYBOARDING = "storyboarding"
    GENERATING = "generating"
    VOICE_OVER = "voice_over"
    SUBTITLING = "subtitling"
    VERIFYING = "verifying"
    UPSCALING = "upscaling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VoiceStyle(str, enum.Enum):
    YOUNG_GIRL = "young_girl"
    YOUNG_BOY = "young_boy"
    ADULT_MALE = "adult_male"
    ADULT_FEMALE = "adult_female"
    NEWS_ANCHOR = "news_anchor"
    ROBOTIC = "robotic"
    CARTOON = "cartoon"
    VILLAIN = "villain"
    HERO = "hero"
    CUSTOM = "custom"
    CLONE = "clone"


class MediaResolution(str, enum.Enum):
    P720 = "720p"
    P1080 = "1080p"
    K4 = "4k"
    K8 = "8k"


class AutoEditStatus(str, enum.Enum):
    UPLOADING = "uploading"
    ANALYZING = "analyzing"
    EDITING = "editing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AutoEditPreset(str, enum.Enum):
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    REELS = "reels"
    INSTAGRAM = "instagram"
    STORY = "story"
    CUSTOM = "custom"


# ===================================================================
# MEDIA JOBS - master record for every media generation request
# ===================================================================

class MediaJob(Base):
    __tablename__ = "media_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type: Mapped[MediaType] = mapped_column(Enum(MediaType), nullable=False)
    status: Mapped[MediaStatus] = mapped_column(Enum(MediaStatus), default=MediaStatus.QUEUED, nullable=False, index=True)

    # User input
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scenes_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_style: Mapped[VoiceStyle] = mapped_column(Enum(VoiceStyle), default=VoiceStyle.ADULT_FEMALE)
    voice_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    duration_seconds: Mapped[int] = mapped_column(Integer, default=15)
    resolution: Mapped[MediaResolution] = mapped_column(Enum(MediaResolution), default=MediaResolution.K8)
    format: Mapped[str] = mapped_column(String(10), default="mp4")
    aspect_ratio: Mapped[str] = mapped_column(String(10), default="16:9")
    quality_slider: Mapped[str] = mapped_column(String(10), default="8k")
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Storyboard (generated)
    storyboard: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    scene_count: Mapped[int] = mapped_column(Integer, default=0)
    storyboard_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Voice over
    voice_over_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    voice_over_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    voice_clone_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    voice_consent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Subtitles & verification
    subtitles_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subtitle_verify_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    verification_report: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    accuracy_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Output
    output_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_resolution: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    output_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_render_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    progress_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)

    # Timestamps
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_media_jobs_user_status", "user_id", "status"),
        Index("idx_media_jobs_created", "created_at"),
    )


# ===================================================================
# MEDIA SCENES - individual scene within a media job
# ===================================================================

class MediaScene(Base):
    __tablename__ = "media_scenes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(Float, default=5.0)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    output_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scene_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON, default={})
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_media_scenes_job", "job_id", "scene_number"),
    )


# ===================================================================
# SUBTITLE TRACKS - one per language per job
# ===================================================================

class SubtitleTrack(Base):
    __tablename__ = "media_subtitle_tracks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    source_script: Mapped[str] = mapped_column(Text, nullable=False)
    subtitle_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("job_id", "language", name="uq_media_subtitle_job_lang"),
    )


# ===================================================================
# SUBTITLE VERIFICATION - word-by-word match results
# ===================================================================

class SubtitleVerification(Base):
    __tablename__ = "media_subtitle_verifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    script_words: Mapped[int] = mapped_column(Integer, nullable=False)
    subtitle_words: Mapped[int] = mapped_column(Integer, nullable=False)
    matched_words: Mapped[int] = mapped_column(Integer, nullable=False)
    mismatch_words: Mapped[int] = mapped_column(Integer, nullable=False)
    match_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    mismatches: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=[])
    regenerated: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_media_subtitle_verify_job", "job_id"),
    )


# ===================================================================
# VOICE CLONES - user-uploaded voice samples for cloning
# ===================================================================

class MediaVoiceClone(Base):
    __tablename__ = "media_voice_clones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    audio_path: Mapped[str] = mapped_column(Text, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en")
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30), default="ready")
    provider_clone_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_media_voice_clones_user", "user_id"),
    )


# ===================================================================
# MEDIA USAGE - daily limits enforcement
# ===================================================================

class MediaUsage(Base):
    __tablename__ = "media_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    usage_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    videos_count: Mapped[int] = mapped_column(Integer, default=0)
    pictures_count: Mapped[int] = mapped_column(Integer, default=0)
    animations_count: Mapped[int] = mapped_column(Integer, default=0)
    total_jobs: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_media_usage_user_date"),
        Index("idx_media_usage_date", "usage_date"),
    )


# ===================================================================
# MEDIA DOWNLOADS - tracking file access
# ===================================================================

class MediaDownload(Base):
    __tablename__ = "media_downloads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_media_downloads_job", "job_id"),
    )


# ===================================================================
# AUTO EDITOR JOBS - professional automatic video editing
# ===================================================================

class AutoEditorJob(Base):
    __tablename__ = "auto_editor_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[AutoEditStatus] = mapped_column(Enum(AutoEditStatus), default=AutoEditStatus.UPLOADING, nullable=False, index=True)
    preset: Mapped[AutoEditPreset] = mapped_column(Enum(AutoEditPreset), default=AutoEditPreset.CUSTOM, nullable=False)

    # Upload
    raw_files: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    raw_file_count: Mapped[int] = mapped_column(Integer, default=0)

    # Analysis
    scene_analysis: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    best_moments: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    cuts_made: Mapped[int] = mapped_column(Integer, default=0)

    # Editing options
    add_transitions: Mapped[bool] = mapped_column(Boolean, default=True)
    add_captions: Mapped[bool] = mapped_column(Boolean, default=True)
    color_grade: Mapped[bool] = mapped_column(Boolean, default=True)
    stabilize: Mapped[bool] = mapped_column(Boolean, default=True)
    ken_burns: Mapped[bool] = mapped_column(Boolean, default=True)
    add_intro_outro: Mapped[bool] = mapped_column(Boolean, default=True)
    adjust_speed: Mapped[bool] = mapped_column(Boolean, default=True)
    background_music: Mapped[bool] = mapped_column(Boolean, default=True)
    watermark_toggle: Mapped[bool] = mapped_column(Boolean, default=True)
    caption_language: Mapped[str] = mapped_column(String(10), default="en")

    # Platform preset
    output_aspect_ratio: Mapped[str] = mapped_column(String(10), default="16:9")
    output_resolution: Mapped[str] = mapped_column(String(10), default="1080p")

    # Manual editor overrides
    trim_start: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trim_end: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speed_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    custom_transition: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    text_overlays: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    stickers: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    voice_over_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Output
    output_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Progress
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    progress_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_auto_editor_jobs_user_status", "user_id", "status"),
        Index("idx_auto_editor_jobs_created", "created_at"),
    )
