"""
Professional AI - Credit Routes
API endpoints for credit management, usage tracking, and billing.
SECURITY HARDENED: Admin authorization, input validation, audit logging.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import redis.asyncio as redis
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.services.credit_service import CreditService
from app.services.auth_service import get_current_user, get_current_admin
from app.services.unlimited_mode import subscription_access
from app.config import settings
from pydantic import BaseModel, Field

router = APIRouter(prefix="/credits", tags=["credits"])


class CreditInfoResponse(BaseModel):
    balance: int
    total_granted: int
    total_consumed: int
    plan: str
    last_reset_at: Optional[str]
    next_reset_at: Optional[str]
    rollover_percentage: int
    display_text: str

class UseFeatureRequest(BaseModel):
    feature: str = Field(..., description="Feature to use: chat, code_generation, image_generation, voice_message, security_tool")
    language: str = Field(default="en", description="Language code")
    usage_log_id: Optional[str] = Field(None, description="Reference to usage log")

class UseFeatureResponse(BaseModel):
    success: bool
    message: str
    credit_info: Optional[CreditInfoResponse]
    can_retry: bool = Field(..., description="Whether user can try again after this response")

class AdminAdjustRequest(BaseModel):
    user_id: str = Field(..., description="User ID to adjust")
    amount: int = Field(..., description="Amount to add (positive) or deduct (negative)")
    reason: str = Field(..., description="Reason for adjustment")

class AdminAdjustResponse(BaseModel):
    success: bool
    message: str
    new_balance: int
    user_email: str

class UsageStatsResponse(BaseModel):
    stats: dict
    period_days: int

class PlanLimitsResponse(BaseModel):
    plan: str
    daily_code_generation: int
    daily_chat: int
    monthly_credits: int
    vault_storage_mb: int
    free_languages: list[str]
    credit_costs: dict
    features: list[str]


async def get_redis() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)


@router.get("/info", response_model=CreditInfoResponse)
async def get_credit_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get current user's credit information."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        subscription = Subscription(user_id=current_user.id, plan="free")
        db.add(subscription)
        await db.flush()

    credit_service = CreditService(db, redis_client)
    credit_info = await credit_service.get_credit_info(str(current_user.id), subscription)

    # UNLIMITED MODE: Active paid plans show UNLIMITED
    # Owner/admin bypass: owner gets unlimited access for free
    decision = subscription_access.check_access(
        user_id=str(current_user.id),
        plan=subscription.plan,
        status=subscription.status,
        user_email=current_user.email,
    )
    if settings.is_owner_email(current_user.email):
        display_text = "OWNER - UNLIMITED (all paid features free)"
    elif decision.unlimited:
        display_text = f"UNLIMITED ({subscription.plan} plan) - No limits"
    elif subscription.plan == "free":
        display_text = "Free Plan - Daily limits apply"
    else:
        display_text = f"Credits left: {credit_info['balance']:,} / {CreditService.PRO_PLAN_CREDITS:,}"

    # TEST CHANGE
    return CreditInfoResponse(
        balance=0,
        total_granted=0,
        total_consumed=0,
        plan=subscription.plan,
        last_reset_at=None,
        next_reset_at=None,
        rollover_percentage=0,
        display_text="TEST CHANGE",
    )


@router.post("/use", response_model=UseFeatureResponse)
async def use_feature(
    request: UseFeatureRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Use a feature and consume credits if needed."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        subscription = Subscription(user_id=current_user.id, plan="free")
        db.add(subscription)
        await db.flush()

    credit_service = CreditService(db, redis_client)
    success, message, credit_info = await credit_service.use_feature(
        user_id=str(current_user.id),
        feature=request.feature,
        language=request.language,
        usage_log_id=request.usage_log_id,
        subscription=subscription,
        user_email=current_user.email,
    )

    can_retry = False
    if not success:
        if "credits" in message.lower() or "upgrade" in message.lower():
            can_retry = True

    credit_response = None
    if credit_info:
        if subscription.plan == "free":
            display_text = "Free Plan - Daily limits apply"
        else:
            display_text = f"Credits left: {credit_info['balance']:,} / {CreditService.PRO_PLAN_CREDITS:,}"

        credit_info["display_text"] = display_text

        credit_response = CreditInfoResponse(
            **credit_info,
        )

    return UseFeatureResponse(
        success=success,
        message=message,
        credit_info=credit_response,
        can_retry=can_retry
    )


@router.get("/limits", response_model=PlanLimitsResponse)
async def get_plan_limits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current plan limits and credit costs."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        subscription = Subscription(user_id=current_user.id, plan="free")
        db.add(subscription)
        await db.flush()

    plan = subscription.plan

    # UNLIMITED MODE: Active paid plans get unlimited limits
    decision = subscription_access.check_access(
        user_id=str(current_user.id),
        plan=plan,
        status=subscription.status,
        user_email=current_user.email,
    )
    is_unlimited = decision.unlimited

    features = {
        "free": ["chat", "code_generation", "vault"],
        "pro": ["chat", "code_generation", "image_generation", "voice_message", "security_tools", "premium_languages", "unlimited_vault"]
    }
    feature_list = features.get(plan, features["pro"])

    if is_unlimited:
        daily_code = -1  # unlimited
        daily_chat = -1  # unlimited
        monthly_credits = -1  # unlimited (no credit consumption)
        vault_mb = -1  # unlimited
    elif plan == "free":
        daily_code = CreditService.FREE_PLAN_LIMITS["code_generation"]
        daily_chat = CreditService.FREE_PLAN_LIMITS["chat"]
        monthly_credits = 0
        vault_mb = CreditService.FREE_PLAN_VAULT_MB
    else:
        # Paid but canceled/downgraded/expired -> limits apply
        daily_code = CreditService.FREE_PLAN_LIMITS["code_generation"]
        daily_chat = CreditService.FREE_PLAN_LIMITS["chat"]
        monthly_credits = CreditService.PRO_PLAN_CREDITS if plan in ["pro", "pro_yearly", "trial"] else 0
        vault_mb = CreditService.FREE_PLAN_VAULT_MB

    return PlanLimitsResponse(
        plan=plan,
        daily_code_generation=daily_code,
        daily_chat=daily_chat,
        monthly_credits=monthly_credits,
        vault_storage_mb=vault_mb,
        free_languages=CreditService.FREE_LANGUAGES,
        credit_costs=CreditService.CREDIT_COSTS,
        features=feature_list
    )


@router.get("/stats", response_model=UsageStatsResponse)
async def get_usage_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get usage statistics for the last N days."""
    credit_service = CreditService(db, redis_client)
    stats = await credit_service.get_usage_stats(str(current_user.id), days)

    return UsageStatsResponse(
        stats=stats,
        period_days=days
    )


