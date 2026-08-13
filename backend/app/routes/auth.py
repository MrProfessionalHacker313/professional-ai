"""
Professional AI - Authentication Routes
Login, register, OAuth, 2FA, passkeys, refresh tokens, logout.
SECURITY HARDENED: OAuth state validation, request body models, secure QR codes, refresh token validation.
"""

import base64
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any, Dict, List
import uuid
import secrets
import asyncio
import httpx
import qrcode
import io
from datetime import datetime, timezone, timedelta
from jose import jwt as jose_jwt

from loguru import logger
from app.database import get_db
from app.config import settings
from app.models.user import User, OAuthAccount, TwoFactorAuth, Session, Passkey
from app.models.owner_settings import OwnerSettings
from app.services.auth_service import AuthService, get_current_user, get_current_admin
from app.middleware.security import InputSanitizer, PasswordValidator, generate_csrf_token
from cryptography.fernet import Fernet

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

OAUTH_STATE_TTL_SECONDS = 900  # 15 minutes

# In-memory WebAuthn challenge store
_webauthn_challenges: dict = {}
WEBAUTHN_CHALLENGE_TTL_SECONDS = 300  # 5 minutes

# In-memory password reset token store
_password_reset_tokens: dict = {}
PASSWORD_RESET_TOKEN_TTL_SECONDS = 3600  # 1 hour

# In-memory used OAuth JTI store
_used_oauth_jti: dict = {}

# In-memory owner setup token store
_owner_setup_tokens: dict = {}
OWNER_SETUP_TOKEN_TTL_SECONDS = 900  # 15 minutes


def _derive_frontend_origin(request: Optional[Request] = None) -> str:
    """Resolve frontend origin from request Origin header with env fallback."""
    if request:
        origin = request.headers.get("origin")
        if origin:
            return origin.rstrip("/")
    return settings.FRONTEND_URL.rstrip("/")


def _derive_rp_id(request: Optional[Request] = None) -> str:
    origin = _derive_frontend_origin(request)
    return origin.replace("https://", "").replace("http://", "").split(":")[0] or "localhost"


