"""
Professional AI - Advanced Features Models
SQLAlchemy models for images, voice, documents, memory, agents, etc.
"""

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, Enum, JSON, Index, UniqueConstraint, UUID
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


# ===================================================================
# ENUMS
# ===================================================================

class MemoryType(str, enum.Enum):
    PREFERENCE = "preference"
    PROJECT = "project"
    CONTEXT = "context"
    SKILL = "skill"


class AgentType(str, enum.Enum):
    RESEARCH = "research"
    WRITING = "writing"
    CODING = "coding"
    ANALYSIS = "analysis"
    CUSTOM = "custom"


class AgentStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImageType(str, enum.Enum):
    GENERATED = "generated"
    UPLOADED = "uploaded"
    ANALYZED = "analyzed"


class RecordingType(str, enum.Enum):
    INPUT = "input"
    OUTPUT = "output"


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    IMAGE = "image"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ===================================================================
# AI MEMORIES
# ===================================================================

class AIMemory(Base):
    __tablename__ = "ai_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    memory_type = Column(Enum(MemoryType), nullable=False)
    key = Column(String(255), nullable=False)
    value_encrypted = Column(Text, nullable=False)
    extra_metadata = Column("metadata", JSON, default={})
    importance_score = Column(Integer, default=5)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "memory_type", "key", name="uq_ai_memories_user_type_key"),
        Index("idx_ai_memories_user", "user_id", "memory_type"),
        Index("idx_ai_memories_importance", "importance_score"),
    )

    user = relationship("User", back_populates="memories")


# ===================================================================
# AI AGENTS
# ===================================================================

class AIAgent(Base):
    __tablename__ = "ai_agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    agent_type = Column(Enum(AgentType), nullable=False)
    system_prompt = Column(Text, nullable=False)
    tools = Column(JSON, default=[])
    config = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    execution_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_ai_agents_user", "user_id"),
        Index("idx_ai_agents_type", "agent_type"),
    )

    user = relationship("User", back_populates="agents")
    executions = relationship("AgentExecution", back_populates="agent", cascade="all, delete-orphan")


# ===================================================================
# AGENT EXECUTIONS
# ===================================================================

class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_description = Column(Text, nullable=False)
    steps = Column(JSON, nullable=False)
    result = Column(Text)
    status = Column(Enum(AgentStatus), default=AgentStatus.RUNNING)
    tokens_used = Column(Integer, default=0)
    execution_time_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_agent_executions_agent", "agent_id", "created_at"),
        Index("idx_agent_executions_user", "user_id", "created_at"),
    )

    agent = relationship("AIAgent", back_populates="executions")
    user = relationship("User", back_populates="agent_executions")


# ===================================================================
# IMAGES
# ===================================================================

class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_type = Column(Enum(ImageType), nullable=False)
    storage_path = Column(Text, nullable=False)
    thumbnail_path = Column(Text)
    prompt = Column(Text)
    negative_prompt = Column(Text)
    model_used = Column(String(100))
    parameters = Column(JSON, default={})
    width = Column(Integer)
    height = Column(Integer)
    file_size_bytes = Column(Integer)
    mime_type = Column(String(50))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_images_user", "user_id", "created_at"),
        Index("idx_images_type", "image_type"),
    )

    user = relationship("User", back_populates="images")
    screenshot_codes = relationship("ScreenshotCode", back_populates="image", cascade="all, delete-orphan")
    screenshot_apps = relationship("ScreenshotApp", back_populates="image", cascade="all, delete-orphan")


# ===================================================================
# VOICE RECORDINGS
# ===================================================================

class VoiceRecording(Base):
    __tablename__ = "voice_recordings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recording_type = Column(Enum(RecordingType), nullable=False)
    storage_path = Column(Text, nullable=False)
    duration_seconds = Column(Integer)
    language = Column(String(10))
    transcription = Column(Text)
    model_used = Column(String(100))
    file_size_bytes = Column(Integer)
    mime_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_voice_recordings_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="voice_recordings")


# ===================================================================
# DOCUMENTS
# ===================================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(Text, nullable=False)
    file_size_bytes = Column(Integer)
    mime_type = Column(String(50))
    page_count = Column(Integer)
    word_count = Column(Integer)
    language_detected = Column(String(10))
    summary = Column(Text)
    extracted_text = Column(Text)
    extra_metadata = Column("metadata", JSON, default={})
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_documents_user", "user_id", "created_at"),
        Index("idx_documents_status", "processing_status"),
    )

    user = relationship("User", back_populates="documents")