@router.post("/admin/adjust", response_model=AdminAdjustResponse)
async def admin_adjust_credits(
    request: AdminAdjustRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Admin endpoint to manually adjust user credits."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can adjust credits"
        )

    result = await db.execute(
        select(User).where(User.id == request.user_id)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    credit_service = CreditService(db, redis_client)
    credit = await credit_service.admin_adjust_credits(
        admin_id=str(current_user.id),
        user_id=request.user_id,
        amount=request.amount,
        reason=request.reason
    )

    await db.commit()

    return AdminAdjustResponse(
        success=True,
        message=f"Successfully adjusted {request.amount} credits for {target_user.email}",
        new_balance=credit.balance,
        user_email=target_user.email
    )


@router.post("/admin/grant-trial")
async def grant_trial(
    request: Request,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Admin endpoint to grant 3-day free trial to a user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can grant trials"
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    sub_result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = sub_result.scalar_one_or_none()

    if not subscription:
        subscription = Subscription(user_id=user_id)
        db.add(subscription)

    now = datetime.utcnow()
    subscription.plan = "trial"
    subscription.trial_start_at = now
    subscription.trial_end_at = now + timedelta(days=CreditService.TRIAL_DAYS)
    subscription.status = "active"

    credit_service = CreditService(db, redis_client)
    credit = await credit_service.grant_credits(
        user_id=str(user_id),
        amount=CreditService.PRO_PLAN_CREDITS,
        transaction_type="grant",
        description=f"3-day free trial ({CreditService.TRIAL_DAYS} days)"
    )

    credit.last_reset_at = now
    credit.next_reset_at = now + timedelta(days=30)

    await db.commit()

    trial_end = subscription.trial_end_at
    return {
        "success": True,
        "message": f"Granted 3-day trial to {target_user.email}",
        "trial_end": trial_end.isoformat() if trial_end is not None else None,
        "credits_granted": CreditService.PRO_PLAN_CREDITS
    }


@router.post("/admin/revoke-trial")
async def revoke_trial(
    request: Request,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """Admin endpoint to revoke trial and downgrade to free plan."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can revoke trials"
        )

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    target_user = result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    sub_result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = sub_result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )

    subscription.plan = "free"
    subscription.trial_start_at = None
    subscription.trial_end_at = None
    subscription.status = "active"

    await db.commit()

    return {
        "success": True,
        "message": f"Revoked trial for {target_user.email}. Downgraded to free plan."
    }
