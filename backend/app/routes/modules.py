"""
Professional AI - Module Access Routes
API endpoints for module access, listing, and management.
SECURITY HARDENED: Admin authorization, input validation, audit logging.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.models.module_access import UserModuleAccess
from app.services.module_access_service import ModuleAccessService
from app.services.auth_service import get_current_user, get_current_admin
from pydantic import validator

router = APIRouter(prefix="/api/modules", tags=["Modules"])


class ModuleResponse(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    color: str
    href: str
    free: bool
    price: str
    has_access: bool


class GrantModuleRequest(BaseModel):
    user_id: str = Field(..., description="User ID to grant module to")
    module_id: str = Field(..., description="Module ID to grant")
    module_name: str = Field(..., description="Human-readable module name")
    expires_at: Optional[str] = Field(None, description="ISO datetime when access expires")

    @validator("module_id")
    def validate_module_id(cls, v):
        allowed = {
            "chat", "code_generation", "prompt_forge", "image_generation",
            "video_generation", "voice_audio", "document_analysis",
            "security_analysis", "advanced_coding", "auto_editor", "media_studio"
        }
        if v not in allowed:
            raise ValueError(f"Invalid module_id. Allowed: {sorted(allowed)}")
        return v


class RevokeModuleRequest(BaseModel):
    user_id: str = Field(..., description="User ID to revoke module from")
    module_id: str = Field(..., description="Module ID to revoke")


class GrantRevokeResponse(BaseModel):
    success: bool
    message: str
    module_id: str
    user_email: str


@router.get("/", response_model=List[ModuleResponse])
async def list_modules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all modules with access status for the current user."""
    service = ModuleAccessService(db)
    modules = await service.get_all_modules_with_access(str(current_user.id), user_email=current_user.email)
    return [ModuleResponse(**m) for m in modules]


@router.get("/access/{module_id}")
async def check_module_access(
    module_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if the current user has access to a specific module."""
    service = ModuleAccessService(db)
    has_access = await service.check_module_access(str(current_user.id), module_id, user_email=current_user.email)
    return {
        "module_id": module_id,
        "has_access": has_access,
        "user_id": str(current_user.id),
    }


@router.get("/my-access")
async def get_my_accessible_modules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of module IDs the current user can access."""
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        subscription = Subscription(user_id=current_user.id, plan="free")
        db.add(subscription)
        await db.flush()

    service = ModuleAccessService(db)
    accessible = await service.get_user_accessible_modules(str(current_user.id), subscription, user_email=current_user.email)
    return {
        "user_id": str(current_user.id),
        "plan": subscription.plan,
        "status": subscription.status,
        "accessible_modules": accessible,
    }


@router.post("/admin/grant", response_model=GrantRevokeResponse)
async def admin_grant_module(
    request: Request,
    data: GrantModuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin endpoint to grant a module to a user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can grant modules"
        )

    result = await db.execute(
        select(User).where(User.id == data.user_id)
    )
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    expires_at_dt = None
    if data.expires_at:
        try:
            expires_at_dt = datetime.fromisoformat(data.expires_at.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at datetime format. Use ISO format.")

    service = ModuleAccessService(db)
    grant = await service.grant_module(
        user_id=data.user_id,
        module_id=data.module_id,
        module_name=data.module_name,
        granted_by=str(current_user.id),
        expires_at=expires_at_dt,
    )

    return GrantRevokeResponse(
        success=True,
        message=f"Granted {data.module_id} to {target_user.email}",
        module_id=data.module_id,
        user_email=target_user.email,
    )


@router.post("/admin/revoke", response_model=GrantRevokeResponse)
async def admin_revoke_module(
    request: Request,
    data: RevokeModuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin endpoint to revoke a module from a user."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can revoke modules"
        )

    result = await db.execute(
        select(User).where(User.id == data.user_id)
    )
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    service = ModuleAccessService(db)
    success = await service.revoke_module(data.user_id, data.module_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module grant not found")

    return GrantRevokeResponse(
        success=True,
        message=f"Revoked {data.module_id} from {target_user.email}",
        module_id=data.module_id,
        user_email=target_user.email,
    )


@router.get("/admin/list-grants")
async def admin_list_grants(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    module_id: Optional[str] = Query(None, description="Filter by module ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Admin endpoint to list all module grants."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view module grants"
        )

    query = select(UserModuleAccess)
    if user_id:
        query = query.where(UserModuleAccess.user_id == user_id)
    if module_id:
        query = query.where(UserModuleAccess.module_id == module_id)

    result = await db.execute(query.order_by(UserModuleAccess.created_at.desc()))
    grants = result.scalars().all()

    return {
        "grants": [
            {
                "id": str(g.id),
                "user_id": str(g.user_id),
                "module_id": g.module_id,
                "module_name": g.module_name,
                "is_active": g.is_active,
                "granted_by": str(g.granted_by) if g.granted_by else None,
                "granted_at": g.granted_at.isoformat() if g.granted_at else None,
                "expires_at": g.expires_at.isoformat() if g.expires_at else None,
                "created_at": g.created_at.isoformat() if g.created_at else None,
            }
            for g in grants
        ]
    }