# ===================================================================
# TRANSLATIONS
# ===================================================================

class Translation(Base):
    __tablename__ = "translations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    context_type = Column(String(50))
    context_id = Column(UUID(as_uuid=True))
    model_used = Column(String(100))
    confidence_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_translations_user", "user_id", "created_at"),
        Index("idx_translations_languages", "source_language", "target_language"),
    )

    user = relationship("User", back_populates="translations")


# ===================================================================
# WEB SEARCHES
# ===================================================================

class WebSearch(Base):
    __tablename__ = "web_searches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    query = Column(Text, nullable=False)
    search_engine = Column(String(50), nullable=False)
    results = Column(JSON, nullable=False)
    result_count = Column(Integer, default=0)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_web_searches_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="web_searches")


# ===================================================================
# CHATBOTS
# ===================================================================

class Chatbot(Base):
    __tablename__ = "chatbots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    avatar_url = Column(Text)
    system_prompt = Column(Text, nullable=False)
    welcome_message = Column(Text)
    suggested_prompts = Column(JSON, default=[])
    config = Column(JSON, default={})
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    conversation_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_chatbots_user", "user_id"),
        Index("idx_chatbots_public", "is_public", "is_featured"),
    )

    user = relationship("User", back_populates="chatbots")
    conversations = relationship("ChatbotConversation", back_populates="chatbot", cascade="all, delete-orphan")


# ===================================================================
# CHATBOT CONVERSATIONS
# ===================================================================

class ChatbotConversation(Base):
    __tablename__ = "chatbot_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), nullable=False)
    messages = Column(JSON, nullable=False, default=[])
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_chatbot_conversations_chatbot", "chatbot_id", "started_at"),
        Index("idx_chatbot_conversations_user", "user_id", "started_at"),
    )

    chatbot = relationship("Chatbot", back_populates="conversations")
    user = relationship("User", back_populates="chatbot_conversations")


# ===================================================================
# SCREENSHOT TO CODE
# ===================================================================

class ScreenshotCode(Base):
    __tablename__ = "screenshot_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"))
    generated_code = Column(Text, nullable=False)
    framework = Column(String(50))
    language = Column(String(50))
    model_used = Column(String(100))
    accuracy_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_screenshot_codes_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="screenshot_codes")
    image = relationship("Image", back_populates="screenshot_codes")


# ===================================================================
# CODE EXPLANATIONS
# ===================================================================

class CodeExplanation(Base):
    __tablename__ = "code_explanations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    explanation = Column(Text, nullable=False)
    line_by_line = Column(JSON)
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_code_explanations_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="code_explanations")


class LanguagePreference(Base):
    __tablename__ = "language_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    preferred_language = Column(String(10), nullable=False, default="en")
    detected_language = Column(String(10))
    auto_translate = Column(Boolean, default=True)
    translation_model = Column(String(100))
    language_context = Column(JSON, default={})
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_language_prefs_user", "user_id"),
    )

    user = relationship("User", back_populates="language_preferences")


class HackingSession(Base):
    __tablename__ = "hacking_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    attack_type = Column(String(50), nullable=False)
    target_description = Column(Text, nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.RUNNING)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=5)
    steps = Column(JSON, default=[])
    result = Column(Text)
    ai_feedback = Column(JSON, default={})
    risk_level = Column(String(20), default="safe")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_hacking_sessions_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="hacking_sessions")


class AIProject(Base):
    __tablename__ = "ai_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    stack = Column(JSON, nullable=False)
    files = Column(JSON, default={})
    status = Column(String(50), default="building")
    progress_percent = Column(Integer, default=0)
    build_log = Column(Text)
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_ai_projects_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="ai_projects")


class ScreenshotApp(Base):
    __tablename__ = "screenshot_apps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"))
    platform = Column(String(50), nullable=False)
    framework = Column(String(100), nullable=False)
    app_files = Column(JSON, default={})
    app_structure = Column(JSON, default={})
    accuracy_score = Column(Float)
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_screenshot_apps_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="screenshot_apps")
    image = relationship("Image", back_populates="screenshot_apps")


