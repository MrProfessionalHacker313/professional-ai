"""
Professional AI - Authentication Service
Handles JWT tokens, OAuth, 2FA, passkeys, password hashing, session management,
account lockout, device fingerprinting, login alerts, and suspicious activity detection.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid
import hashlib
import secrets
import asyncio
import ipaddress

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.database import get_db
from app.models.user import User, OAuthAccount, TwoFactorAuth, Passkey, Session, LoginAttempt
from app.middleware.security import InputSanitizer, PasswordValidator
from app.services.unlimited_mode import subscription_access
from loguru import logger

# Password hashing context with Argon2 support (fallback to bcrypt)
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto", bcrypt__rounds=12)
security_scheme = HTTPBearer(auto_error=False)


class AuthService:
    """Core authentication service."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: str, email: str, is_admin: bool = False) -> str:
        """Create short-lived JWT access token (15 min) with all security claims."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_id,
            "email": email,
            "admin": is_admin,
            "type": "access",
            "exp": expire,
            "iat": now,
            "nbf": now,
            "jti": str(uuid.uuid4()),
            "iss": "professional-ai",
            "aud": "professional-ai-frontend",
        }
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Create long-lived refresh token (7 days) with all security claims."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        token = str(uuid.uuid4())
        to_encode = {
            "sub": user_id,
            "type": "refresh",
            "token": token,
            "exp": expire,
            "iat": now,
            "nbf": now,
            "jti": str(uuid.uuid4()),
            "iss": "professional-ai",
            "aud": "professional-ai-frontend",
        }
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        """Hash refresh token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and validate JWT token with issuer and audience validation."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                issuer="professional-ai",
                audience="professional-ai-frontend",
            )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def generate_totp_secret() -> str:
        """Generate TOTP secret for 2FA."""
        import pyotp
        return pyotp.random_base32()

    @staticmethod
    def get_totp_uri(secret: str, email: str) -> str:
        """Generate TOTP provisioning URI for authenticator apps."""
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name="Professional AI")

    @staticmethod
    def verify_totp_code(secret: str, code: str) -> bool:
        """Verify TOTP code with window tolerance."""
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)

    @staticmethod
    def generate_backup_codes(count: int = 8) -> list:
        """Generate 2FA backup codes (8 by default as per security requirements)."""
        return [secrets.token_hex(4).upper() for _ in range(count)]

    @staticmethod
    async def send_login_alert(user: User, request: Request):
        """Send login alert email to user."""
        if not settings.ALERT_EMAIL_TO or not settings.SMTP_HOST:
            return
        try:
            from app.services.email_service import EmailService
            email_service = EmailService()
            await email_service.send_login_alert(
                to_email=user.email,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "unknown"),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            logger.warning(f"Failed to send login alert: {e}")

    @staticmethod
    async def record_login_attempt(db: AsyncSession, email: str, user: Optional[User], success: bool, request: Request, failure_reason: Optional[str] = None):
        """Record login attempt for audit and lockout tracking."""
        attempt = LoginAttempt(
            user_id=user.id if user else None,
            email=email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=success,
            failure_reason=failure_reason,
        )
        db.add(attempt)
        await db.commit()

        # Detect suspicious activity
        if not success and settings.ALERT_ON_BRUTE_FORCE:
            await AuthService._detect_brute_force(db, email, request)

    @staticmethod
    async def _detect_brute_force(db: AsyncSession, email: str, request: Request):
        """Detect brute force attacks and send alerts."""
        try:
            from app.models.audit import SecurityEvent
            from datetime import datetime, timezone, timedelta
            
            # Check failed attempts in last 10 minutes
            ten_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
            result = await db.execute(
                select(func.count(LoginAttempt.id)).where(
                    and_(
                        LoginAttempt.email == email,
                        LoginAttempt.success == False,
                        LoginAttempt.attempted_at >= ten_minutes_ago
                    )
                )
            )
            failed_count = result.scalar() or 0
            
            if failed_count >= 10:
                ip = request.client.host if request.client else "unknown"
                event = SecurityEvent(
                    event_type="brute_force_detected",
                    severity="high",
                    ip_address=ip,
                    details=f"Multiple failed login attempts for {email}: {failed_count} in 10 minutes",
                )
                db.add(event)
                await db.commit()
                
                logger.warning(f"BRUTE FORCE DETECTED: {failed_count} failed attempts for {email} from {ip}")
                
                # Send alert email to owner
                if settings.ALERT_EMAIL_TO and settings.SMTP_HOST:
                    try:
                        from app.services.email_service import EmailService
                        email_service = EmailService()
                        await email_service.send_security_alert(
                            to_email=settings.ALERT_EMAIL_TO,
                            subject="SECURITY ALERT: Brute Force Attack Detected",
                            body=f"Multiple failed login attempts detected for {email}.\n\n"
                                 f"Failed attempts: {failed_count}\n"
                                 f"IP address: {ip}\n"
                                 f"Time: {datetime.now(timezone.utc).isoformat()}\n\n"
                                 f"Action taken: Account may be locked after {settings.MAX_LOGIN_ATTEMPTS} attempts."
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send brute force alert: {e}")
        except Exception as e:
            logger.debug(f"Brute force detection failed: {e}")

    @staticmethod
    async def check_account_lockout(db: AsyncSession, email: str) -> Optional[int]:
        """Check if account is locked due to failed attempts. Returns remaining lockout seconds or None."""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None

        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = (user.locked_until - datetime.now(timezone.utc)).total_seconds()
            return int(remaining)
        return None

    @staticmethod
    async def increment_failed_login(db: AsyncSession, user: User):
        """Increment failed login counter and lock account if threshold reached."""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            user.failed_login_attempts = 0
        await db.commit()

    @staticmethod
    async def reset_failed_login(db: AsyncSession, user: User):
        """Reset failed login counter on successful login."""
        user.failed_login_attempts = 0
        user.locked_until = None
        await db.commit()

    @staticmethod
    async def create_session(db: AsyncSession, user_id: uuid.UUID, refresh_token: str, request: Request) -> Session:
        """Create a new session with device fingerprinting."""
        session = Session(
            user_id=user_id,
            refresh_token_hash=AuthService.hash_refresh_token(refresh_token),
            device_fingerprint=getattr(request.state, "device_fingerprint", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def invalidate_all_sessions(db: AsyncSession, user_id: uuid.UUID):
        """Invalidate all existing sessions for a user."""
        result = await db.execute(
            select(Session).where(Session.user_id == user_id, Session.is_valid == True)
        )
        sessions = result.scalars().all()
        for session in sessions:
            session.is_valid = False
        await db.commit()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token = credentials.credentials
    payload = AuthService.decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Validate user_id is a proper UUID BEFORE querying —
    # an invalid UUID previously caused a raw ValueError → 500.
    try:
        user_uuid = uuid.UUID(str(user_id))
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload — please login again",
        )

    # Fetch user from database
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.subscription),
            selectinload(User.two_factor_auth),
            selectinload(User.passkeys),
        )
        .where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found — please login again",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    if user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is banned. Contact support.",
        )

    # Check if account is locked
    lockout_remaining = await AuthService.check_account_lockout(db, user.email)
    if lockout_remaining is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked. Try again in {lockout_remaining // 60} minutes.",
            headers={"Retry-After": str(lockout_remaining)},
        )

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to verify the current user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_owner(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to verify the current user is the configured owner account."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )

    if not settings.is_owner_email(current_user.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required",
        )

    return current_user


async def get_free_user_limit(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """Check if free user has exceeded daily code generation limit (3/day)."""
    from app.models.usage import CodeGenerationCounter
    from sqlalchemy import func

    # Check if user has an active UNLIMITED subscription (PRO/MAX/BUSINESS/ENTERPRISE)
    if user.subscription:
        decision = subscription_access.check_access(
            user_id=str(user.id),
            plan=user.subscription.plan,
            status=user.subscription.status,
        )
        if decision.unlimited:
            return True  # Paid users have UNLIMITED access

    # OWNER BYPASS: The platform owner always has unlimited access - no limits ever.
    if settings.is_owner_email(user.email):
        return True

    # Check free user daily limit
    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(CodeGenerationCounter).where(
            and_(
                CodeGenerationCounter.user_id == user.id,
                CodeGenerationCounter.date == today,
            )
        )
    )
    counter = result.scalar_one_or_none()

    if counter and counter.count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Free daily limit finished. Upgrade to PRO for unlimited power.",
        )

    return True
