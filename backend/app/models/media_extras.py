"""
Professional AI - Extra Media Features Models
Models for thumbnails, memes, watermarks, and other advanced media features.
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

class MemeType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"


class MemeStatus(str, enum.Enum):
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ThumbnailStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


# ===================================================================
# MEDIA MEMES - user-generated memes
# ===================================================================

class MediaMeme(Base):
    __tablename__ = "media_memes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    meme_text = Column(Text, nullable=False)
    meme_type = Column(Enum(MemeType), default=MemeType.IMAGE, nullable=False)
    template_used = Column(String(100), nullable=True)
    status = Column(Enum(MemeStatus), default=MemeStatus.QUEUED, nullable=False, index=True)
    
    # Output
    output_path = Column(Text, nullable=True)
    output_url = Column(Text, nullable=True)
    output_size_bytes = Column(Integer, nullable=True)
    
    # AI suggestions
    suggested_captions = Column(JSON, nullable=True)  # AI-generated funny captions
    humor_score = Column(Float, nullable=True)  # 0-100 how funny AI thinks it is
    
    # Progress
    progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_media_memes_user_status", "user_id", "status"),
        Index("idx_media_memes_created", "created_at"),
    )


# ===================================================================
# MEDIA THUMBNAILS - auto-generated thumbnails for videos
# ===================================================================

class MediaThumbnail(Base):
    __tablename__ = "media_thumbnails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(ThumbnailStatus), default=ThumbnailStatus.PENDING, nullable=False, index=True)
    
    # Thumbnail data
    thumbnail_url = Column(Text, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    thumbnail_text = Column(Text, nullable=True)  # Bold text overlay
    is_selected = Column(Boolean, default=False)  # User's choice
    
    # Generation details
    generation_prompt = Column(Text, nullable=True)
    ai_model_used = Column(String(100), nullable=True)
    
    # Metadata
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    selected_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_media_thumbnails_job", "job_id"),
        Index("idx_media_thumbnails_user", "user_id"),
    )


# ===================================================================
# MEDIA WATERMARKS - branding watermarks for PRO users
# ===================================================================

class MediaWatermark(Base):
    __tablename__ = "media_watermarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Watermark content
    watermark_text = Column(String(200), nullable=True)  # User's name/website
    logo_path = Column(Text, nullable=True)  # Eagle logo path
    position = Column(String(20), default="bottom-right")  # Position on video/image
    
    # Settings
    opacity = Column(Float, default=0.7)  # 0-1 transparency
    font_size = Column(Integer, default=24)
    is_active = Column(Boolean, default=True)
    
    # Usage tracking
    total_applied = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_media_watermark_user"),
        Index("idx_media_watermarks_user", "user_id"),
    )


# ===================================================================
# MEDIA TRENDS - trending hooks/captions/hashtags by country
# ===================================================================

class MediaTrend(Base):
    __tablename__ = "media_trends"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_code = Column(String(2), nullable=False, index=True)  # PK, IN, US, UK
    platform = Column(String(20), nullable=False, index=True)  # tiktok, reels, youtube, instagram
    
    # Trend data
    trend_type = Column(String(50), nullable=False)  # hook, caption, hashtag, effect
    content = Column(Text, nullable=False)
    engagement_score = Column(Float, nullable=True)  # 0-100 based on views/likes
    
    # Metadata
    category = Column(String(50), nullable=True)  # comedy, education, lifestyle, etc.
    language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    trend_start_date = Column(DateTime(timezone=True), nullable=True)
    trend_end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_media_trends_country_platform", "country_code", "platform"),
        Index("idx_media_trends_active", "is_active"),
    )


# ===================================================================
# MEDIA BATCH CAMPAIGNS - business batch video generation
# ===================================================================

class MediaBatchCampaign(Base):
    __tablename__ = "media_batch_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Campaign details
    campaign_name = Column(String(200), nullable=False)
    product_description = Column(Text, nullable=False)
    product_media_path = Column(Text, nullable=True)  # Product image/video
    
    # Batch settings
    total_prompts = Column(Integer, default=10)
    completed_prompts = Column(Integer, default=0)
    failed_prompts = Column(Integer, default=0)
    
    # Status
    status = Column(String(30), default="queued", index=True)  # queued, processing, completed, failed
    progress = Column(Float, default=0.0)
    
    # Output
    output_urls = Column(JSON, nullable=True)  # List of generated video URLs
    
    # Timestamps
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_media_batch_campaigns_user", "user_id"),
        Index("idx_media_batch_campaigns_status", "status"),
    )


# ===================================================================
# MEDIA BATCH PROMPTS - individual prompts in a batch campaign
# ===================================================================

class MediaBatchPrompt(Base):
    __tablename__ = "media_batch_prompts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("media_batch_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Prompt details
    prompt_text = Column(Text, nullable=False)
    prompt_number = Column(Integer, nullable=False)  # 1-10
    
    # Job reference
    media_job_id = Column(UUID(as_uuid=True), ForeignKey("media_jobs.id", ondelete="SET NULL"), nullable=True)
    
    # Status
    status = Column(String(30), default="pending", index=True)  # pending, processing, completed, failed
    output_url = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_media_batch_prompts_campaign", "campaign_id", "prompt_number"),
    )