class ThreatAnalysis(Base):
    __tablename__ = "threat_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    analysis_type = Column(String(50), nullable=False)
    target = Column(Text, nullable=False)
    threat_level = Column(String(20))
    threats_found = Column(JSON, default=[])
    recommendations = Column(JSON, default=[])
    confidence_score = Column(Float)
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_threat_analyses_user", "user_id", "created_at"),
        Index("idx_threat_analyses_type", "analysis_type"),
    )

    user = relationship("User", back_populates="threat_analyses")


class VoiceCommandSession(Base):
    __tablename__ = "voice_command_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255), nullable=False)
    commands = Column(JSON, default=[])
    status = Column(String(50), default="active")
    language = Column(String(10))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_voice_command_sessions_user", "user_id", "created_at"),
        Index("idx_voice_command_sessions_session", "session_id"),
    )

    user = relationship("User", back_populates="voice_command_sessions")


class MemoryVaultBackup(Base):
    __tablename__ = "memory_vault_backups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    backup_data = Column(Text, nullable=False)
    encrypted = Column(Boolean, default=True)
    memory_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_memory_vault_backups_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="memory_vault_backups")


class TaskBatch(Base):
    __tablename__ = "task_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tasks = Column(JSON, nullable=False)
    results = Column(JSON, default={})
    status = Column(String(50), default="pending")
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    failed_tasks = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_task_batches_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="task_batches")


class AICourse(Base):
    __tablename__ = "ai_courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String(255), nullable=False)
    difficulty = Column(String(50), nullable=False)
    description = Column(Text)
    course_content = Column(JSON, default={})
    total_lessons = Column(Integer, default=0)
    current_lesson = Column(Integer, default=0)
    progress_percent = Column(Integer, default=0)
    status = Column(String(50), default="created")
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_ai_courses_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="ai_courses")


class BusinessPlan(Base):
    __tablename__ = "business_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    industry = Column(String(100), nullable=False)
    budget = Column(String(100))
    timeline = Column(String(100))
    plan_content = Column(JSON, default={})
    marketing_strategy = Column(JSON, default={})
    status = Column(String(50), default="draft")
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_business_plans_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="business_plans")


class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_format = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text)
    file_content = Column(Text)
    file_size_bytes = Column(Integer)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_generated_files_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="generated_files")


class CompatibilityCheck(Base):
    __tablename__ = "compatibility_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    code = Column(Text, nullable=False)
    target_platform = Column(String(100), nullable=False)
    compatible = Column(Boolean, default=False)
    issues = Column(JSON, default=[])
    suggestions = Column(JSON, default=[])
    confidence_score = Column(Float)
    model_used = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_compatibility_checks_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="compatibility_checks")


class DeviceProfile(Base):
    __tablename__ = "device_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_name = Column(String(255), nullable=False)
    device_type = Column(String(100))
    os = Column(String(100))
    cpu_cores = Column(Integer)
    ram_gb = Column(Integer)
    gpu = Column(String(255))
    preferred_model = Column(String(100))
    capabilities = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_device_profiles_user", "user_id"),
    )

    user = relationship("User", back_populates="device_profiles")


class VoiceClone(Base):
    __tablename__ = "voice_clones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    voice_name = Column(String(255), nullable=False)
    audio_sample_path = Column(Text, nullable=False)
    consent = Column(Boolean, default=False)
    status = Column(String(50), default="processing")
    model_used = Column(String(100))
    accuracy_score = Column(Float)
    voice_metadata = Column("extra_metadata", JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_voice_clones_user", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="voice_clones")


class NewsSubscription(Base):
    __tablename__ = "news_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topics = Column(JSON, nullable=False)
    frequency = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    last_delivered_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_news_subscriptions_user", "user_id"),
    )

    user = relationship("User", back_populates="news_subscriptions")


class NewsDigest(Base):
    __tablename__ = "news_digests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("news_subscriptions.id", ondelete="SET NULL"))
    topics = Column(JSON, nullable=False)
    articles = Column(JSON, default={})
    summary = Column(Text)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_news_digests_user", "user_id", "generated_at"),
    )

    user = relationship("User", back_populates="news_digests")


# ===================================================================
# MODEL ROUTER LOGS
# ===================================================================

class ModelRouterLog(Base):
    __tablename__ = "model_router_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_type = Column(String(50), nullable=False)
    selected_model = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    reason = Column(String(255))
    execution_time_ms = Column(Integer)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_model_router_logs_user", "user_id", "created_at"),
        Index("idx_model_router_logs_model", "selected_model", "created_at"),
    )

    user = relationship("User", back_populates="model_router_logs")