"""
Professional AI - Credit System Models
Tracks user credits, transactions, and billing cycles.
"""

from __future__ import annotations

from sqlalchemy import String, Integer, DateTime, Text, UUID, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import uuid
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.usage import UsageLog
    from app.models.revenue import RevenueLog


class Credit(Base):
    __tablename__ = "credits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    total_granted: Mapped[int] = mapped_column(Integer, default=0)
    total_consumed: Mapped[int] = mapped_column(Integer, default=0)
    last_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rollover_percentage: Mapped[int] = mapped_column(Integer, default=0)  # 0 = no rollover, 20 = 20% rollover
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="credits")
    transactions: Mapped[list["CreditTransaction"]] = relationship("CreditTransaction", back_populates="credit", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_credits_user', 'user_id'),
    )


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    credit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("credits.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    credit: Mapped["Credit"] = relationship("Credit", back_populates="transactions")

    __table_args__ = (
        Index('idx_credit_transactions_user_created', 'user_id', 'created_at'),
        Index('idx_credit_transactions_type', 'transaction_type'),
    )