def _generate_oauth_state() -> str:
    """Generate stateless signed OAuth state token to support multi-instance deployments."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=OAUTH_STATE_TTL_SECONDS)
    payload = {
        "type": "oauth_state",
        "nonce": secrets.token_urlsafe(16),
        "jti": secrets.token_urlsafe(16),
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jose_jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def _validate_oauth_state(state: str) -> bool:
    """Validate OAuth state parameter with one-time JTI tracking."""
    if not state:
        return False

    try:
        payload = jose_jwt.decode(
            state,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False, "verify_iss": False},
        )
        if payload.get("type") != "oauth_state" or not payload.get("nonce"):
            return False
    except Exception:
        return False

    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()

    if payload.get("exp") and now_ts > payload["exp"]:
        return False

    jti = payload.get("jti")
    if not jti:
        return False

    expired_jtis = [j for j, exp_ts in _used_oauth_jti.items() if now_ts > exp_ts]
    for j in expired_jtis:
        _used_oauth_jti.pop(j, None)

    if jti in _used_oauth_jti:
        return False

    _used_oauth_jti[jti] = now_ts + OAUTH_STATE_TTL_SECONDS
    return True


# ---- Request/Response Models ----

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)
    display_name: Optional[str] = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    # Password is OPTIONAL — the owner can log in with email only (password/OTP default OFF).
    # Non-owner users still must provide a password.
    password: Optional[str] = Field(default=None, min_length=1, max_length=128)
    totp_code: Optional[str] = Field(default=None, min_length=6, max_length=10)
    device_fingerprint: Optional[str] = Field(default=None, min_length=32, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    csrf_token: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20, max_length=500)


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    is_admin: bool
    is_approved: bool
    preferred_language: str
    plan: str = "free"


class OAuthCallbackRequest(BaseModel):
    provider: str
    code: str = Field(..., min_length=10)
    state: str = Field(..., min_length=16)
    redirect_uri: str


class OwnerEmailLoginRequest(BaseModel):
    email: EmailStr


class OwnerSetupFinishRequest(BaseModel):
    email: EmailStr
    setup_token: str = Field(..., min_length=20, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    enable_totp: bool = False
    totp_secret: Optional[str] = Field(default=None, min_length=16, max_length=255)
    totp_code: Optional[str] = Field(default=None, min_length=6, max_length=10)


class OwnerPasswordResetRequest(BaseModel):
    email: EmailStr


class OwnerTotpBootstrapRequest(BaseModel):
    email: EmailStr
    setup_token: str = Field(..., min_length=20, max_length=255)


class OwnerPasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    token: str = Field(..., min_length=6, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=128)


def _owner_fernet() -> Fernet:
    key_seed = (settings.SECRET_KEY or settings.JWT_SECRET or "professional-ai-owner-key").encode("utf-8")
    digest = hashlib.sha256(key_seed).digest()
    fernet_key = base64.urlsafe_b64encode(digest)
    return Fernet(fernet_key)


def _encrypt_owner_secret(raw_secret: str) -> str:
    return _owner_fernet().encrypt(raw_secret.encode("utf-8")).decode("utf-8")


def _decrypt_owner_secret(secret_encrypted: str) -> str:
    return _owner_fernet().decrypt(secret_encrypted.encode("utf-8")).decode("utf-8")


def _store_owner_setup_token(token: str, email: str) -> None:
    _owner_setup_tokens[token] = {
        "email": email,
        "created_at": datetime.now(timezone.utc),
    }
    now = datetime.now(timezone.utc)
    expired = [
        t for t, meta in _owner_setup_tokens.items()
        if (now - meta["created_at"]).total_seconds() > OWNER_SETUP_TOKEN_TTL_SECONDS
    ]
    for item in expired:
        _owner_setup_tokens.pop(item, None)


def _consume_owner_setup_token(token: str, email: str) -> bool:
    meta = _owner_setup_tokens.get(token)
    if not meta:
        return False
    _owner_setup_tokens.pop(token, None)
    if meta.get("email") != email:
        return False
    created_at = meta.get("created_at")
    if not created_at:
        return False
    return (datetime.now(timezone.utc) - created_at).total_seconds() <= OWNER_SETUP_TOKEN_TTL_SECONDS


def _is_owner_setup_token_valid(token: str, email: str) -> bool:
    meta = _owner_setup_tokens.get(token)
    if not meta or meta.get("email") != email:
        return False
    created_at = meta.get("created_at")
    if not created_at:
        return False
    return (datetime.now(timezone.utc) - created_at).total_seconds() <= OWNER_SETUP_TOKEN_TTL_SECONDS


# ------------------------------------------------------------------
# OAuth redirect URI: frontend callback path (SPA relay architecture).
# Google/GitHub console mein EXACT yahi URI register karo.
# ------------------------------------------------------------------
def _frontend_oauth_redirect(provider: str, request: Optional[Request] = None) -> str:
    origin = None
    if request:
        origin = request.headers.get("origin")
        if not origin:
            referer = request.headers.get("referer")
            if referer:
                parts = referer.split("/")
                if len(parts) >= 3:
                    origin = parts[0] + "//" + parts[2]
        if origin:
            origin = origin.rstrip("/")
    if not origin:
        origin = settings.FRONTEND_URL.rstrip("/")
    redirect_uri = f"{origin}/auth/callback/{provider}"
    # Config override ke liye (agar aapne custom path use kiya ho)
    if getattr(settings, "OAUTH_CALLBACK_PATH", None):
        redirect_uri = f"{origin}{settings.OAUTH_CALLBACK_PATH}/{provider}"
    return redirect_uri


def _provider_credentials(provider: str) -> tuple[Optional[str], Optional[str]]:
    mapping = {
        "google": (settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET),
    }
    return mapping.get(provider, (None, None))


def _provider_auth_url(provider: str, state: str, request: Optional[Request] = None) -> str:
    from urllib.parse import quote
    redirect_uri = _frontend_oauth_redirect(provider, request)
    safe_redirect = quote(redirect_uri, safe=":/")
    safe_state = quote(state, safe="")

    if provider == "google":
        # access_type=offline + prompt=consent => refresh_token wapas aaye
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
            f"&access_type=offline"
            f"&prompt=consent"
            f"&redirect_uri={safe_redirect}"
            f"&state={safe_state}"
        )
    return ""


# FIX: ab _finalize_oauth_login ko REAL request pass hoti hai (fake Request crash fix)
async def _finalize_oauth_login(
    provider: str,
    provider_account_id: str,
    email: str,
    display_name: Optional[str],
    avatar_url: Optional[str],
    access_token: Optional[str],
    db: AsyncSession,
    request: Request,
    refresh_token: Optional[str] = None,
) -> dict:
    normalized_email = email.lower().strip()
    if not normalized_email:
        raise HTTPException(status_code=400, detail=f"{provider.title()} account has no email")

    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=normalized_email,
            display_name=display_name or normalized_email.split("@")[0],
            avatar_url=avatar_url,
            email_verified=True,
            is_active=True,
        )
        db.add(user)
        await db.flush()
    else:
        user.display_name = user.display_name or display_name
        user.avatar_url = user.avatar_url or avatar_url
        if not user.email_verified:
            user.email_verified = True

    oauth_result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_account_id == provider_account_id,
        )
    )
    oauth_account = oauth_result.scalar_one_or_none()
    if not oauth_account:
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        db.add(oauth_account)
    else:
        oauth_account.access_token = access_token
        oauth_account.refresh_token = refresh_token

    await AuthService.invalidate_all_sessions(db, user.id)
    access_token_jwt = AuthService.create_access_token(str(user.id), user.email, user.is_admin)
    refresh_token_jwt = AuthService.create_refresh_token(str(user.id))
    # FIX: REAL request pass karo
    await AuthService.create_session(db, user.id, refresh_token_jwt, request)
    await db.commit()

    csrf_token = generate_csrf_token()
    return {
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            is_admin=user.is_admin,
            is_approved=user.is_approved,
            preferred_language=user.preferred_language,
        ),
        "tokens": TokenResponse(
            access_token=access_token_jwt,
            refresh_token=refresh_token_jwt,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            csrf_token=csrf_token,
        ),
    }


async def _exchange_oauth_code(
    provider: str,
    code: str,
    redirect_uri: str,
    token_url: str,
    token_data: Dict[str, Any],
    *,
    use_basic_auth: bool = False,
    extra_headers: Optional[Dict[str, str]] = None,
    client_secret: Optional[str] = None,
) -> Dict[str, Any]:
    resolved_client_id, resolved_client_secret = _provider_credentials(provider)
    if client_secret is not None:
        resolved_client_secret = client_secret
    if not resolved_client_id or not resolved_client_secret:
        raise HTTPException(
            status_code=400,
            detail=f"{provider.title()} sign-in is not configured. Please ask the admin to add the {provider.title()} API keys.",
        )

    payload = dict(token_data)
    payload.update({"code": code, "redirect_uri": redirect_uri})

    headers = {"Accept": "application/json"}
    if extra_headers:
        headers.update(extra_headers)

    request_kwargs: Dict[str, Any] = {"data": payload, "headers": headers}
    if use_basic_auth:
        request_kwargs["auth"] = (resolved_client_id, resolved_client_secret)
    else:
        payload.setdefault("client_id", resolved_client_id)
        payload.setdefault("client_secret", resolved_client_secret)

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_response = await client.post(token_url, **request_kwargs)
        if token_response.status_code != 200:
            logger.error(f"{provider.title()} token exchange failed: {token_response.text}")
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        return token_response.json()


async def _handle_microsoft_callback(code: str, redirect_uri: str, db: AsyncSession, request: Request) -> dict:
    token_json = await _exchange_oauth_code(
        "microsoft",
        code,
        redirect_uri,
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        {"grant_type": "authorization_code", "scope": "openid email profile"},
        use_basic_auth=True,
    )

    access_token = token_json.get("access_token")
    async with httpx.AsyncClient(timeout=15.0) as client:
        userinfo_response = await client.get(
            "https://graph.microsoft.com/oidc/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch user info from Microsoft")
        microsoft_user = userinfo_response.json()

    return await _finalize_oauth_login(
        provider="microsoft",
        provider_account_id=str(microsoft_user.get("sub") or microsoft_user.get("id") or microsoft_user.get("email")),
        email=microsoft_user.get("email") or microsoft_user.get("preferred_username") or "",
        display_name=microsoft_user.get("name"),
        avatar_url=None,
        access_token=access_token,
        refresh_token=token_json.get("refresh_token"),
        db=db,
        request=request,
    )


async def _handle_google_callback(code: str, redirect_uri: str, db: AsyncSession, request: Request) -> dict:
    """Exchange Google authorization code for tokens and create/login user."""
    try:
        token_json = await _exchange_oauth_code(
            "google",
            code,
            redirect_uri,
            "https://oauth2.googleapis.com/token",
            {"grant_type": "authorization_code"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Google token exchange network error: {exc}")
        raise HTTPException(status_code=400, detail="Failed to connect to Google OAuth service")

    access_token = token_json.get("access_token")
    if not token_json.get("id_token"):
        raise HTTPException(status_code=400, detail="Missing id_token from Google")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch user info from Google")
            google_user = userinfo_response.json()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Google userinfo fetch error: {exc}")
        raise HTTPException(status_code=400, detail="Failed to fetch user info from Google")

    return await _finalize_oauth_login(
        provider="google",
        provider_account_id=str(google_user.get("sub") or google_user.get("email")),
        email=google_user.get("email") or "",
        display_name=google_user.get("name"),
        avatar_url=google_user.get("picture"),
        access_token=access_token,
        refresh_token=token_json.get("refresh_token"),
        db=db,
        request=request,
    )


async def _get_or_create_owner_settings(db: AsyncSession, owner_email: str) -> OwnerSettings:
    result = await db.execute(select(OwnerSettings).where(OwnerSettings.owner_email == owner_email))
    settings_row = result.scalar_one_or_none()
    if settings_row:
        return settings_row

    settings_row = OwnerSettings(owner_email=owner_email)
    db.add(settings_row)
    await db.flush()
    await db.commit()
    return settings_row


async def _issue_login_response(
    db: AsyncSession,
    request: Request,
    user: User,
    plan: str = "free",
) -> dict:
    await AuthService.invalidate_all_sessions(db, user.id)

    access_token = AuthService.create_access_token(str(user.id), user.email, user.is_admin)
    refresh_token = AuthService.create_refresh_token(str(user.id))
    await AuthService.create_session(db, user.id, refresh_token, request)

    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host if request.client else None
    await db.commit()

    csrf_token = generate_csrf_token()
    return {
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            is_admin=user.is_admin,
            is_approved=user.is_approved,
            preferred_language=user.preferred_language,
            plan=plan,
        ),
        "tokens": TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            csrf_token=csrf_token,
        ),
    }


# ---- Routes ----

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: Request, reg: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    email = InputSanitizer.sanitize_text(reg.email.lower().strip())
    password = reg.password
    display_name = InputSanitizer.sanitize_text(reg.display_name or email.split("@")[0])

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=email,
        password_hash=AuthService.hash_password(password),
        display_name=display_name,
    )
    db.add(user)
    await db.flush()

    access_token = AuthService.create_access_token(str(user.id), user.email, user.is_admin)
    refresh_token = AuthService.create_refresh_token(str(user.id))

    # FIX: REAL request pass karo (register crash fix)
    await AuthService.create_session(db, user.id, refresh_token, request)

    csrf_token = generate_csrf_token()

    return {
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            is_admin=user.is_admin,
            is_approved=user.is_approved,
            preferred_language=user.preferred_language,
        ),
        "tokens": TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            csrf_token=csrf_token,
        ),
    }


@router.post("/login")
async def login(request: Request, login_request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password."""
    email = login_request.email.lower().strip()
    password = login_request.password
    device_fingerprint = login_request.device_fingerprint

    lockout_remaining = await AuthService.check_account_lockout(db, email)
    if lockout_remaining is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked. Try again in {lockout_remaining // 60} minutes.",
            headers={"Retry-After": str(lockout_remaining)},
        )

    result = await db.execute(
        select(User).where(User.email == email).options(selectinload(User.two_factor_auth), selectinload(User.subscription))
    )
    user = result.scalar_one_or_none()

    if settings.is_owner_email(email):
        owner_settings = await _get_or_create_owner_settings(db, email)

        # OWNER EMAIL-ONLY LOGIN: password/OTP are OPTIONAL (default OFF).
        # The owner is ALWAYS allowed to log in with just their email.
        # If a password IS provided and a password hash exists, verify it;
        # otherwise skip password verification entirely (owner never blocked).
        password_ok = True
        if password and owner_settings.password_hash:
            password_ok = AuthService.verify_password(password, owner_settings.password_hash)
        elif owner_settings.password_hash and not password:
            # Password required by existing owner settings but none provided —
            # still allow email-only access per requirement (owner never blocked).
            password_ok = True

        if not password_ok:
            if user:
                await AuthService.increment_failed_login(db, user)
            await AuthService.record_login_attempt(db, email, user, False, request, "Invalid owner credentials")
            raise HTTPException(status_code=401, detail="Invalid owner credentials")

        # TOTP check — only enforced if TOTP is explicitly enabled AND a code was provided.
        # Password/OTP default OFF: never force the owner into a TOTP wall.
        if owner_settings.totp_enabled and login_request.totp_code:
            if not owner_settings.totp_secret_encrypted:
                raise HTTPException(status_code=400, detail="Owner TOTP is misconfigured")
            owner_totp_secret = _decrypt_owner_secret(owner_settings.totp_secret_encrypted)
            if not AuthService.verify_totp_code(owner_totp_secret, login_request.totp_code):
                if user:
                    await AuthService.increment_failed_login(db, user)
                await AuthService.record_login_attempt(db, email, user, False, request, "Invalid owner TOTP")
                raise HTTPException(status_code=401, detail="Invalid owner TOTP code")

        if not user:
            user = User(
                email=email,
                password_hash=owner_settings.password_hash,
                display_name="Owner",
                is_admin=True,
                is_approved=True,
                is_active=True,
                is_banned=False,
                email_verified=True,
            )
            db.add(user)
            await db.flush()
        else:
            user.password_hash = owner_settings.password_hash or user.password_hash
            user.is_admin = True
            user.is_approved = True
            user.is_active = True
            user.is_banned = False
            user.email_verified = True
            user.failed_login_attempts = 0
            user.locked_until = None

        await AuthService.reset_failed_login(db, user)
        owner_response = await _issue_login_response(
            db=db,
            request=request,
            user=user,
            plan=user.subscription.plan if user.subscription else "free",
        )
        await AuthService.record_login_attempt(db, email, user, True, request)
        return owner_response

    if not user or not user.password_hash or not password or not AuthService.verify_password(password, user.password_hash):
        if user:
            await AuthService.increment_failed_login(db, user)
        await AuthService.record_login_attempt(db, email, user, False, request, "Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.is_banned:
        await AuthService.record_login_attempt(db, email, user, False, request, "Account banned")
        raise HTTPException(status_code=403, detail="Account is banned. Contact support.")

    await AuthService.reset_failed_login(db, user)

    if user.two_factor_auth and user.two_factor_auth.is_enabled:
        if not login_request.totp_code:
            await AuthService.record_login_attempt(db, email, user, False, request, "2FA required")
            return JSONResponse(
                status_code=200,
                content={"requires_2fa": True, "user_id": str(user.id)},
            )
        if not AuthService.verify_totp_code(user.two_factor_auth.secret, login_request.totp_code):
            await AuthService.increment_failed_login(db, user)
            await AuthService.record_login_attempt(db, email, user, False, request, "Invalid 2FA code")
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

    user.device_fingerprint = device_fingerprint
    response = await _issue_login_response(
        db=db,
        request=request,
        user=user,
        plan=user.subscription.plan if user.subscription else "free",
    )

    await AuthService.record_login_attempt(db, email, user, True, request)

    try:
        asyncio.create_task(AuthService.send_login_alert(user, request))
    except Exception:
        pass

    return response


@router.post("/owner/email-login")
async def owner_email_login(payload: OwnerEmailLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """OWNER EMAIL-ONLY LOGIN (PERMANENT FIX). Email-only, no password/OTP, never blocked."""
    owner_email = payload.email.lower().strip()
    if not settings.is_owner_email(owner_email):
        raise HTTPException(status_code=403, detail="Owner access required")

    await _get_or_create_owner_settings(db, owner_email)

    result = await db.execute(
        select(User)
        .where(User.email == owner_email)
        .options(selectinload(User.subscription))
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=owner_email,
            display_name="Owner",
            is_admin=True,
            is_approved=True,
            is_active=True,
            is_banned=False,
            email_verified=True,
        )
        db.add(user)
        await db.flush()
    else:
        user.is_admin = True
        user.is_approved = True
        user.is_active = True
        user.is_banned = False
        user.email_verified = True
        user.failed_login_attempts = 0
        user.locked_until = None

    response = await _issue_login_response(
        db=db,
        request=request,
        user=user,
        plan=user.subscription.plan if user.subscription else "free",
    )

    await AuthService.record_login_attempt(db, owner_email, user, True, request)
    logger.info(f"👑 OWNER EMAIL-ONLY LOGIN SUCCESS: {owner_email}")
    return response


@router.post("/refresh")
async def refresh_token(request: Request, refresh_req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = AuthService.decode_token(refresh_req.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    if user.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned")

    token_hash = AuthService.hash_refresh_token(refresh_req.refresh_token)
    session_result = await db.execute(
        select(Session).where(
            Session.user_id == user.id,
            Session.refresh_token_hash == token_hash,
            Session.is_valid == True,
        )
    )
    session = session_result.scalar_one_or_none()

    if not session:
        await AuthService.invalidate_all_sessions(db, user.id)
        raise HTTPException(status_code=401, detail="Invalid refresh token session")

    if session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    await AuthService.invalidate_all_sessions(db, user.id)

    access_token = AuthService.create_access_token(str(user.id), user.email, user.is_admin)
    new_refresh_token = AuthService.create_refresh_token(str(user.id))

    await AuthService.create_session(db, user.id, new_refresh_token, request)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout - invalidate all sessions."""
    await AuthService.invalidate_all_sessions(db, current_user.id)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        is_admin=current_user.is_admin,
        is_approved=current_user.is_approved,
        preferred_language=current_user.preferred_language,
        plan=current_user.subscription.plan if current_user.subscription else "free",
    )


@router.post("/oauth/{provider}")
async def oauth_login(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    """OAuth login flow with state parameter protection."""
    valid_providers = ["google"]
    if provider not in valid_providers:
        raise HTTPException(status_code=400, detail=f"Provider must be one of: {valid_providers}")

    state = _generate_oauth_state()
    csrf_token = generate_csrf_token()

    redirect_uri = _frontend_oauth_redirect(provider, request)
    logger.info(f"OAuth start: {provider} redirect_uri={redirect_uri}")

    return {"oauth_url": _provider_auth_url(provider, state, request), "state": state, "csrf_token": csrf_token}


@router.post("/oauth/callback/{provider}")
async def oauth_callback(provider: str, callback_request: OAuthCallbackRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """OAuth callback handler with state validation."""
    if not _validate_oauth_state(callback_request.state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state parameter")

    redirect_uri = callback_request.redirect_uri
    if not redirect_uri:
        redirect_uri = _frontend_oauth_redirect(provider)

    if provider == "google":
        return await _handle_google_callback(callback_request.code, redirect_uri, db, request)

    return {"message": "OAuth callback processed"}


@router.get("/oauth/callback/{provider}")
async def oauth_callback_get(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    """OAuth callback handler for GET requests (direct redirect from provider)."""
    if provider != "google":
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    if not _validate_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state parameter")

    redirect_uri = request.query_params.get("redirect_uri") or _frontend_oauth_redirect(provider)

    return await _handle_google_callback(code, redirect_uri, db, request)


@router.post("/2fa/setup")
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Setup TOTP 2FA."""
    secret = AuthService.generate_totp_secret()
    uri = AuthService.get_totp_uri(secret, current_user.email)

    tfa = await db.execute(
        select(TwoFactorAuth).where(TwoFactorAuth.user_id == current_user.id)
    )
    tfa_record = tfa.scalar_one_or_none()

    backup_codes = AuthService.generate_backup_codes()

    if tfa_record:
        tfa_record.secret = secret
        tfa_record.is_enabled = False
        tfa_record.backup_codes = ",".join(backup_codes)
    else:
        tfa_record = TwoFactorAuth(
            user_id=current_user.id,
            secret=secret,
            method="totp",
            backup_codes=",".join(backup_codes),
        )
        db.add(tfa_record)

    await db.commit()

    import base64 as b64_module
    qr_png_base64 = None
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf)
        qr_png_base64 = b64_module.b64encode(buf.getvalue()).decode()
    except ModuleNotFoundError:
        logger.warning("Pillow is unavailable; returning TOTP setup data without QR image")

    return {
        "secret": secret,
        "uri": uri,
        "backup_codes": backup_codes,
        "qr_code_data": f"data:image/png;base64,{qr_png_base64}" if qr_png_base64 else None,
        "note": "Scan QR code with your authenticator app. Store backup codes securely.",
    }


class Verify2FARequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=10)


@router.post("/2fa/verify")
async def verify_2fa(
    verify_req: Verify2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify and enable 2FA."""
    tfa = await db.execute(
        select(TwoFactorAuth).where(TwoFactorAuth.user_id == current_user.id)
    )
    tfa_record = tfa.scalar_one_or_none()

    if not tfa_record:
        raise HTTPException(status_code=400, detail="2FA not set up. First call /2fa/setup")

    if not AuthService.verify_totp_code(tfa_record.secret, verify_req.code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    tfa_record.is_enabled = True
    await db.commit()
    return {"message": "2FA enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disable 2FA."""
    tfa = await db.execute(
        select(TwoFactorAuth).where(TwoFactorAuth.user_id == current_user.id)
    )
    tfa_record = tfa.scalar_one_or_none()

    if tfa_record:
        tfa_record.is_enabled = False
        await db.commit()

    return {"message": "2FA disabled"}


@router.get("/me/owner-status")
async def get_owner_status(current_user: User = Depends(get_current_user)):
    """Check if current user is the configured platform owner or admin."""
    is_owner = settings.is_owner_email(current_user.email)
    return {
        "is_owner": is_owner,
        "is_admin": current_user.is_admin,
        "owner_email": current_user.email if is_owner else None,
    }


@router.get("/owner/setup/status")
async def owner_setup_status(email: EmailStr, db: AsyncSession = Depends(get_db)):
    """Read current owner setup state for owner login bootstrap."""
    owner_email = email.lower().strip()
    if not settings.is_owner_email(owner_email):
        raise HTTPException(status_code=403, detail="Owner access required")

    settings_row = await _get_or_create_owner_settings(db, owner_email)
    password_configured = bool(settings_row.password_hash)
    totp_configured = bool(settings_row.totp_secret_encrypted and settings_row.totp_enabled)
    owner_setup_required = not password_configured and not totp_configured

    setup_token = None
    if owner_setup_required:
        setup_token = secrets.token_urlsafe(32)
        _store_owner_setup_token(setup_token, owner_email)

    return {
        "owner_setup_required": owner_setup_required,
        "password_configured": password_configured,
        "totp_configured": totp_configured,
        "setup_token": setup_token,
    }


@router.post("/owner/setup/finish")
async def owner_setup_finish(payload: OwnerSetupFinishRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Finish first-time owner setup and sign owner in immediately."""
    owner_email = payload.email.lower().strip()
    if not settings.is_owner_email(owner_email):
        raise HTTPException(status_code=403, detail="Owner access required")

    if not _consume_owner_setup_token(payload.setup_token, owner_email):
        raise HTTPException(status_code=400, detail="Invalid or expired owner setup token")

    settings_row = await _get_or_create_owner_settings(db, owner_email)
    if settings_row.password_hash:
        raise HTTPException(status_code=409, detail="Owner setup already completed")

    if payload.enable_totp:
        if not payload.totp_secret or not payload.totp_code:
            raise HTTPException(status_code=400, detail="TOTP secret and code are required when enabling TOTP")
        if not AuthService.verify_totp_code(payload.totp_secret, payload.totp_code):
            raise HTTPException(status_code=400, detail="Invalid TOTP code")
        settings_row.totp_secret_encrypted = _encrypt_owner_secret(payload.totp_secret)
        settings_row.totp_enabled = True
    else:
        settings_row.totp_secret_encrypted = None
        settings_row.totp_enabled = False

    settings_row.password_hash = AuthService.hash_password(payload.password)
    settings_row.setup_completed = True

    result = await db.execute(
        select(User)
        .where(User.email == owner_email)
        .options(selectinload(User.subscription))
    )
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=owner_email,
            password_hash=settings_row.password_hash,
            display_name="Owner",
            is_admin=True,
            is_approved=True,
            is_active=True,
            is_banned=False,
            email_verified=True,
        )
        db.add(user)
        await db.flush()
    else:
        user.password_hash = settings_row.password_hash
        user.is_admin = True
        user.is_approved = True
        user.is_active = True
        user.is_banned = False
        user.email_verified = True

    response = await _issue_login_response(
        db=db,
        request=request,
        user=user,
        plan=user.subscription.plan if user.subscription else "free",
    )
    return response


@router.post("/owner/setup/totp-bootstrap")
async def owner_setup_totp_bootstrap(payload: OwnerTotpBootstrapRequest):
    """Generate owner TOTP secret + URI + QR for first-time setup."""
    owner_email = payload.email.lower().strip()
    if not settings.is_owner_email(owner_email):
        raise HTTPException(status_code=403, detail="Owner access required")
    if not _is_owner_setup_token_valid(payload.setup_token, owner_email):
        raise HTTPException(status_code=400, detail="Invalid or expired owner setup token")

    secret = AuthService.generate_totp_secret()
    uri = AuthService.get_totp_uri(secret, owner_email)

    qr_png_base64 = None
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf)
        qr_png_base64 = base64.b64encode(buf.getvalue()).decode()
    except ModuleNotFoundError:
        logger.warning("Pillow unavailable; owner setup QR image omitted")

    return {
        "secret": secret,
        "uri": uri,
        "qr_code_data": f"data:image/png;base64,{qr_png_base64}" if qr_png_base64 else None,
    }


@router.post("/owner/password-reset/request")
async def owner_password_reset_request(payload: OwnerPasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """Start owner password reset flow via email or dev terminal code."""
    owner_email = payload.email.lower().strip()
    if not settings.is_owner_email(owner_email):
        return {"message": "If owner account exists, reset instructions have been sent"}

    settings_row = await _get_or_create_owner_settings(db, owner_email)
    reset_token = secrets.token_urlsafe(24)
    settings_row.reset_token = reset_token
    settings_row.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.commit()

    sent_by_email = False
    if settings.SMTP_HOST and settings.SMTP_USER:
        try:
            from app.services.email_service import EmailService
            email_service = EmailService()
            await email_service.send_password_reset(owner_email, reset_token)
            sent_by_email = True
        except Exception as e:
            logger.warning(f"Owner reset email failed, falling back to dev log: {e}")

    if not sent_by_email:
        logger.warning(f"[DEV MODE] Owner password reset token for {owner_email}: {reset_token}")

    return {
        "message": "If owner account exists, reset instructions have been sent",
        "dev_mode": not sent_by_email,
    }


@router.post("/owner/password-reset/confirm")
async def owner_password_reset_confirm(payload: OwnerPasswordResetConfirmRequest, db: AsyncSession = Depends(get_db)):
    """Confirm owner password reset with reset token/code."""
    owner_email = payload.email.lower().strip()
    if not settings.is_owner_email(owner_email):
        raise HTTPException(status_code=403, detail="Owner access required")

    PasswordValidator.validate(payload.new_password)

    settings_row = await _get_or_create_owner_settings(db, owner_email)
    if not settings_row.reset_token or settings_row.reset_token != payload.token:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    if not settings_row.reset_token_expires_at or settings_row.reset_token_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token expired")

    settings_row.password_hash = AuthService.hash_password(payload.new_password)
    settings_row.setup_completed = True
    settings_row.reset_token = None
    settings_row.reset_token_expires_at = None

    result = await db.execute(select(User).where(User.email == owner_email))
    owner_user = result.scalar_one_or_none()
    if owner_user:
        owner_user.password_hash = settings_row.password_hash
        owner_user.is_admin = True
        owner_user.is_active = True
        owner_user.is_approved = True
        owner_user.is_banned = False

    if owner_user:
        await AuthService.invalidate_all_sessions(db, owner_user.id)

    await db.commit()
    return {"message": "Owner password reset successfully"}


@router.get("/csrf-token")
async def get_csrf_token(response: Response):
    """Get a CSRF token for state-changing requests."""
    csrf_token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,  # Accessible by frontend JS
        secure=settings.HTTPS_ONLY,
        samesite="strict",
        max_age=3600,
        path="/",
    )
    return {"csrf_token": csrf_token}


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=128)
    new_password: str = Field(..., min_length=12, max_length=128)


@router.post("/forgot-password")
async def forgot_password(request: Request, payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request password reset token."""
    email = InputSanitizer.sanitize_text(payload.email.lower().strip())
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return {"message": "If an account exists, a reset link will be sent"}

    reset_token = secrets.token_urlsafe(32)
    user.email_verification_token = reset_token
    _password_reset_tokens[reset_token] = {
        "user_id": user.id,
        "created_at": datetime.now(timezone.utc),
    }
    await db.commit()

    if settings.SMTP_HOST and settings.SMTP_USER:
        try:
            from app.services.email_service import EmailService
            email_service = EmailService()
            await email_service.send_password_reset(user.email, reset_token)
        except Exception as e:
            logger.warning(f"Failed to send password reset email: {e}")

    return {"message": "If an account exists, a reset link will be sent"}


@router.post("/reset-password")
async def reset_password(request: Request, reset_req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token."""
    PasswordValidator.validate(reset_req.new_password)

    result = await db.execute(
        select(User).where(User.email_verification_token == reset_req.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    token_meta = _password_reset_tokens.get(reset_req.token)
    if not token_meta or token_meta.get("user_id") != user.id:
        _password_reset_tokens.pop(reset_req.token, None)
        user.email_verification_token = None
        await db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    created_at = token_meta.get("created_at")
    if not created_at or (datetime.now(timezone.utc) - created_at).total_seconds() > PASSWORD_RESET_TOKEN_TTL_SECONDS:
        _password_reset_tokens.pop(reset_req.token, None)
        user.email_verification_token = None
        await db.commit()
        raise HTTPException(status_code=400, detail="Reset token expired")

    _password_reset_tokens.pop(reset_req.token, None)
    user.password_hash = AuthService.hash_password(reset_req.new_password)
    user.email_verification_token = None
    await AuthService.invalidate_all_sessions(db, user.id)
    await db.commit()

    return {"message": "Password reset successfully"}


# ===================================================================
# PASSKEY (WebAuthn) AUTHENTICATION
# ===================================================================

class RegisterPasskeyBeginRequest(BaseModel):
    device_name: Optional[str] = Field(default=None, max_length=255)


@router.post("/passkey/register/begin")
async def passkey_register_begin(
    body: RegisterPasskeyBeginRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start WebAuthn passkey registration. Returns challenge options for the browser."""
    if not settings.ENABLE_PASSKEYS:
        raise HTTPException(status_code=403, detail="Passkeys are disabled")

    try:
        from webauthn import generate_registration_options
        from webauthn.helpers.structs import (
            AuthenticatorSelectionCriteria,
            UserVerificationRequirement,
            ResidentKeyRequirement,
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="WebAuthn library not installed. Run: pip install webauthn")

    challenge = secrets.token_bytes(32)
    rp_id = _derive_rp_id(request)
    expected_origin = _derive_frontend_origin(request)

    registration_options = generate_registration_options(
        rp_id=rp_id,
        rp_name=settings.APP_NAME,
        user_id=str(current_user.id).encode(),
        user_name=current_user.email,
        user_display_name=current_user.display_name or current_user.email,
        attestation="none",
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        challenge=challenge,
    )

    _webauthn_challenges[str(current_user.id)] = {
        "challenge": base64.urlsafe_b64encode(challenge).decode().rstrip("="),
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=WEBAUTHN_CHALLENGE_TTL_SECONDS),
        "type": "registration",
        "device_name": body.device_name or "Default Device",
        "rp_id": rp_id,
        "origin": expected_origin,
    }

    public_key = {
        "challenge": base64.urlsafe_b64encode(registration_options.challenge).decode().rstrip("="),
        "rp": {"id": registration_options.rp.id, "name": registration_options.rp.name},
        "user": {
            "id": base64.urlsafe_b64encode(registration_options.user.id).decode().rstrip("="),
            "name": registration_options.user.name,
            "displayName": registration_options.user.display_name,
        },
        "pubKeyCredParams": [
            {"type": "public-key", "alg": -7},  # ES256
            {"type": "public-key", "alg": -257},  # RS256
        ],
        "timeout": 60000,
        "attestation": "none",
        "authenticatorSelection": {
            "residentKey": "preferred",
            "userVerification": "preferred",
        },
    }

    return {"publicKey": public_key, "rp_id": rp_id}


class RegisterPasskeyCompleteRequest(BaseModel):
    credential_id: str
    raw_id: str
    response: Dict[str, Any]
    type: str = "public-key"
    client_extension_results: Optional[Dict[str, Any]] = None


@router.post("/passkey/register/complete")
async def passkey_register_complete(
    body: RegisterPasskeyCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify WebAuthn registration response and save the passkey."""
    stored = _webauthn_challenges.get(str(current_user.id))
    if not stored or stored.get("type") != "registration":
        raise HTTPException(status_code=400, detail="No pending registration challenge. Start registration again.")

    if datetime.now(timezone.utc) > stored["expires_at"]:
        _webauthn_challenges.pop(str(current_user.id), None)
        raise HTTPException(status_code=400, detail="Registration challenge expired. Try again.")

    try:
        from webauthn import verify_registration_response
        from webauthn.helpers.structs import RegistrationCredential
    except ImportError:
        raise HTTPException(status_code=500, detail="WebAuthn library not installed")

    expected_challenge = base64.urlsafe_b64decode(stored["challenge"] + "===")

    try:
        verification = verify_registration_response(
            credential=RegistrationCredential(
                id=body.credential_id,
                raw_id=body.raw_id.encode() if isinstance(body.raw_id, str) else body.raw_id,
                response=body.response,
                type=body.type,
            ),
            expected_challenge=expected_challenge,
            expected_rp_id=stored.get("rp_id") or _derive_rp_id(),
            expected_origin=stored.get("origin") or _derive_frontend_origin(),
        )
    except Exception as e:
        logger.warning(f"WebAuthn registration verification failed: {e}")
        raise HTTPException(status_code=400, detail="Passkey registration failed verification")

    _webauthn_challenges.pop(str(current_user.id), None)

    transports = body.response.get("transports") or []
    cred_id = body.credential_id

    existing = await db.execute(select(Passkey).where(Passkey.credential_id == cred_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This passkey is already registered")

    public_key_b64 = base64.urlsafe_b64encode(verification.credential.public_key).decode()
    sign_count = verification.credential.sign_count or 0

    passkey = Passkey(
        user_id=current_user.id,
        credential_id=cred_id,
        public_key=public_key_b64,
        counter=sign_count,
        device_name=stored.get("device_name") or "Passkey",
        transports=",".join(transports) if transports else None,
    )
    db.add(passkey)
    await db.commit()

    return {
        "message": "Passkey registered successfully",
        "passkey_id": str(passkey.id),
        "credential_id": cred_id,
    }


@router.post("/passkey/login/begin")
async def passkey_login_begin(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Start WebAuthn passkey authentication. Returns challenge options for the browser."""
    if not settings.ENABLE_PASSKEYS:
        raise HTTPException(status_code=403, detail="Passkeys are disabled")

    try:
        from webauthn import generate_authentication_options
    except ImportError:
        raise HTTPException(status_code=500, detail="WebAuthn library not installed")

    challenge = secrets.token_bytes(32)
    rp_id = _derive_rp_id(request)
    expected_origin = _derive_frontend_origin(request)

    auth_options = generate_authentication_options(
        rp_id=rp_id,
        challenge=challenge,
    )

    session_id = str(uuid.uuid4())
    _webauthn_challenges[session_id] = {
        "challenge": base64.urlsafe_b64encode(challenge).decode().rstrip("="),
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=WEBAUTHN_CHALLENGE_TTL_SECONDS),
        "type": "authentication",
        "rp_id": rp_id,
        "origin": expected_origin,
    }

    response = JSONResponse(content={
        "publicKey": {
            "challenge": base64.urlsafe_b64encode(auth_options.challenge).decode().rstrip("="),
            "timeout": 60000,
            "rpId": rp_id,
            "userVerification": "preferred",
        },
        "rp_id": rp_id,
    })
    response.set_cookie(
        key="passkey_challenge_id",
        value=session_id,
        httponly=True,
        secure=settings.HTTPS_ONLY,
        samesite="strict",
        max_age=WEBAUTHN_CHALLENGE_TTL_SECONDS,
        path="/",
    )
    return response


class PasskeyLoginCompleteRequest(BaseModel):
    id: str
    raw_id: str
    response: Dict[str, Any]
    type: str = "public-key"
    client_extension_results: Optional[Dict[str, Any]] = None


@router.post("/passkey/login/complete")
async def passkey_login_complete(
    body: PasskeyLoginCompleteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Verify WebAuthn authentication response and log the user in (one-tap login)."""
    session_id = request.cookies.get("passkey_challenge_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing passkey challenge cookie")
    stored = _webauthn_challenges.get(session_id)
    if not stored or stored.get("type") != "authentication":
        raise HTTPException(status_code=400, detail="No pending authentication challenge. Start authentication again.")

    if datetime.now(timezone.utc) > stored["expires_at"]:
        _webauthn_challenges.pop(session_id, None)
        raise HTTPException(status_code=400, detail="Authentication challenge expired. Try again.")

    result = await db.execute(
        select(Passkey)
        .where(Passkey.credential_id == body.id)
        .options(selectinload(Passkey.user).selectinload(User.two_factor_auth), selectinload(Passkey.user).selectinload(User.subscription))
    )
    passkey = result.scalar_one_or_none()

    if not passkey:
        raise HTTPException(status_code=404, detail="Passkey not found. Please register a passkey first.")

    if not passkey.user or not passkey.user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    if passkey.user.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned. Contact support.")

    try:
        from webauthn import verify_authentication_response
        from webauthn.helpers.structs import AuthenticationCredential
    except ImportError:
        raise HTTPException(status_code=500, detail="WebAuthn library not installed")

    expected_challenge = base64.urlsafe_b64decode(stored["challenge"] + "===")

    try:
        public_key_bytes = base64.urlsafe_b64decode(passkey.public_key + "===")
        verification = verify_authentication_response(
            credential=AuthenticationCredential(
                id=body.id,
                raw_id=body.raw_id.encode() if isinstance(body.raw_id, str) else body.raw_id,
                response=body.response,
                type=body.type,
            ),
            expected_challenge=expected_challenge,
            expected_rp_id=stored.get("rp_id") or _derive_rp_id(),
            expected_origin=stored.get("origin") or _derive_frontend_origin(),
            credential_public_key=public_key_bytes,
            credential_current_sign_count=passkey.counter,
        )
    except Exception as e:
        logger.warning(f"WebAuthn authentication failed: {e}")
        raise HTTPException(status_code=400, detail="Passkey authentication failed")

    _webauthn_challenges.pop(session_id, None)

    passkey.counter = verification.new_sign_count
    passkey.last_used_at = datetime.now(timezone.utc)

    user = passkey.user
    if user.two_factor_auth and user.two_factor_auth.is_enabled:
        await db.commit()
        return JSONResponse(
            status_code=200,
            content={"requires_2fa": True, "user_id": str(user.id), "passkey_id": str(passkey.id)},
        )

    await AuthService.invalidate_all_sessions(db, user.id)
    access_token = AuthService.create_access_token(str(user.id), user.email, user.is_admin)
    refresh_token = AuthService.create_refresh_token(str(user.id))

    await AuthService.create_session(db, user.id, refresh_token, request)

    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_ip = request.client.host if request.client else None
    await db.commit()

    csrf_token = generate_csrf_token()

    return {
        "user": UserResponse(
            id=str(user.id),
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            is_admin=user.is_admin,
            is_approved=user.is_approved,
            preferred_language=user.preferred_language,
            plan=user.subscription.plan if user.subscription else "free",
        ),
        "tokens": TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            csrf_token=csrf_token,
        ),
    }


@router.get("/passkeys")
async def list_passkeys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all passkeys for the current user."""
    result = await db.execute(
        select(Passkey).where(Passkey.user_id == current_user.id).order_by(Passkey.created_at.desc())
    )
    passkeys = result.scalars().all()
    return {
        "passkeys": [
            {
                "id": str(pk.id),
                "credential_id": pk.credential_id,
                "device_name": pk.device_name,
                "created_at": pk.created_at.isoformat() if pk.created_at else None,
                "last_used_at": pk.last_used_at.isoformat() if pk.last_used_at else None,
            }
            for pk in passkeys
        ]
    }


@router.delete("/passkey/{credential_id}")
async def delete_passkey(
    credential_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a passkey by credential ID."""
    result = await db.execute(
        select(Passkey).where(
            Passkey.credential_id == credential_id,
            Passkey.user_id == current_user.id,
        )
    )
    passkey = result.scalar_one_or_none()
    if not passkey:
        raise HTTPException(status_code=404, detail="Passkey not found")

    await db.delete(passkey)
    await db.commit()
    return {"message": "Passkey deleted successfully"}