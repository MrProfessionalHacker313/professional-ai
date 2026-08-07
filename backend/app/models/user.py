"""
Professional AI - User Model
SQLAlchemy model for users, OAuth accounts, 2FA, passkeys, sessions, and login attempts.
"""

from __future__ import annotations

import sqlalchemy
from sqlalchemy import String, Boolean, DateTime, Text, UUID, ForeignKey, BigInteger, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import uuid
from app.database import Base

if TYPE_CHECKING:
    from app.models.subscription import Subscription
    from app.models.usage import UsageLog
    from app.models.vault import VaultData
    from app.models.support import SupportTicket
    from app.models.credit import Credit
    from app.models.advanced_features import (
        AIMemory, AIAgent, AgentExecution, Image, VoiceRecording,
        Document, Translation, WebSearch, Chatbot, ChatbotConversation,
        ScreenshotCode, CodeExplanation, ModelRouterLog, LanguagePreference,
        HackingSession, AIProject, ScreenshotApp, ThreatAnalysis,
        VoiceCommandSession, MemoryVaultBackup, TaskBatch, AICourse,
        BusinessPlan, GeneratedFile, CompatibilityCheck, DeviceProfile,
        VoiceClone, NewsSubscription, NewsDigest
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    device_fingerprint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45).with_variant(sqlalchemy.dialects.postgresql.INET, "postgresql"),
        nullable=True
    )
    failed_login_attempts: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    two_factor_auth: Mapped[Optional["TwoFactorAuth"]] = relationship("TwoFactorAuth", back_populates="user", uselist=False, cascade="all, delete-orphan")
    passkeys: Mapped[list["Passkey"]] = relationship("Passkey", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    login_attempts: Mapped[list["LoginAttempt"]] = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")
    subscription: Mapped[Optional["Subscription"]] = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    usage_logs: Mapped[list["UsageLog"]] = relationship("UsageLog", back_populates="user", cascade="all, delete-orphan")
    vault_entries: Mapped[list["VaultData"]] = relationship("VaultData", back_populates="user", cascade="all, delete-orphan")
    support_tickets: Mapped[list["SupportTicket"]] = relationship("SupportTicket", back_populates="user", cascade="all, delete-orphan", foreign_keys="SupportTicket.user_id")
    credits: Mapped[Optional["Credit"]] = relationship("Credit", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # Advanced Features Relationships
    memories: Mapped[list["AIMemory"]] = relationship("AIMemory", back_populates="user", cascade="all, delete-orphan")
    agents: Mapped[list["AIAgent"]] = relationship("AIAgent", back_populates="user", cascade="all, delete-orphan")
    agent_executions: Mapped[list["AgentExecution"]] = relationship("AgentExecution", back_populates="user", cascade="all, delete-orphan")
    images: Mapped[list["Image"]] = relationship("Image", back_populates="user", cascade="all, delete-orphan")
    voice_recordings: Mapped[list["VoiceRecording"]] = relationship("VoiceRecording", back_populates="user", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    translations: Mapped[list["Translation"]] = relationship("Translation", back_populates="user", cascade="all, delete-orphan")
    web_searches: Mapped[list["WebSearch"]] = relationship("WebSearch", back_populates="user", cascade="all, delete-orphan")
    chatbots: Mapped[list["Chatbot"]] = relationship("Chatbot", back_populates="user", cascade="all, delete-orphan")
    chatbot_conversations: Mapped[list["ChatbotConversation"]] = relationship("ChatbotConversation", back_populates="user", cascade="all, delete-orphan")
    screenshot_codes: Mapped[list["ScreenshotCode"]] = relationship("ScreenshotCode", back_populates="user", cascade="all, delete-orphan")
    code_explanations: Mapped[list["CodeExplanation"]] = relationship("CodeExplanation", back_populates="user", cascade="all, delete-orphan")
    model_router_logs: Mapped[list["ModelRouterLog"]] = relationship("ModelRouterLog", back_populates="user", cascade="all, delete-orphan")
    language_preferences: Mapped[list["LanguagePreference"]] = relationship("LanguagePreference", back_populates="user", cascade="all, delete-orphan")
    hacking_sessions: Mapped[list["HackingSession"]] = relationship("HackingSession", back_populates="user", cascade="all, delete-orphan")
    ai_projects: Mapped[list["AIProject"]] = relationship("AIProject", back_populates="user", cascade="all, delete-orphan")
    screenshot_apps: Mapped[list["ScreenshotApp"]] = relationship("ScreenshotApp", back_populates="user", cascade="all, delete-orphan")
    threat_analyses: Mapped[list["ThreatAnalysis"]] = relationship("ThreatAnalysis", back_populates="user", cascade="all, delete-orphan")
    voice_command_sessions: Mapped[list["VoiceCommandSession"]] = relationship("VoiceCommandSession", back_populates="user", cascade="all, delete-orphan")
    memory_vault_backups: Mapped[list["MemoryVaultBackup"]] = relationship("MemoryVaultBackup", back_populates="user", cascade="all, delete-orphan")
    task_batches: Mapped[list["TaskBatch"]] = relationship("TaskBatch", back_populates="user", cascade="all, delete-orphan")
    ai_courses: Mapped[list["AICourse"]] = relationship("AICourse", back_populates="user", cascade="all, delete-orphan")
    business_plans: Mapped[list["BusinessPlan"]] = relationship("BusinessPlan", back_populates="user", cascade="all, delete-orphan")
    generated_files: Mapped[list["GeneratedFile"]] = relationship("GeneratedFile", back_populates="user", cascade="all, delete-orphan")
    compatibility_checks: Mapped[list["CompatibilityCheck"]] = relationship("CompatibilityCheck", back_populates="user", cascade="all, delete-orphan")
    device_profiles: Mapped[list["DeviceProfile"]] = relationship("DeviceProfile", back_populates="user", cascade="all, delete-orphan")
    voice_clones: Mapped[list["VoiceClone"]] = relationship("VoiceClone", back_populates="user", cascade="all, delete-orphan")
    news_subscriptions: Mapped[list["NewsSubscription"]] = relationship("NewsSubscription", back_populates="user", cascade="all, delete-orphan")
    news_digests: Mapped[list["NewsDigest"]] = relationship("NewsDigest", back_populates="user", cascade="all, delete-orphan")


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")

    __table_args__ = (
        UniqueConstraint("provider", "provider_account_id"),
    )


class TwoFactorAuth(Base):
    __tablename__ = "two_factor_auth"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    secret: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(20), default="totp")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    backup_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="two_factor_auth")


class Passkey(Base):
    __tablename__ = "passkeys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    credential_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    counter: Mapped[int] = mapped_column(BigInteger, default=0)
    device_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    transports: Mapped[Optional[list]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="passkeys")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    device_fingerprint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45).with_variant(INET, "postgresql"),
        nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45).with_variant(INET, "postgresql"),
        nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="login_attempts")
