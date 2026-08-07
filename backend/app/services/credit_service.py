"""
Professional AI - Credit Service
Handles credit consumption, billing cycles, free/pro plans, and Redis caching.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, func, and_, or_
from datetime import datetime, timedelta
from typing import Optional, Tuple
import redis.asyncio as redis
import json
import logging
from app.models.credit import Credit, CreditTransaction
from app.models.usage import UsageLog
from app.models.subscription import Subscription
from app.models.user import User
from app.config import settings
from app.services.unlimited_mode import subscription_access

logger = logging.getLogger(__name__)


class CreditService:
    """Service for managing user credits with PostgreSQL + Redis."""
    
    # Credit costs for different actions
    CREDIT_COSTS = {
        "chat": 1,
        "code_generation": 5,
        "image_generation": 10,
        "voice_message": 2,
        "premium_language": 2,
        "security_tool": 5,
    }
    
    # Free plan daily limits
    FREE_PLAN_LIMITS = {
        "code_generation": 3,  # per day
        "chat": 50,  # per day
    }
    
    # Plan monthly credits
    PRO_PLAN_CREDITS = 2000
    PLAN_CREDITS = {
        "starter": 100,
        "pro": 2000,
        "pro_yearly": 2000,
        "max": 10000,
        "business": 2000,
        "enterprise": 10000,
        "trial": 2000,
    }
    
    # Free plan vault storage limit (MB)
    FREE_PLAN_VAULT_MB = 3
    
    # Free languages
    FREE_LANGUAGES = ["en", "ur", "hi", "bn"]  # English, Urdu, Hindi, Bengali
    
    # Trial period (days)
    TRIAL_DAYS = 3
    
    # Rollover percentage (0 = no rollover, 20 = 20% rollover)
    ROLLOVER_PERCENTAGE = 20
    
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client
    
    async def get_user_credits(self, user_id: str) -> Optional[Credit]:
        """Get user's credit record from database."""
        result = await self.db.execute(
            select(Credit).where(Credit.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_credits_from_cache(self, user_id: str) -> Optional[int]:
        """Get credits from Redis cache for fast reads."""
        try:
            cached = await self.redis.get(f"credits:{user_id}")
            if cached is not None:
                return int(cached)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        return None
    
    async def set_credits_cache(self, user_id: str, balance: int, ttl: int = 300):
        """Set credits in Redis cache (5 min TTL by default)."""
        try:
            await self.redis.setex(f"credits:{user_id}", ttl, str(balance))
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    async def invalidate_credits_cache(self, user_id: str):
        """Invalidate credits cache after updates."""
        try:
            await self.redis.delete(f"credits:{user_id}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
    
    async def initialize_user_credits(self, user_id: str) -> Credit:
        """
        Initialize credits for a new user.
        Free plan gets 0 credits (uses daily limits instead).
        """
        # Check if already exists
        existing = await self.get_user_credits(user_id)
        if existing:
            return existing
        
        credit = Credit(
            user_id=user_id,
            balance=0,
            total_granted=0,
            total_consumed=0,
            rollover_percentage=self.ROLLOVER_PERCENTAGE,
        )
        self.db.add(credit)
        await self.db.flush()
        
        # Cache it
        await self.set_credits_cache(user_id, 0)
        
        return credit
    
    async def get_user_credit_balance(self, user_id: str) -> int:
        """
        Get user's current credit balance.
        Checks cache first, then database.
        """
        # Try cache first
        cached = await self.get_credits_from_cache(user_id)
        if cached is not None:
            return cached
        
        # Get from database
        credit = await self.get_user_credits(user_id)
        if not credit:
            credit = await self.initialize_user_credits(user_id)
        
        # Update cache
        await self.set_credits_cache(user_id, credit.balance)
        
        return credit.balance
    
    async def grant_credits(
        self,
        user_id: str,
        amount: int,
        transaction_type: str = "grant",
        description: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> Credit:
        """
        Grant credits to a user (atomic operation with locking).
        Used for: subscription purchases, admin grants, refunds, rollovers.
        """
        # Use SELECT FOR UPDATE to prevent race conditions
        result = await self.db.execute(
            select(Credit).where(Credit.user_id == user_id).with_for_update()
        )
        credit = result.scalar_one_or_none()
        
        if not credit:
            credit = await self.initialize_user_credits(user_id)
        
        # Update balance
        credit.balance += amount
        credit.total_granted += amount
        
        # Create transaction record
        transaction = CreditTransaction(
            credit_id=credit.id,
            user_id=user_id,
            amount=amount,
            balance_after=credit.balance,
            transaction_type=transaction_type,
            description=description,
            reference_id=reference_id,
        )
        self.db.add(transaction)
        
        # Update cache
        await self.set_credits_cache(user_id, credit.balance)
        
        logger.info(f"Granted {amount} credits to user {user_id}. New balance: {credit.balance}")
        
        return credit
    
    async def consume_credits(
        self,
        user_id: str,
        amount: int,
        action: str,
        description: Optional[str] = None,
        reference_id: Optional[str] = None
    ) -> Tuple[bool, str, int]:
        """
        Consume credits from a user's balance (atomic operation with locking).
        Returns: (success, message, remaining_balance)
        """
        # Use SELECT FOR UPDATE to prevent race conditions
        result = await self.db.execute(
            select(Credit).where(Credit.user_id == user_id).with_for_update()
        )
        credit = result.scalar_one_or_none()
        
        if not credit:
            credit = await self.initialize_user_credits(user_id)
        
        # Check if user has enough credits
        if credit.balance < amount:
            return False, "Insufficient credits", credit.balance
        
        # Deduct credits
        credit.balance -= amount
        credit.total_consumed += amount
        
        # Create transaction record
        transaction = CreditTransaction(
            credit_id=credit.id,
            user_id=user_id,
            amount=-amount,
            balance_after=credit.balance,
            transaction_type="consume",
            action=action,
            description=description,
            reference_id=reference_id,
        )
        self.db.add(transaction)
        
        # Update cache
        await self.set_credits_cache(user_id, credit.balance)
        
        logger.info(f"Consumed {amount} credits from user {user_id} for {action}. Remaining: {credit.balance}")
        
        return True, "Credits consumed", credit.balance
    
    async def check_and_reset_monthly_credits(self, user_id: str, subscription: Subscription) -> bool:
        """
        Check if monthly credits need to be reset.
        Returns True if reset was performed.
        """
        if subscription.plan == "free":
            return False
        
        credit = await self.get_user_credits(user_id)
        if not credit:
            return False
        
        now = datetime.utcnow()
        
        # Check if we've reached the reset date
        if credit.next_reset_at and now >= credit.next_reset_at:
            # Calculate rollover (20% of remaining balance)
            rollover = int(credit.balance * (self.ROLLOVER_PERCENTAGE / 100))
            plan_credits = self.get_plan_credit_allowance(subscription)
            
            # Reset credits
            credit.balance = plan_credits + rollover
            credit.total_granted += plan_credits + rollover
            credit.last_reset_at = now
            credit.next_reset_at = now + timedelta(days=30)
            
            # Create reset transaction
            transaction = CreditTransaction(
                credit_id=credit.id,
                user_id=user_id,
                amount=plan_credits + rollover,
                balance_after=credit.balance,
                transaction_type="reset",
                description=f"Monthly credit reset (rollover: {rollover})",
            )
            self.db.add(transaction)
            
            # Flush changes to database
            await self.db.flush()
            
            # Update cache
            await self.set_credits_cache(user_id, credit.balance)
            
            logger.info(f"Reset monthly credits for user {user_id}. New balance: {credit.balance}")
            return True
        
        return False
    
    async def get_credit_info(self, user_id: str, subscription: Subscription) -> dict:
        """
        Get comprehensive credit information for the user.
        """
        credit = await self.get_user_credits(user_id)
        if not credit:
            credit = await self.initialize_user_credits(user_id)
        
        # Check if reset is needed
        await self.check_and_reset_monthly_credits(user_id, subscription)
        
        # Refresh credit object
        await self.db.refresh(credit)
        
        return {
            "balance": credit.balance,
            "total_granted": credit.total_granted,
            "total_consumed": credit.total_consumed,
            "plan": subscription.plan,
            "last_reset_at": credit.last_reset_at.isoformat() if credit.last_reset_at else None,
            "next_reset_at": credit.next_reset_at.isoformat() if credit.next_reset_at else None,
            "rollover_percentage": credit.rollover_percentage,
            "display_text": f"{credit.balance:,} credits ({subscription.plan} plan)",
        }
    
    async def can_use_feature(
        self,
        user_id: str,
        feature: str,
        language: str = "en",
        subscription: Optional[Subscription] = None
    ) -> Tuple[bool, str]:
        """
        Check if user can use a feature based on their plan and credits.
        Returns: (can_use, reason)
        """
        if not subscription:
            result = await self.db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscription = result.scalar_one_or_none()
            if not subscription:
                # Create default free subscription
                subscription = Subscription(user_id=user_id, plan="free")
                self.db.add(subscription)
                await self.db.flush()
        
        # UNLIMITED MODE: Active paid users (PRO/MAX/BUSINESS/ENTERPRISE) get unlimited access
        decision = subscription_access.check_access(
            user_id=str(user_id),
            plan=subscription.plan,
            status=subscription.status,
        )
        if decision.unlimited:
            return True, "OK"  # Unlimited users bypass all limits

        # Free plan checks
        if subscription.plan == "free":
            # Check language restrictions
            if language not in self.FREE_LANGUAGES:
                return False, f"Language '{language}' requires Pro plan. Upgrade to access 30+ premium languages."
            
            # Check daily code generation limit
            if feature == "code_generation":
                from sqlalchemy import cast, Date
                from datetime import date
                
                result = await self.db.execute(
                    select(func.count(UsageLog.id))
                    .where(
                        and_(
                            UsageLog.user_id == user_id,
                            UsageLog.action == "code_generation",
                            func.date(UsageLog.created_at) == date.today()
                        )
                    )
                )
                daily_count = result.scalar_one_or_none() or 0
                
                if daily_count >= self.FREE_PLAN_LIMITS["code_generation"]:
                    return False, f"Free plan limit reached: {self.FREE_PLAN_LIMITS['code_generation']} code generations per day. Upgrade to Pro for unlimited access."
            
            # Check daily chat limit
            if feature == "chat":
                from datetime import date
                
                result = await self.db.execute(
                    select(func.count(UsageLog.id))
                    .where(
                        and_(
                            UsageLog.user_id == user_id,
                            UsageLog.action == "chat",
                            func.date(UsageLog.created_at) == date.today()
                        )
                    )
                )
                daily_count = result.scalar_one_or_none() or 0
                
                if daily_count >= self.FREE_PLAN_LIMITS["chat"]:
                    return False, f"Free plan limit reached: {self.FREE_PLAN_LIMITS['chat']} chat messages per day. Upgrade to Pro for unlimited access."
        
        # Paid plans - check credits
        if self.is_paid_plan(subscription.plan):
            credit_info = await self.get_credit_info(user_id, subscription)
            
            cost = self.CREDIT_COSTS.get(feature, 1)
            if feature == "premium_language":
                cost = self.CREDIT_COSTS["premium_language"]
            
            if credit_info["balance"] < cost:
                return False, f"Insufficient credits. You need {cost} credits but have {credit_info['balance']}. Please upgrade or purchase more credits."
        
        return True, "OK"
    
    async def use_feature(
        self,
        user_id: str,
        feature: str,
        language: str = "en",
        usage_log_id: Optional[str] = None,
        subscription: Optional[Subscription] = None
    ) -> Tuple[bool, str, dict]:
        """
        Use a feature and consume credits if needed.
        Returns: (success, message, credit_info)
        """
        if not subscription:
            result = await self.db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscription = result.scalar_one_or_none()
            if not subscription:
                subscription = Subscription(user_id=user_id, plan="free")
                self.db.add(subscription)
                await self.db.flush()
        
        # Check if user can use the feature
        can_use, reason = await self.can_use_feature(user_id, feature, language, subscription)
        if not can_use:
            return False, reason, {}
        
        # UNLIMITED MODE: Active paid users don't consume credits
        decision = subscription_access.check_access(
            user_id=str(user_id),
            plan=subscription.plan,
            status=subscription.status,
        )
        if decision.unlimited:
            # Log usage but don't consume credits
            usage_log = UsageLog(
                user_id=user_id,
                action=feature,
            )
            self.db.add(usage_log)
            await self.db.flush()
            
            credit_info = await self.get_credit_info(user_id, subscription)
            return True, "Feature used (UNLIMITED plan)", credit_info
        
        # Free plan - no credits consumed, just log usage
        if subscription.plan == "free":
            # Log usage
            usage_log = UsageLog(
                user_id=user_id,
                action=feature,
            )
            self.db.add(usage_log)
            await self.db.flush()
            
            credit_info = await self.get_credit_info(user_id, subscription)
            return True, "Feature used (free plan)", credit_info
        
        # Paid plans - consume credits
        cost = self.CREDIT_COSTS.get(feature, 1)
        if feature == "premium_language":
            cost = self.CREDIT_COSTS["premium_language"]
        
        success, message, remaining = await self.consume_credits(
            user_id=user_id,
            amount=cost,
            action=feature,
            description=f"Used {feature}",
            reference_id=usage_log_id,
        )
        
        if success:
            credit_info = await self.get_credit_info(user_id, subscription)
            plan_allowance = max(1, self.get_plan_credit_allowance(subscription))
            
            # Check if credits are running low (warn at 10% remaining)
            if credit_info["balance"] < (plan_allowance * 0.1):
                message += f" Warning: Only {credit_info['balance']} credits remaining!"
            
            return True, message, credit_info
        else:
            return False, message, {}
    
    async def admin_adjust_credits(
        self,
        admin_id: str,
        user_id: str,
        amount: int,
        reason: str
    ) -> Credit:
        """
        Admin manually adjusts user credits.
        Positive amount = grant, Negative amount = deduct.
        """
        transaction_type = "admin_adjust"
        
        credit = await self.grant_credits(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=f"Admin adjustment: {reason}",
        )
        
        logger.info(f"Admin {admin_id} adjusted credits for user {user_id}: {amount}. Reason: {reason}")
        
        return credit
    
    async def process_refund(
        self,
        user_id: str,
        amount: int,
        revenue_id: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Credit:
        """
        Process refund - reverse credits and return money.
        """
        credit = await self.grant_credits(
            user_id=user_id,
            amount=amount,
            transaction_type="refund",
            description=f"Refund processed: {reason}",
            reference_id=revenue_id,
        )
        
        logger.info(f"Refund processed for user {user_id}: {amount} credits")
        
        return credit

    def is_paid_plan(self, plan: str) -> bool:
        return plan in self.PLAN_CREDITS

    def get_plan_credit_allowance(self, subscription: Subscription) -> int:
        plan = (subscription.plan or "free").lower()
        return self.PLAN_CREDITS.get(plan, 0)
    
    async def get_usage_stats(self, user_id: str, days: int = 30) -> dict:
        """Get usage statistics for the last N days."""
        from datetime import timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            select(
                UsageLog.action,
                func.count(UsageLog.id).label("count"),
                func.sum(UsageLog.tokens_used).label("total_tokens")
            )
            .where(
                and_(
                    UsageLog.user_id == user_id,
                    UsageLog.created_at >= start_date
                )
            )
            .group_by(UsageLog.action)
        )
        
        stats = {}
        for row in result.fetchall():
            stats[row.action] = {
                "count": row.count,
                "total_tokens": row.total_tokens or 0
            }
        
        return stats