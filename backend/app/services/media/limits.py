"""
Professional AI - Media Engine Limits Service
Enforces plan-specific daily limits:
- FREE: 1 video/day + 10 pictures/day + 3 animations/day
- STARTER: 5 videos/day + 20 pictures/day + 5 animations/day, 1080p
- PRO: 20 videos/day + 50 pictures/day + 20 animations/day, 8K + auto-edit
- MAX: unlimited media, 8K priority
- BUSINESS: shared team pool (same as PRO per-user limits)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Tuple
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.media_engine import MediaUsage
from app.services.unlimited_mode import subscription_access


class MediaLimitsService:
    """Enforces daily media generation limits based on subscription plan."""

    PLAN_LIMITS: Dict[str, Dict[str, Any]] = {
        "free": {
            "video": 1,
            "picture": 10,
            "animation": 3,
            "auto_edit": 0,
            "max_duration": 30,
            "resolution": "720p",
        },
        "starter": {
            "video": 5,
            "picture": 20,
            "animation": 5,
            "auto_edit": 0,
            "max_duration": 120,
            "resolution": "1080p",
        },
        "pro": {
            "video": 20,
            "picture": 50,
            "animation": 20,
            "auto_edit": 10,
            "max_duration": 600,
            "resolution": "8k",
        },
        "pro_yearly": {
            "video": 20,
            "picture": 50,
            "animation": 20,
            "auto_edit": 10,
            "max_duration": 600,
            "resolution": "8k",
        },
        "max": {
            "video": -1,
            "picture": -1,
            "animation": -1,
            "auto_edit": -1,
            "max_duration": 600,
            "resolution": "8k",
        },
        "business": {
            "video": 20,
            "picture": 50,
            "animation": 20,
            "auto_edit": 10,
            "max_duration": 600,
            "resolution": "8k",
        },
        "enterprise": {
            "video": -1,
            "picture": -1,
            "animation": -1,
            "auto_edit": -1,
            "max_duration": 600,
            "resolution": "8k",
        },
    }

    # Free durations (seconds)
    FREE_DURATIONS = [int(d) for d in settings.MEDIA_FREE_DURATIONS.split(",") if d.strip()]
    # Paid durations (seconds)
    PAID_DURATIONS = [int(d) for d in settings.MEDIA_PAID_DURATIONS.split(",") if d.strip()]

    # MAX/ENTERPRISE plans get unlimited
    UNLIMITED_PLANS = {"max", "enterprise"}

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_limit(
        self,
        user_id: str,
        media_type: str,
        plan: str = "free",
        status: str = "active",
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if the user can generate more media of the given type today.
        Returns (allowed, info).
        """
        # Check unlimited mode first
        decision = subscription_access.check_access(
            user_id=user_id,
            plan=plan,
            status=status,
        )
        if decision.unlimited:
            return True, {
                "allowed": True,
                "unlimited": True,
                "plan": plan,
                "message": "Unlimited media generation",
            }

        # MAX/ENTERPRISE plans get unlimited media
        if plan.lower() in self.UNLIMITED_PLANS and status == "active":
            return True, {
                "allowed": True,
                "unlimited": True,
                "plan": plan,
                "message": "Unlimited media generation (MAX plan)",
            }

        plan_limits = self.PLAN_LIMITS.get(plan.lower(), self.PLAN_LIMITS["free"])
        limit = plan_limits.get(media_type, 0)

        if limit == -1:
            return True, {
                "allowed": True,
                "unlimited": True,
                "plan": plan,
                "message": "Unlimited media generation",
            }

        # Get today's usage
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        usage = await self._get_or_create_usage(user_id, today)

        if media_type == "video":
            used = usage.videos_count
        elif media_type == "picture":
            used = usage.pictures_count
        elif media_type == "animation":
            used = usage.animations_count
        else:
            used = 0

        remaining = max(0, limit - used)

        if used >= limit:
            return False, {
                "allowed": False,
                "unlimited": False,
                "plan": plan,
                "limit": limit,
                "used": used,
                "remaining": 0,
                "message": f"Daily {media_type} limit reached ({limit}/{limit}). Upgrade to PRO for more.",
            }

        return True, {
            "allowed": True,
            "unlimited": False,
            "plan": plan,
            "limit": limit,
            "used": used,
            "remaining": remaining,
            "message": f"{remaining} {media_type}(s) remaining today",
        }

    async def increment_usage(
        self,
        user_id: str,
        media_type: str,
    ) -> None:
        """Increment the user's daily usage counter for a media type."""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        usage = await self._get_or_create_usage(user_id, today)

        if media_type == "video":
            usage.videos_count += 1
        elif media_type == "picture":
            usage.pictures_count += 1
        elif media_type == "animation":
            usage.animations_count += 1

        usage.total_jobs += 1
        await self.db.flush()

    async def _get_or_create_usage(self, user_id: str, date: datetime) -> MediaUsage:
        """Get or create the usage record for a user on a given date."""
        result = await self.db.execute(
            select(MediaUsage).where(
                MediaUsage.user_id == user_id,
                MediaUsage.usage_date == date,
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            usage = MediaUsage(
                user_id=user_id,
                usage_date=date,
            )
            self.db.add(usage)
            await self.db.flush()

        return usage

    async def increment_auto_edit_usage(self, user_id: str) -> None:
        """Increment the user's daily auto-edit counter."""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        usage = await self._get_or_create_usage(user_id, today)
        usage.auto_edits_count = (usage.auto_edits_count or 0) + 1
        usage.total_jobs = (usage.total_jobs or 0) + 1
        await self.db.flush()

    async def get_usage_summary(self, user_id: str) -> Dict[str, Any]:
        """Get the user's current daily usage summary."""
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        usage = await self._get_or_create_usage(user_id, today)

        return {
            "date": today.isoformat(),
            "videos_used": usage.videos_count,
            "pictures_used": usage.pictures_count,
            "animations_used": usage.animations_count,
            "total_jobs": usage.total_jobs,
        }

    def get_available_durations(self, plan: str, status: str = "active") -> Dict[str, Any]:
        """Get available durations for the user's plan."""
        if plan.lower() in self.UNLIMITED_PLANS and status == "active":
            return {
                "durations": self.PAID_DURATIONS,
                "plan": plan,
                "unlimited": True,
            }
        if plan == "free":
            return {
                "durations": self.FREE_DURATIONS,
                "plan": "free",
            }
        if status == "active":
            return {
                "durations": self.PAID_DURATIONS,
                "plan": plan,
            }
        return {
            "durations": self.FREE_DURATIONS,
            "plan": "free",
        }

    def validate_duration(self, duration: int, plan: str, status: str = "active") -> bool:
        """Check if a duration is allowed for the user's plan."""
        available = self.get_available_durations(plan, status)
        return duration in available["durations"]

    def get_plan_info(self, plan: str) -> Dict[str, Any]:
        """Get plan limits and features info."""
        return self.PLAN_LIMITS.get(plan.lower(), self.PLAN_LIMITS["free"])