"""
Professional AI - Module Access Service
Handles module access checks, grants, and revokes based on subscription plan and manual grants.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.user import User
from app.models.subscription import Subscription
from app.models.module_access import UserModuleAccess
from app.services.unlimited_mode import subscription_access


class ModuleAccessService:
    """
    Determines which modules a user can access.
    
    Free users: Chat + Code Generation (with daily credits)
    Paid users (PRO/MAX/BUSINESS/ENTERPRISE/TRIAL): All modules unlocked
    Admin can manually grant/revoke specific modules.
    """

    # Free plan modules
    FREE_MODULES: List[str] = ["chat", "code_generation"]

    # Paid plan modules (all unlocked for active paid subscriptions)
    PAID_MODULES: List[str] = [
        "chat",
        "code_generation",
        "prompt_forge",
        "image_generation",
        "video_generation",
        "voice_audio",
        "document_analysis",
        "security_analysis",
        "advanced_coding",
        "auto_editor",
        "media_studio",
    ]

    # Module metadata for frontend display
    MODULE_METADATA: Dict[str, Dict[str, Any]] = {
        "chat": {
            "name": "Chat",
            "description": "AI chat with multilingual support in 40+ languages",
            "icon": "MessageSquare",
            "color": "from-blue-500 to-cyan-500",
            "href": "/chat?mode=chat",
            "free": True,
            "price": "Free (daily credits)",
        },
        "code_generation": {
            "name": "Code Generation",
            "description": "Generate production-ready code in 35+ programming languages",
            "icon": "Code2",
            "color": "from-green-500 to-emerald-500",
            "href": "/chat?mode=code",
            "free": True,
            "price": "Free (daily credits)",
        },
        "prompt_forge": {
            "name": "Prompt Forge",
            "description": "Generate unblockable, optimized prompts for any AI model",
            "icon": "Wand2",
            "color": "from-amber-500 to-orange-500",
            "href": "/prompt-forge",
            "free": False,
            "price": "$19.99/mo (PRO)",
        },
        "image_generation": {
            "name": "Image Generation",
            "description": "Create stunning AI images with Flux, SDXL, and 8K quality",
            "icon": "Image",
            "color": "from-pink-500 to-rose-500",
            "href": "/media?mode=image",
            "free": False,
            "price": "$19.99/mo (PRO)",
        },
        "video_generation": {
            "name": "Video Generation",
            "description": "Generate AI videos with Kling, Runway, Luma, and Pika engines",
            "icon": "Video",
            "color": "from-red-500 to-orange-500",
            "href": "/media?mode=video",
            "free": False,
            "price": "$19.99/mo (PRO)",
        },
        "voice_audio": {
            "name": "Voice/Audio",
            "description": "Text-to-speech, voice cloning, and natural voice conversations",
            "icon": "Mic",
            "color": "from-indigo-500 to-blue-500",
            "href": "/media?mode=voice",
            "free": False,
            "price": "$19.99/mo (PRO)",
        },
        "document_analysis": {
            "name": "Document Analysis",
            "description": "Upload PDFs, docs, and get AI-powered analysis and insights",
            "icon": "FileText",
            "color": "from-purple-500 to-violet-500",
            "href": "/media?mode=documents",
            "free": False,
            "price": "$19.99/mo (PRO)",
        },
        "security_analysis": {
            "name": "Security Analysis",
            "description": "Scan code for vulnerabilities and get OWASP defense strategies",
            "icon": "Shield",
            "color": "from-emerald-500 to-teal-500",
            "href": "/chat?mode=security",
            "free": False,
            "price": "$19.99/mo (PRO)",
        },
        "advanced_coding": {
            "name": "Advanced Coding",
            "description": "Bug fixing, refactoring, and advanced code generation with AI",
            "icon": "Terminal",
            "color": "from-sky-500 to-blue-600",
            "href": "/chat?mode=code",
            "free": False,
            "price": "$19.99/mo (PRO)",
        },
        "auto_editor": {
            "name": "Auto Video Editor",
            "description": "AI-powered video editing with presets, transitions, and auto-captions",
            "icon": "Clapperboard",
            "color": "from-fuchsia-500 to-pink-600",
            "href": "/media?mode=editor",
            "free": False,
            "price": "$19.99/mo (PRO)",
        },
        "media_studio": {
            "name": "Media Studio",
            "description": "Full AI media studio: video, image, animation, and voice-over",
            "icon": "Sparkles",
            "color": "from-violet-500 to-purple-600",
            "href": "/media",
            "free": False,
            "price": "$19.99/mo (PRO)",
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_module_access(self, user_id: str) -> List[UserModuleAccess]:
        """Get all module access records for a user."""
        result = await self.db.execute(
            select(UserModuleAccess).where(UserModuleAccess.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_user_accessible_modules(self, user_id: str, subscription: Optional[Subscription] = None, user_email: Optional[str] = None) -> List[str]:
        """
        Get list of module IDs the user has access to.
        Combines subscription-based access with manual grants.
        Owner/admin always gets all modules for free.
        """
        if settings.is_owner_email(user_email):
            return sorted(list(set(self.FREE_MODULES + self.PAID_MODULES)))

        if not subscription:
            sub_result = await self.db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscription = sub_result.scalar_one_or_none()

        plan = subscription.plan if subscription else "free"
        status = subscription.status if subscription else "free"
        decision = subscription_access.check_access(user_id=user_id, plan=plan, status=status, user_email=user_email)

        accessible = set()

        if decision.unlimited:
            # Paid users get all modules
            accessible.update(self.PAID_MODULES)
        else:
            # Free users get only free modules
            accessible.update(self.FREE_MODULES)

        # Add manually granted modules from database
        result = await self.db.execute(
            select(UserModuleAccess).where(
                and_(
                    UserModuleAccess.user_id == user_id,
                    UserModuleAccess.is_active == True,
                    UserModuleAccess.expires_at == None,
                )
            )
        )
        manual_grants = result.scalars().all()
        for grant in manual_grants:
            accessible.add(grant.module_id)

        return sorted(list(accessible))

    async def check_module_access(self, user_id: str, module_id: str, user_email: Optional[str] = None) -> bool:
        """Check if a user has access to a specific module."""
        accessible = await self.get_user_accessible_modules(user_id, user_email=user_email)
        return module_id in accessible

    async def grant_module(self, user_id: str, module_id: str, module_name: str, granted_by: Optional[str] = None, expires_at: Optional[datetime] = None) -> UserModuleAccess:
        """Manually grant a module to a user."""
        result = await self.db.execute(
            select(UserModuleAccess).where(
                and_(
                    UserModuleAccess.user_id == user_id,
                    UserModuleAccess.module_id == module_id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.is_active = True
            existing.expires_at = expires_at
            existing.granted_at = datetime.now(timezone.utc)
            existing.granted_by = granted_by
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        new_grant = UserModuleAccess(
            user_id=user_id,
            module_id=module_id,
            module_name=module_name,
            is_active=True,
            granted_by=granted_by,
            expires_at=expires_at,
        )
        self.db.add(new_grant)
        await self.db.commit()
        await self.db.refresh(new_grant)
        return new_grant

    async def revoke_module(self, user_id: str, module_id: str) -> bool:
        """Revoke a module from a user."""
        result = await self.db.execute(
            select(UserModuleAccess).where(
                and_(
                    UserModuleAccess.user_id == user_id,
                    UserModuleAccess.module_id == module_id,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if not existing:
            return False

        existing.is_active = False
        existing.expires_at = datetime.now(timezone.utc)
        await self.db.commit()
        return True

    async def get_all_modules_with_access(self, user_id: str, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all modules with access status for a user."""
        accessible = await self.get_user_accessible_modules(user_id, user_email=user_email)
        modules = []

        for module_id, meta in self.MODULE_METADATA.items():
            modules.append({
                "id": module_id,
                "name": meta["name"],
                "description": meta["description"],
                "icon": meta["icon"],
                "color": meta["color"],
                "href": meta["href"],
                "free": meta["free"],
                "price": meta["price"],
                "has_access": module_id in accessible,
            })

        return modules
