"""
Professional AI - Media Engine Models
SQLAlchemy models for videos, pictures, posters, animations, voice clones,
storyboard scenes, subtitle verification, and media usage tracking.
"""

from datetime import datetime
import uuid
import enum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Enum, JSON, Index, UniqueConstraint, UUID
)
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(Enum(MediaType), nullable=False)
    status = Column(Enum(MediaStatus), default=MediaStatus.QUEUED, nullable=False, index=True)

    # User input
    topic = Column(Text, nullable=False)
    script = Column(Text, nullable=True)
    scenes_text = Column(Text, nullable=True)          # raw scene descriptions from user
    voice_style = Column(Enum(VoiceStyle), default=VoiceStyle.ADULT_FEMALE)
    voice_prompt = Column(Text, nullable=True)          # e.g. "young girl voice, sweet, Urdu"
    language = Column(String(10), default="en")
    duration_seconds = Column(Integer, default=15)
    resolution = Column(Enum(MediaResolution), default=MediaResolution.K8)
    format = Column(String(10), default="mp4")          # mp4, png, gif, webp, mov
    aspect_ratio = Column(String(10), default="16:9")
    quality_slider = Column(String(10), default="8k")
    model = Column(String(100), nullable=True)          # engine used (fal, kling, runway, animatediff)
    negative_prompt = Column(Text, nullable=True)

    # Storyboard (generated)
    storyboard = Column(JSON, nullable=True)            # list of scene objects
    scene_count = Column(Integer, default=0)
    storyboard_status = Column(String(30), nullable=True)

    # Voice over
    voice_over_path = Column(Text, nullable=True)
    voice_over_status = Column(String(30), nullable=True)
    voice_clone_id = Column(UUID(as_uuid=True), nullable=True)
    voice_consent = Column(Boolean, default=False)

    # Subtitles & verification
    subtitles_path = Column(Text, nullable=True)
    subtitle_verify_status = Column(String(30), nullable=True)
    verification_report = Column(JSON, nullable=True)   # word-match check results
    accuracy_verified = Column(Boolean, default=False)

    # Output
    output_path = Column(Text, nullable=True)
    output_url = Column(Text, nullable=True)
    output_resolution = Column(String(10), nullable=True)
    output_size_bytes = Column(Integer, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    duration_render_seconds = Column(Float, nullable=True)
    progress = Column(Float, default=0.0)               # 0-100
    progress_stage = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # Timestamps
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_media_jobs_user_status", "user_id", "status"),
        Index("idx_media_jobs_created", "created_at"),
    )


# ===================================================================
# MEDIA SCENES - individual scene within a media job
# ===================================================================

class MediaScene(Base):
    __tablename__ = "media_scenes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    scene_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)               # fully constructed generation prompt
    duration_seconds = Column(Float, default=5.0)
    status = Column(String(30), default="pending")      # pending, generating, generated, failed, verified
    output_path = Column(Text, nullable=True)
    output_url = Column(Text, nullable=True)
    seed = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    scene_metadata = Column("metadata", JSON, default={})
    generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_media_scenes_job", "job_id", "scene_number"),
    )


# ===================================================================
# SUBTITLE TRACKS - one per language per job
# ===================================================================

class SubtitleTrack(Base):
    __tablename__ = "media_subtitle_tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(10), default="en")
    source_script = Column(Text, nullable=False)         # the exact script text
    subtitle_path = Column(Text, nullable=False)         # .srt or .vtt file
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("job_id", "language", name="uq_media_subtitle_job_lang"),
    )


# ===================================================================
# SUBTITLE VERIFICATION - word-by-word match results
# ===================================================================

class SubtitleVerification(Base):
    __tablename__ = "media_subtitle_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(10), default="en")
    script_words = Column(Integer, nullable=False)
    subtitle_words = Column(Integer, nullable=False)
    matched_words = Column(Integer, nullable=False)
    mismatch_words = Column(Integer, nullable=False)
    match_percentage = Column(Float, nullable=False)
    passed = Column(Boolean, default=False)
    mismatches = Column(JSON, default=[])                # [{script_word, subtitle_word, index}]
    regenerated = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_media_subtitle_verify_job", "job_id"),
    )


# ===================================================================
# VOICE CLONES - user-uploaded voice samples for cloning
# ===================================================================

class MediaVoiceClone(Base):
    __tablename__ = "media_voice_clones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    audio_path = Column(Text, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    language = Column(String(10), default="en")
    consent_given = Column(Boolean, default=False)       # REQUIRED consent checkbox
    status = Column(String(30), default="ready")         # ready, processing, failed
    provider_clone_id = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_media_voice_clones_user", "user_id"),
    )


# ===================================================================
# MEDIA USAGE - daily limits enforcement
# ===================================================================

class MediaUsage(Base):
    __tablename__ = "media_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    usage_date = Column(DateTime(timezone=True), nullable=False, index=True)
    videos_count = Column(Integer, default=0)
    pictures_count = Column(Integer, default=0)
    animations_count = Column(Integer, default=0)
    total_jobs = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_media_usage_user_date"),
        Index("idx_media_usage_date", "usage_date"),
    )


# ===================================================================
# MEDIA DOWNLOADS - tracking file access
# ===================================================================

class MediaDownload(Base):
    __tablename__ = "media_downloads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    downloaded_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_media_downloads_job", "job_id"),
    )


# ===================================================================
# AUTO EDITOR JOBS - professional automatic video editing
# ===================================================================

class AutoEditorJob(Base):
    __tablename__ = "auto_editor_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(AutoEditStatus), default=AutoEditStatus.UPLOADING, nullable=False, index=True)
    preset = Column(Enum(AutoEditPreset), default=AutoEditPreset.CUSTOM, nullable=False)

    # Upload
    raw_files = Column(JSON, nullable=True)            # list of uploaded file paths
    raw_file_count = Column(Integer, default=0)

    # Analysis
    scene_analysis = Column(JSON, nullable=True)       # [{timestamp, score, keep, reason}]
    best_moments = Column(JSON, nullable=True)         # [{start, end, score}]
    cuts_made = Column(Integer, default=0)

    # Editing options
    add_transitions = Column(Boolean, default=True)
    add_captions = Column(Boolean, default=True)
    color_grade = Column(Boolean, default=True)
    stabilize = Column(Boolean, default=True)
    ken_burns = Column(Boolean, default=True)
    add_intro_outro = Column(Boolean, default=True)
    adjust_speed = Column(Boolean, default=True)
    background_music = Column(Boolean, default=True)
    watermark_toggle = Column(Boolean, default=True)
    caption_language = Column(String(10), default="en")

    # Platform preset
    output_aspect_ratio = Column(String(10), default="16:9")
    output_resolution = Column(String(10), default="1080p")

    # Manual editor overrides
    trim_start = Column(Float, nullable=True)
    trim_end = Column(Float, nullable=True)
    speed_factor = Column(Float, nullable=True)
    custom_transition = Column(String(30), nullable=True)
    text_overlays = Column(JSON, nullable=True)        # [{text, x, y, start, end}]
    stickers = Column(JSON, nullable=True)             # [sticker_ids]
    voice_over_path = Column(Text, nullable=True)

    # Output
    output_path = Column(Text, nullable=True)
    output_url = Column(Text, nullable=True)
    output_size_bytes = Column(Integer, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Progress
    progress = Column(Float, default=0.0)
    progress_stage = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_auto_editor_jobs_user_status", "user_id", "status"),
        Index("idx_auto_editor_jobs_created", "created_at"),
    )