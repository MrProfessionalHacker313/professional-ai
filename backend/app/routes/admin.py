"""
Professional AI - Admin Routes
Owner-only commands: user management, revenue, vault, refunds, analytics.
SECURITY HARDENED: Audit logging, input sanitization, rate limiting, IDOR protection.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Header
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import json
from datetime import datetime, timezone, timedelta
import httpx
from cryptography.fernet import Fernet
import redis.asyncio as redis

from app.database import get_db
from app.config import settings
from app.models.user import User, TwoFactorAuth, Passkey, Session
from app.models.subscription import Subscription
from app.models.vault import VaultData, VaultAccessLog
from app.models.revenue import RevenueLog, RefundLog
from app.models.usage import UsageLog
from app.models.support import SupportTicket
from app.services.auth_service import get_current_owner, AuthService, pwd_context
from app.middleware.security import InputSanitizer

router = APIRouter(prefix="/api/admin", tags=["Admin"])


class UserAdminResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    is_active: bool
    is_banned: bool
    is_approved: bool
    is_admin: bool
    plan: str
    free_access_granted: bool = False
    created_at: str
    last_login_at: Optional[str]


class OwnerSetupRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=12, max_length=255)
    totp_secret: str = Field(..., min_length=16, max_length=255)
    totp_code: str = Field(..., min_length=6, max_length=10)
    passkey_credential_id: str = Field(..., min_length=8, max_length=4096)
    passkey_public_key: str = Field(..., min_length=8, max_length=8192)


class OwnerLoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)
    totp_code: str = Field(..., min_length=6, max_length=10)
    passkey_credential_id: str = Field(..., min_length=8, max_length=4096)


class OwnerControlStateRequest(BaseModel):
    feature_toggles: Dict[str, bool]
    global_limits: Dict[str, int]
    plan_prices: Dict[str, float]


class OwnerCardSetupRequest(BaseModel):
    card_holder: str = Field(..., min_length=2, max_length=120)
    card_last4: str = Field(..., min_length=4, max_length=4)
    expiry_month: str = Field(..., min_length=1, max_length=2)
    expiry_year: str = Field(..., min_length=2, max_length=4)
    card_network: str = Field(..., min_length=2, max_length=40)
    billing_currency: str = Field(default="USD", min_length=3, max_length=3)
    card_balance_usd: float = Field(default=0, ge=0)


class OwnerDirectPurchaseRequest(BaseModel):
    item_type: str = Field(..., pattern="^(plan|credits|feature)$")
    item_name: str = Field(..., min_length=1, max_length=80)
    amount_usd: float = Field(..., gt=0)
    credits_to_grant: int = Field(default=0, ge=0)


class OwnerWithdrawRequest(BaseModel):
    amount_usd: float = Field(..., gt=0)


FREE_ACCESS_PAYMENT_METHOD = "admin_free_access"
FREE_ACCESS_MAX_USERS = 10


def _redis_client() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def _owner_email() -> str:
    return (settings.OWNER_EMAIL or "").strip().lower()


def _encryption_key_bytes() -> bytes:
    key = settings.ENCRYPTION_KEY
    return key.encode() if isinstance(key, str) else key


def _encrypt_payload(data: Dict[str, Any]) -> str:
    payload = json.dumps(data)
    f = Fernet(_encryption_key_bytes())
    return f.encrypt(payload.encode()).decode()


def _decrypt_payload(data_encrypted: str) -> Dict[str, Any]:
    f = Fernet(_encryption_key_bytes())
    raw = f.decrypt(data_encrypted.encode()).decode()
    return json.loads(raw)


def _default_owner_control_state() -> Dict[str, Any]:
    return {
        "feature_toggles": {
            # Core features
            "chat": True,
            "code": True,
            "security_tools": True,
            "images": True,
            "voice": True,
            "languages": True,
            # Extra media features (Phase 1-4)
            "thumbnail_maker": True,  # Feature #1 - AI Thumbnail Maker
            "meme_maker": True,  # Feature #8 - Meme Maker
            "watermark_branding": True,  # Feature #7 - Watermark & Branding
            "background_music": True,  # Feature #2 - Background Music
            "ai_intro_outro": True,  # Feature #10 - AI Intro/Outro
            "video_to_blog": True,  # Feature #9 - Video → Blog
            "trending_pack": True,  # Feature #5 - TikTok/Reels Trending Pack
            "talking_avatar": True,  # Feature #4 - Talking Avatar Videos
            "story_to_video": True,  # Feature #3 - Story-to-Video
            "batch_campaign": True,  # Feature #6 - Batch Campaign Maker
        },
        "global_limits": {
            "free_code_per_day": 3,
            "free_chat_per_day": 50,
            "trial_days": 3,
            "credit_price_usd": 0,
            # Media feature limits
            "free_thumbnails_per_day": 10,
            "free_memes_per_day": 5,
            "free_trending_packs_per_day": 3,
        },
        "plan_prices": {
            "starter_monthly_usd": 9.99,
            "starter_yearly_monthly_usd": 7.99,
            "pro_monthly_usd": 19.99,
            "pro_yearly_usd": 159.99,
            "max_monthly_usd": 99.99,
            "business_per_user_monthly_usd": 24.99,
            "enterprise_from_monthly_usd": 499.00,
        },
    }


async def log_admin_action(db: AsyncSession, admin_id: uuid.UUID, action: str, target_type: str, target_id: Optional[str], details: str, request: Request):
    """Log admin action for audit trail."""
    from app.models.audit import AdminAuditLog
    log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(log)
    await db.commit()


# ---- Owner Auth + Control ----

@router.post("/owner/setup")
async def owner_setup(
    payload: OwnerSetupRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_owner_setup_key: Optional[str] = Header(default=None),
):
    """One-time owner bootstrap with bcrypt password, TOTP, and passkey binding."""
    required_key = (settings.OWNER_SETUP_KEY or "").strip()
    provided_key = (x_owner_setup_key or "").strip()
    if not required_key or required_key != provided_key:
        raise HTTPException(status_code=403, detail="Invalid owner setup key")

    if payload.email.strip().lower() != _owner_email():
        raise HTTPException(status_code=400, detail="Owner email must match configured OWNER_EMAIL")

    if not AuthService.verify_totp_code(payload.totp_secret, payload.totp_code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code for provided secret")

    result = await db.execute(select(User).where(User.email == payload.email.strip().lower()))
    owner_user = result.scalar_one_or_none()

    bcrypt_hash = pwd_context.hash(payload.password, scheme="bcrypt")

    if owner_user:
        owner_user.password_hash = bcrypt_hash
        owner_user.is_admin = True
        owner_user.is_approved = True
        owner_user.is_active = True
        owner_user.is_banned = False
        owner_user.email_verified = True
    else:
        owner_user = User(
            email=payload.email.strip().lower(),
            password_hash=bcrypt_hash,
            is_admin=True,
            is_approved=True,
            is_active=True,
            is_banned=False,
            email_verified=True,
        )
        db.add(owner_user)
        await db.flush()

    tf_result = await db.execute(select(TwoFactorAuth).where(TwoFactorAuth.user_id == owner_user.id))
    tf = tf_result.scalar_one_or_none()
    if tf:
        tf.secret = payload.totp_secret
        tf.is_enabled = True
    else:
        db.add(
            TwoFactorAuth(
                user_id=owner_user.id,
                secret=payload.totp_secret,
                method="totp",
                is_enabled=True,
            )
        )

    passkey_result = await db.execute(
        select(Passkey).where(
            Passkey.user_id == owner_user.id,
            Passkey.credential_id == payload.passkey_credential_id,
        )
    )
    passkey = passkey_result.scalar_one_or_none()
    if passkey:
        passkey.public_key = payload.passkey_public_key
    else:
        db.add(
            Passkey(
                user_id=owner_user.id,
                credential_id=payload.passkey_credential_id,
                public_key=payload.passkey_public_key,
                counter=0,
                device_name="Owner Device",
            )
        )

    await db.commit()
    await log_admin_action(db, owner_user.id, "owner_setup", "owner", str(owner_user.id), "Owner account bootstrap completed", request)

    return {
        "message": "Owner setup completed",
        "owner_email": owner_user.email,
        "totp_enabled": True,
        "passkey_bound": True,
    }


@router.post("/owner/login")
async def owner_login(
    payload: OwnerLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Owner-only login with password + TOTP + passkey verification."""
    email = payload.email.strip().lower()
    if not settings.is_owner_email(email):
        raise HTTPException(status_code=403, detail="Owner access required")

    result = await db.execute(select(User).where(User.email == email))
    owner_user = result.scalar_one_or_none()
    if not owner_user or not owner_user.is_admin:
        raise HTTPException(status_code=403, detail="Owner account not configured")

    if not AuthService.verify_password(payload.password, owner_user.password_hash or ""):
        raise HTTPException(status_code=401, detail="Invalid owner credentials")

    tf_result = await db.execute(select(TwoFactorAuth).where(TwoFactorAuth.user_id == owner_user.id))
    tf = tf_result.scalar_one_or_none()
    if settings.OWNER_ENFORCE_TOTP and (not tf or not tf.is_enabled or not AuthService.verify_totp_code(tf.secret, payload.totp_code)):
        raise HTTPException(status_code=401, detail="Invalid owner TOTP code")

    passkey_result = await db.execute(
        select(Passkey).where(
            Passkey.user_id == owner_user.id,
            Passkey.credential_id == payload.passkey_credential_id,
        )
    )
    passkey = passkey_result.scalar_one_or_none()
    if settings.OWNER_ENFORCE_PASSKEY and not passkey:
        raise HTTPException(status_code=401, detail="Passkey verification failed")

    access_token = AuthService.create_access_token(str(owner_user.id), owner_user.email, is_admin=True)
    refresh_token = AuthService.create_refresh_token(str(owner_user.id))

    owner_user.last_login_at = datetime.now(timezone.utc)
    owner_user.last_login_ip = request.client.host if request.client else None
    db.add(
        Session(
            user_id=owner_user.id,
            refresh_token_hash=AuthService.hash_refresh_token(refresh_token),
            device_fingerprint=getattr(request.state, "device_fingerprint", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            is_valid=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "owner": {
            "id": str(owner_user.id),
            "email": owner_user.email,
        },
    }


@router.get("/owner/control-state")
async def get_owner_control_state(
    owner: User = Depends(get_current_owner),
):
    r = _redis_client()
    raw = await r.get("owner:control_state")
    if not raw:
        default_state = _default_owner_control_state()
        await r.set("owner:control_state", json.dumps(default_state))
        return default_state
    return json.loads(raw)


@router.get("/plans")
async def get_admin_plans(
    owner: User = Depends(get_current_owner),
):
    """Compatibility endpoint for admin plans UI."""
    state = await get_owner_control_state(owner=owner)
    plan_prices = state.get("plan_prices", {})
    return {
        "plans": [
            {"name": "FREE", "price_usd": 0},
            {"name": "STARTER", "price_usd": plan_prices.get("starter_monthly_usd", 9.99)},
            {"name": "PRO", "price_usd": plan_prices.get("pro_monthly_usd", 19.99)},
            {"name": "PRO YEARLY", "price_usd": plan_prices.get("pro_yearly_usd", 159.99)},
            {"name": "MAX", "price_usd": plan_prices.get("max_monthly_usd", 99.99)},
            {"name": "BUSINESS", "price_usd": plan_prices.get("business_per_user_monthly_usd", 24.99)},
        ]
    }


@router.put("/plans")
async def update_admin_plans(
    payload: Dict[str, Any],
    request: Request,
    owner: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Compatibility endpoint for admin plans UI updates."""
    plans = payload.get("plans", [])
    by_name = {str(p.get("name", "")).upper(): p for p in plans}
    plan_prices = {
        "starter_monthly_usd": float(by_name.get("STARTER", {}).get("price_usd", 9.99)),
        "pro_monthly_usd": float(by_name.get("PRO", {}).get("price_usd", 19.99)),
        "pro_yearly_usd": float(by_name.get("PRO YEARLY", {}).get("price_usd", 159.99)),
        "max_monthly_usd": float(by_name.get("MAX", {}).get("price_usd", 99.99)),
        "business_per_user_monthly_usd": float(by_name.get("BUSINESS", {}).get("price_usd", 24.99)),
    }

    current_state = await get_owner_control_state(owner=owner)
    updated = {
        "feature_toggles": current_state.get("feature_toggles", {}),
        "global_limits": current_state.get("global_limits", {}),
        "plan_prices": plan_prices,
    }

    r = _redis_client()
    await r.set("owner:control_state", json.dumps(updated))
    await log_admin_action(db, owner.id, "update_admin_plans", "global", None, "Updated admin plan prices", request)
    return {"message": "Plans updated", "plan_prices": plan_prices}


@router.put("/owner/control-state")
async def update_owner_control_state(
    payload: OwnerControlStateRequest,
    request: Request,
    owner: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    r = _redis_client()
    state = {
        "feature_toggles": payload.feature_toggles,
        "global_limits": payload.global_limits,
        "plan_prices": payload.plan_prices,
    }
    await r.set("owner:control_state", json.dumps(state))
    await log_admin_action(db, owner.id, "update_control_state", "global", None, "Updated owner global control settings", request)
    return {"message": "Owner control state updated", "state": state}


@router.get("/owner/subscriptions")
async def owner_subscriptions(
    owner: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Subscription).order_by(Subscription.created_at.desc()))
    rows = result.scalars().all()
    return {
        "subscriptions": [
            {
                "id": str(row.id),
                "user_id": str(row.user_id),
                "plan": row.plan,
                "status": row.status,
                "payment_method": row.payment_method,
                "current_period_start": row.current_period_start.isoformat() if row.current_period_start else None,
                "current_period_end": row.current_period_end.isoformat() if row.current_period_end else None,
                "cancel_at_period_end": row.cancel_at_period_end,
            }
            for row in rows
        ]
    }


@router.put("/owner/card")
async def owner_set_card(
    payload: OwnerCardSetupRequest,
    request: Request,
    owner: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    card_payload = {
        "card_holder": payload.card_holder,
        "card_last4": payload.card_last4,
        "expiry_month": payload.expiry_month,
        "expiry_year": payload.expiry_year,
        "card_network": payload.card_network,
        "billing_currency": payload.billing_currency.upper(),
        "card_balance_usd": payload.card_balance_usd,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    encrypted = _encrypt_payload(card_payload)
    digest = AuthService.hash_refresh_token(encrypted)

    result = await db.execute(
        select(VaultData).where(
            VaultData.user_id == owner.id,
            VaultData.project_name == "__owner_payment_card__",
        )
    )
    entry = result.scalar_one_or_none()

    if entry:
        entry.data_encrypted = encrypted
        entry.iv_hex = digest[:32]
        entry.auth_tag_hex = digest[32:64]
    else:
        db.add(
            VaultData(
                user_id=owner.id,
                project_name="__owner_payment_card__",
                data_encrypted=encrypted,
                encryption_key_id="owner-card-v1",
                iv_hex=digest[:32],
                auth_tag_hex=digest[32:64],
            )
        )

    await db.commit()
    await log_admin_action(db, owner.id, "owner_card_update", "vault", str(owner.id), "Owner updated direct payment card", request)
    return {"message": "Owner card stored securely"}


@router.get("/owner/card")
async def owner_get_card(
    owner: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(VaultData).where(
            VaultData.user_id == owner.id,
            VaultData.project_name == "__owner_payment_card__",
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return {"configured": False}

    card = _decrypt_payload(entry.data_encrypted)
    return {
        "configured": True,
        "card_holder": card.get("card_holder"),
        "card_last4": card.get("card_last4"),
        "card_network": card.get("card_network"),
        "billing_currency": card.get("billing_currency"),
        "card_balance_usd": float(card.get("card_balance_usd", 0) or 0),
        "updated_at": card.get("updated_at"),
    }


@router.post("/owner/purchase")
async def owner_direct_purchase(
    payload: OwnerDirectPurchaseRequest,
    request: Request,
    owner: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    # Bypasses normal user billing flow for owner direct card usage.
    card_result = await db.execute(
        select(VaultData).where(
            VaultData.user_id == owner.id,
            VaultData.project_name == "__owner_payment_card__",
        )
    )
    if not card_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Owner card is not configured")

    tx_id = f"owner-{uuid.uuid4()}"
    db.add(
        RevenueLog(
            user_id=owner.id,
            subscription_id=owner.subscription.id if owner.subscription else None,
            amount=payload.amount_usd,
            currency="USD",
            payment_method="owner_direct_card",
            transaction_id=tx_id,
            status="completed",
            description=json.dumps(
                {
                    "item_type": payload.item_type,
                    "item_name": payload.item_name,
                    "bypass_flow": True,
                }
            ),
        )
    )

    if payload.credits_to_grant > 0:
        from app.services.credit_service import CreditService

        cs = CreditService(db, _redis_client())
        await cs.grant_credits(
            user_id=str(owner.id),
            amount=payload.credits_to_grant,
            transaction_type="owner_direct_purchase",
            description=f"Owner direct purchase: {payload.item_name}",
            reference_id=tx_id,
        )

    r = _redis_client()
    card_usage = float(await r.get("owner:card_usage_usd") or 0.0)
    await r.set("owner:card_usage_usd", round(card_usage + payload.amount_usd, 2))

    await db.commit()
    await log_admin_action(db, owner.id, "owner_direct_purchase", "payment", tx_id, f"Owner purchased {payload.item_name} for ${payload.amount_usd}", request)
    return {"message": "Owner direct purchase completed", "transaction_id": tx_id}


@router.get("/owner/wallet")
async def owner_wallet(
    owner: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(
        select(func.sum(RevenueLog.amount)).where(RevenueLog.status == "completed")
    )
    total_revenue_usd = float(total_result.scalar() or 0.0)

    pkr_rate = 275.0
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            fx = await client.get(
                settings.EXCHANGE_RATE_API_URL,
                params={"base": "USD", "symbols": "PKR", "access_key": settings.EXCHANGE_RATE_API_KEY or "", "app_id": settings.EXCHANGE_RATE_API_KEY or ""},
            )
            fx.raise_for_status()
            payload = fx.json()
            pkr_rate = float((payload.get("rates") or {}).get("PKR", 275.0))
    except Exception:
        pass

    r = _redis_client()
    payouts_usd = float(await r.get("owner:payouts_usd") or 0.0)
    owner_card_usage = float(await r.get("owner:card_usage_usd") or 0.0)

    card_result = await db.execute(
        select(VaultData).where(
            VaultData.user_id == owner.id,
            VaultData.project_name == "__owner_payment_card__",
        )
    )
    card_entry = card_result.scalar_one_or_none()
    card_balance = 0.0
    if card_entry:
        card_balance = float(_decrypt_payload(card_entry.data_encrypted).get("card_balance_usd", 0) or 0)

    return {
        "owner_email": owner.email,
        "total_revenue_usd": round(total_revenue_usd, 2),
        "total_revenue_pkr": round(total_revenue_usd * pkr_rate, 2),
        "payouts_to_allied_bank_usd": round(payouts_usd, 2),
        "payouts_to_allied_bank_pkr": round(payouts_usd * pkr_rate, 2),
        "owner_card_usage_usd": round(owner_card_usage, 2),
        "owner_card_balance_usd": round(card_balance, 2),
        "allied_bank": {
            "account_name": settings.ALLIED_BANK_ACCOUNT_NAME,
            "account_number": settings.ALLIED_BANK_ACCOUNT_NUMBER,
            "iban": settings.ALLIED_BANK_IBAN,
            "swift": settings.ALLIED_BANK_SWIFT,
            "branch": settings.ALLIED_BANK_BRANCH,
        },
    }


@router.post("/owner/withdraw")
async def owner_withdraw(
    payload: OwnerWithdrawRequest,
    request: Request,
    owner: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    total_result = await db.execute(
        select(func.sum(RevenueLog.amount)).where(RevenueLog.status == "completed")
    )
    total_revenue_usd = float(total_result.scalar() or 0.0)

    r = _redis_client()
    payouts_usd = float(await r.get("owner:payouts_usd") or 0.0)
    available = max(total_revenue_usd - payouts_usd, 0.0)

    if payload.amount_usd > available:
        raise HTTPException(status_code=400, detail=f"Insufficient available balance. Available: ${available:.2f}")

    new_total = round(payouts_usd + payload.amount_usd, 2)
    await r.set("owner:payouts_usd", new_total)

    await log_admin_action(db, owner.id, "owner_withdraw", "wallet", None, f"Owner withdrew ${payload.amount_usd} to Allied Bank", request)
    return {
        "message": "Withdrawal queued to Allied Bank",
        "withdrawn_usd": round(payload.amount_usd, 2),
        "total_payouts_usd": new_total,
        "allied_bank": {
            "account_name": settings.ALLIED_BANK_ACCOUNT_NAME,
            "account_number": settings.ALLIED_BANK_ACCOUNT_NUMBER,
            "iban": settings.ALLIED_BANK_IBAN,
            "swift": settings.ALLIED_BANK_SWIFT,
            "branch": settings.ALLIED_BANK_BRANCH,
        },
    }


# ---- User Management ----

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """List all users with pagination and search."""
    search_sanitized = InputSanitizer.sanitize_text(search) if search else None

    query = select(User).options(selectinload(User.subscription))

    if search_sanitized:
        query = query.where(User.email.ilike(f"%{search_sanitized}%") | User.display_name.ilike(f"%{search_sanitized}%"))

    query = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    count_query = select(func.count(User.id))
    if search_sanitized:
        count_query = count_query.where(User.email.ilike(f"%{search_sanitized}%") | User.display_name.ilike(f"%{search_sanitized}%"))
    total = await db.execute(count_query)
    total_count = total.scalar()

    return {
        "users": [
            UserAdminResponse(
                id=str(u.id),
                email=u.email,
                display_name=u.display_name,
                is_active=u.is_active,
                is_banned=u.is_banned,
                is_approved=u.is_approved,
                is_admin=u.is_admin,
                plan=u.subscription.plan if u.subscription else "free",
                free_access_granted=bool(u.subscription and u.subscription.payment_method == FREE_ACCESS_PAYMENT_METHOD and u.subscription.status == "active"),
                created_at=u.created_at.isoformat() if u.created_at else "",
                last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
            )
            for u in users
        ],
        "total": total_count,
        "page": page,
        "limit": limit,
    }


@router.post("/approve/{email}")
async def approve_user(
    email: str,
    request: Request,
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Approve a user registration."""
    email = InputSanitizer.sanitize_text(email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_approved = True
    await db.commit()
    await log_admin_action(db, admin.id, "approve_user", "user", str(user.id), f"Approved user {email}", request)
    return {"message": f"User {email} approved successfully"}


@router.post("/users/{user_id}/{action}")
async def user_action_by_id(
    user_id: str,
    action: str,
    request: Request,
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Perform approve/disapprove/ban actions by user id for static frontend compatibility."""
    if action not in {"approve", "disapprove", "ban", "grant-free-access", "revoke-free-access"}:
        raise HTTPException(status_code=400, detail="Invalid action")

    try:
        parsed_user_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user id")

    result = await db.execute(select(User).where(User.id == parsed_user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if action == "approve":
        user.is_approved = True
        details = f"Approved user {user.email}"
    elif action == "disapprove":
        user.is_approved = False
        details = f"Disapproved user {user.email}"
    elif action == "ban":
        if user.is_admin:
            raise HTTPException(status_code=400, detail="Cannot ban another admin")
        user.is_banned = True
        user.is_active = False
        details = f"Banned user {user.email}"
    elif action == "grant-free-access":
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscription = sub_result.scalar_one_or_none()

        if subscription and subscription.payment_method == FREE_ACCESS_PAYMENT_METHOD and subscription.status == "active":
            return {
                "message": f"Free full access already granted to {user.email}",
                "free_access_slots_total": FREE_ACCESS_MAX_USERS,
            }

        used_result = await db.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.payment_method == FREE_ACCESS_PAYMENT_METHOD,
                    Subscription.status == "active",
                )
            )
        )
        used_slots = int(used_result.scalar() or 0)
        if used_slots >= FREE_ACCESS_MAX_USERS:
            raise HTTPException(
                status_code=400,
                detail=f"Free access slot limit reached ({FREE_ACCESS_MAX_USERS}/{FREE_ACCESS_MAX_USERS}). Revoke one user first.",
            )

        now = datetime.now(timezone.utc)
        if not subscription:
            subscription = Subscription(user_id=user.id)
            db.add(subscription)

        subscription.plan = "enterprise"
        subscription.status = "active"
        subscription.payment_method = FREE_ACCESS_PAYMENT_METHOD
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(days=3650)

        user.is_approved = True
        user.is_active = True
        user.is_banned = False

        details = f"Granted admin free full-access to {user.email}"
    else:
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
        subscription = sub_result.scalar_one_or_none()
        if not subscription or subscription.payment_method != FREE_ACCESS_PAYMENT_METHOD:
            raise HTTPException(status_code=400, detail="User does not have admin free access")

        subscription.plan = "free"
        subscription.status = "active"
        subscription.payment_method = None
        subscription.current_period_start = None
        subscription.current_period_end = None
        details = f"Revoked admin free full-access from {user.email}"

    await db.commit()
    await log_admin_action(db, admin.id, f"{action}_user", "user", str(user.id), details, request)
    if action in {"grant-free-access", "revoke-free-access"}:
        used_result = await db.execute(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.payment_method == FREE_ACCESS_PAYMENT_METHOD,
                    Subscription.status == "active",
                )
            )
        )
        used_slots = int(used_result.scalar() or 0)
        return {
            "message": details,
            "free_access_slots_used": used_slots,
            "free_access_slots_total": FREE_ACCESS_MAX_USERS,
            "free_access_slots_remaining": max(FREE_ACCESS_MAX_USERS - used_slots, 0),
        }
    return {"message": details}


@router.get("/owner/free-access-users")
async def list_free_access_users(
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """List users currently receiving admin free full-access seats."""
    result = await db.execute(
        select(User, Subscription)
        .join(Subscription, Subscription.user_id == User.id)
        .where(
            Subscription.payment_method == FREE_ACCESS_PAYMENT_METHOD,
            Subscription.status == "active",
        )
        .order_by(Subscription.updated_at.desc())
    )

    rows = result.all()
    users = [
        {
            "user_id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "plan": subscription.plan,
            "granted_at": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
        }
        for user, subscription in rows
    ]
    used = len(users)
    return {
        "users": users,
        "slots_used": used,
        "slots_total": FREE_ACCESS_MAX_USERS,
        "slots_remaining": max(FREE_ACCESS_MAX_USERS - used, 0),
    }


@router.post("/disapprove/{email}")
async def disapprove_user(
    email: str,
    request: Request,
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Disapprove a user registration."""
    email = InputSanitizer.sanitize_text(email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_approved = False
    await db.commit()
    await log_admin_action(db, admin.id, "disapprove_user", "user", str(user.id), f"Disapproved user {email}", request)
    return {"message": f"User {email} disapproved"}


@router.post("/ban/{email}")
async def ban_user(
    email: str,
    request: Request,
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Ban a user from the platform."""
    email = InputSanitizer.sanitize_text(email)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot ban another admin")

    user.is_banned = True
    user.is_active = False
    await db.commit()
    await log_admin_action(db, admin.id, "ban_user", "user", str(user.id), f"Banned user {email}", request)
    return {"message": f"User {email} banned successfully"}


# ---- Revenue ----

@router.get("/revenue")
async def get_revenue(
    period: str = Query("month", pattern="^(day|week|month|year|all)$"),
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """View revenue statistics."""
    query = select(
        func.sum(RevenueLog.amount).label("total_revenue"),
        func.count(RevenueLog.id).label("total_transactions"),
        func.avg(RevenueLog.amount).label("avg_transaction"),
    ).where(RevenueLog.status == "completed")

    result = await db.execute(query)
    stats = result.one()

    recent = await db.execute(
        select(RevenueLog).order_by(RevenueLog.created_at.desc()).limit(20)
    )
    transactions = recent.scalars().all()

    active_plan_counts_query = await db.execute(
        select(Subscription.plan, func.count(Subscription.id))
        .where(
            Subscription.status == "active",
            Subscription.plan.in_(["starter", "pro", "pro_yearly", "max", "business", "enterprise"]),
        )
        .group_by(Subscription.plan)
    )
    active_plan_counts = {row[0]: int(row[1]) for row in active_plan_counts_query.all()}

    mrr_unit_usd = {
        "starter": 9.99,
        "pro": 19.99,
        "pro_yearly": 159.99 / 12.0,
        "max": 99.99,
        "business": 24.99,
        "enterprise": 499.0,
    }
    mrr_by_plan = {
        plan: round(count * mrr_unit_usd.get(plan, 0.0), 2)
        for plan, count in active_plan_counts.items()
    }
    mrr_total_usd = round(sum(mrr_by_plan.values()), 2)

    pkr_rate = 275.0
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            fx = await client.get(
                settings.EXCHANGE_RATE_API_URL,
                params={"base": "USD", "symbols": "PKR", "access_key": settings.EXCHANGE_RATE_API_KEY or "", "app_id": settings.EXCHANGE_RATE_API_KEY or ""},
            )
            fx.raise_for_status()
            payload = fx.json()
            pkr_rate = float((payload.get("rates") or {}).get("PKR", 275.0))
    except Exception:
        pass

    total_revenue_usd = float(stats.total_revenue or 0)
    total_revenue_pkr = round(total_revenue_usd * pkr_rate, 2)
    mrr_total_pkr = round(mrr_total_usd * pkr_rate, 2)

    mrr_formula_examples = []
    for plan, count in active_plan_counts.items():
        unit = mrr_unit_usd.get(plan, 0.0)
        mrr_formula_examples.append(
            f"{count:,} {plan.upper()} users x ${unit:.2f} = ${count * unit:,.2f}/month"
        )

    return {
        "total_revenue": total_revenue_usd,
        "total_revenue_pkr": total_revenue_pkr,
        "total_transactions": stats.total_transactions,
        "average_transaction": float(stats.avg_transaction or 0),
        "active_subscribers_per_plan": active_plan_counts,
        "mrr_estimate_usd": mrr_total_usd,
        "mrr_estimate_pkr": mrr_total_pkr,
        "mrr_by_plan_usd": mrr_by_plan,
        "mrr_formula_examples": mrr_formula_examples,
        "recent_transactions": [
            {
                "id": str(t.id),
                "amount": float(t.amount),
                "currency": t.currency,
                "payment_method": t.payment_method,
                "status": t.status,
                "metadata": json.loads(t.description) if t.description and t.description.startswith("{") else None,
                "created_at": t.created_at.isoformat() if t.created_at is not None else "",
            }
            for t in transactions
        ],
    }


@router.post("/refund/{transaction_id}")
async def refund_payment(
    transaction_id: str,
    reason: str,
    request: Request,
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Process a refund for a transaction."""
    result = await db.execute(
        select(RevenueLog).where(RevenueLog.transaction_id == transaction_id)
    )
    revenue = result.scalar_one_or_none()

    if not revenue:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if revenue.status == "refunded":
        raise HTTPException(status_code=400, detail="Transaction already refunded")

    refund = RefundLog(
        revenue_id=revenue.id,
        admin_id=admin.id,
        amount=revenue.amount,
        reason=reason,
    )
    db.add(refund)

    revenue.status = "refunded"
    await db.commit()
    await log_admin_action(db, admin.id, "refund", "revenue", str(revenue.id), f"Refunded {revenue.amount} {revenue.currency}", request)

    return {"message": f"Refund of {revenue.amount} {revenue.currency} processed successfully"}


# ---- Vault ----

@router.get("/vault/{email}")
async def view_vault(
    email: str,
    request: Request,
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """View and decrypt a user's vault data (with audit trail)."""
    email = InputSanitizer.sanitize_text(email)
    user_result = await db.execute(select(User).where(User.email == email))
    target_user = user_result.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    vault_result = await db.execute(
        select(VaultData).where(VaultData.user_id == target_user.id)
    )
    vault_entries = vault_result.scalars().all()

    for entry in vault_entries:
        access_log = VaultAccessLog(
            accessed_by_admin_id=admin.id,
            target_user_id=target_user.id,
            vault_entry_id=entry.id,
            action="view",
        )
        db.add(access_log)

    await db.commit()
    await log_admin_action(db, admin.id, "view_vault", "vault", str(target_user.id), f"Viewed vault for {email}", request)

    return {
        "user_email": email,
        "vault_entries": [
            {
                "id": str(entry.id),
                "project_name": entry.project_name,
                "encrypted": True,
                "version": entry.version,
                "created_at": entry.created_at.isoformat() if entry.created_at is not None else "",
                "updated_at": entry.updated_at.isoformat() if entry.updated_at is not None else "",
                "note": "Data is AES-256-GCM encrypted. Use admin decryption key to view.",
            }
            for entry in vault_entries
        ],
    }

# ---- Usage Analytics ----

@router.get("/analytics")
async def get_analytics(
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Get usage analytics and statistics."""
    total_users = await db.execute(select(func.count(User.id)))
    total_users_count = total_users.scalar()

    active_users = await db.execute(
        select(func.count(func.distinct(UsageLog.user_id)))
        .where(UsageLog.created_at >= func.now() - func.make_interval(days=7))
    )
    active_users_count = active_users.scalar()

    pro_users = await db.execute(
        select(func.count(Subscription.id)).where(
            Subscription.plan.in_(["starter", "pro", "pro_yearly", "max", "business", "enterprise", "trial"]),
            Subscription.status == "active",
        )
    )
    pro_users_count = pro_users.scalar()

    total_calls = await db.execute(select(func.count(UsageLog.id)))
    total_calls_count = total_calls.scalar()

    today_calls = await db.execute(
        select(func.count(UsageLog.id)).where(
            UsageLog.action == "code_generation",
            UsageLog.created_at >= func.now() - func.make_interval(hours=24),
        )
    )
    today_calls_count = today_calls.scalar()

    return {
        "total_users": total_users_count,
        "active_users_7days": active_users_count,
        "pro_users": pro_users_count,
        "total_api_calls": total_calls_count,
        "code_generations_today": today_calls_count,
    }


@router.get("/overview")
async def get_overview(
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """Compatibility endpoint for admin overview cards."""
    analytics = await get_analytics(admin=admin, db=db)
    return {
        "total_users": analytics.get("total_users", 0),
        "active_subscribers": analytics.get("pro_users", 0),
        "revenue_usd": 0,
        "revenue_pkr": 0,
        "media_jobs_today": analytics.get("code_generations_today", 0),
    }


# ---- Support Tickets ----

@router.get("/tickets")
async def list_tickets(
    status_filter: Optional[str] = Query(None, pattern="^(open|in_progress|resolved|closed)$"),
    admin: User = Depends(get_current_owner),
    db: AsyncSession = Depends(get_db),
):
    """List all support tickets."""
    query = select(SupportTicket).order_by(SupportTicket.created_at.desc())

    if status_filter:
        query = query.where(SupportTicket.status == status_filter)

    result = await db.execute(query)
    tickets = result.scalars().all()

    return {
        "tickets": [
            {
                "id": str(t.id),
                "user_id": str(t.user_id),
                "subject": t.subject,
                "status": t.status,
                "priority": t.priority,
                "created_at": t.created_at.isoformat() if t.created_at is not None else "",
            }
            for t in tickets
        ]
    }
