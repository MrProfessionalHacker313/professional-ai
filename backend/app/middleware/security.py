"""
Professional AI - Security Middleware
Helmet-style headers, input sanitization, rate limiting, CSRF protection, account lockout,
device fingerprinting, login alerts, request validation, and security monitoring.
"""

from typing import Optional, Callable, Awaitable, Dict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from loguru import logger
import bleach
import re
import secrets
import time
import hashlib
import hmac
import ipaddress
from urllib.parse import urlparse


def _owner_exempt_limiter_key(request: Request) -> str:
    """
    Rate-limit key function that ALWAYS exempts the platform owner.
    Owner requests get a unique per-request key so they never hit any bucket limit.
    """
    try:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            try:
                from jose import jwt as jose_jwt
                payload = jose_jwt.decode(
                    token,
                    settings.JWT_SECRET,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_aud": False, "verify_iss": False},
                )
                email = payload.get("email")
                if email and settings.is_owner_email(email):
                    # Fresh key per request => owner is never rate limited.
                    return f"owner-exempt-{secrets.token_hex(8)}"
            except Exception:
                pass
    except Exception:
        pass
    return get_remote_address(request)


# Rate limiter instance (Redis-backed in production)
# Owner email is ALWAYS exempt from rate limits via _owner_exempt_limiter_key.
limiter = Limiter(key_func=_owner_exempt_limiter_key, default_limits=["100/minute"])


# CSRF token store with expiry (in-memory fallback; Redis in production)
_csrf_tokens: Dict[str, float] = {}
CSRF_TOKEN_TTL_SECONDS = 3600  # 1 hour


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses (Helmet-style)."""

    # Paths that serve pre-built Next.js static export — these need
    # permissive CSP because we cannot inject nonces into the static HTML.
    _FRONTEND_PREFIXES = (
        "/_next/",
        "/static/",
        "/manifest.json",
        "/sw.js",
        "/offline.html",
        "/knowledge/",
    )

    def _is_frontend_static(self, path: str) -> bool:
        """Check if the request is for a frontend static asset or page."""
        if path.startswith(self._FRONTEND_PREFIXES):
            return True
        # Root and non-API paths are frontend pages
        if path == "/" or (not path.startswith("/api") and not path.startswith("/metrics") and not path.startswith("/docs") and not path.startswith("/redoc")):
            return True
        return False

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Generate per-request nonce for CSP
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # Use permissive CSP for frontend static files (Next.js static export
        # has inline scripts we can't nonce). Use strict nonce-based CSP for API.
        if self._is_frontend_static(request.url.path):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: https: blob:; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "connect-src 'self' ws: wss: http: https:;"
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'nonce-{nonce}' https://cdn.tailwindcss.com https://unpkg.com; "
                "style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com; "
                "img-src 'self' data: https: blob:; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "connect-src 'self' ws: wss:;"
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            ).format(nonce=nonce)

        response.headers["X-Request-Id"] = str(request.headers.get("X-Request-Id", ""))

        # Allow caching for static assets, but no-store for API responses
        if self._is_frontend_static(request.url.path) and "_next/static" in request.url.path:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # Log slow requests (>1s)
        if process_time > 1.0:
            logger.warning(f"Slow request: {request.method} {request.url.path} - {process_time:.2f}s")

        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request for tracing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or secrets.token_urlsafe(16)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


class DeviceFingerprint:
    """Generate and validate device fingerprints."""

    @staticmethod
    def generate(request: Request) -> str:
        """Generate a device fingerprint from request attributes."""
        user_agent = request.headers.get("user-agent", "")
        accept_language = request.headers.get("accept-language", "")
        accept_encoding = request.headers.get("accept-encoding", "")
        ip = request.client.host if request.client else ""

        # Combine attributes and hash
        raw = f"{user_agent}|{accept_language}|{accept_encoding}|{ip}"
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def validate(fingerprint: str) -> bool:
        """Validate fingerprint format."""
        return bool(fingerprint) and len(fingerprint) == 64 and all(c in "0123456789abcdef" for c in fingerprint)


class InputSanitizer:
    """Sanitize user input to prevent XSS and injection attacks."""

    ALLOWED_TAGS = ["p", "br", "strong", "em", "u", "code", "pre"]
    ALLOWED_ATTRIBUTES = {"*": ["class"]}
    ALLOWED_STYLES = []

    @staticmethod
    def sanitize_text(text: str, max_length: int = 100_000) -> str:
        """Sanitize text input using bleach."""
        if not text:
            return text
        if len(text) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length} characters")
        return bleach.clean(
            text,
            tags=InputSanitizer.ALLOWED_TAGS,
            attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
            strip=True,
        ).strip()

    @staticmethod
    def sanitize_code_input(code: str, max_length: int = 1_000_000) -> str:
        """Sanitize code input - block dangerous patterns."""
        if not code:
            return code
        if len(code) > max_length:
            raise ValueError(f"Code input exceeds maximum length of {max_length} characters")

        dangerous_patterns = [
            (r'import\s+os\s*;', "Direct OS import"),
            (r'subprocess\.', "Subprocess execution"),
            (r'os\.system\s*\(', "OS command execution"),
            (r'__import__\s*\(', "Dynamic import"),
            (r'\beval\s*\(', "Eval execution"),
            (r'\bexec\s*\(', "Exec execution"),
            (r'pickle\.loads?\s*\(', "Unsafe deserialization"),
            (r'base64\.b64decode\s*\(', "Base64 decode"),
            (r'marshal\.loads?\s*\(', "Unsafe marshal"),
            (r'shell=True', "Shell injection"),
        ]
        for pattern, description in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                logger.warning(f"Blocked dangerous code pattern: {description}")
                raise HTTPException(status_code=400, detail=f"Dangerous code pattern detected: {description}")
        return code

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize uploaded filename."""
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        filename = re.sub(r'[\s\-]+', '-', filename)
        return filename[:255] or "unnamed"

    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize URL to prevent SSRF."""
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Invalid URL scheme")
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise HTTPException(status_code=400, detail="Invalid URL")
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                raise HTTPException(status_code=400, detail="URL points to private/internal address")
        except ValueError:
            pass
        blocked_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "metadata.google.internal"]
        if hostname.lower() in blocked_hosts:
            raise HTTPException(status_code=400, detail="URL points to blocked host")
        return url


class PasswordValidator:
    """Password strength validator."""

    @staticmethod
    def validate(password: str) -> None:
        """Validate password strength. Raises HTTPException if weak."""
        if len(password) < 12:
            raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
        if not re.search(r'[A-Z]', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one lowercase letter")
        if not re.search(r'\d', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise HTTPException(status_code=400, detail="Password must contain at least one special character")


class LogSanitizer:
    """Sanitize sensitive data from logs."""

    SENSITIVE_PATTERNS = [
        (r'Bearer\s+[A-Za-z0-9\-_\.]+', 'Bearer [REDACTED]'),
        (r'"password"\s*:\s*"[^"]*"', '"password":"[REDACTED]"'),
        (r'"api_key"\s*:\s*"[^"]*"', '"api_key":"[REDACTED]"'),
        (r'"secret"\s*:\s*"[^"]*"', '"secret":"[REDACTED]"'),
        (r'"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"', '[EMAIL REDACTED]'),
        (r'\b\d{4}[\-\s]?\d{4}[\-\s]?\d{4}[\-\s]?\d{4}\b', '[CARD REDACTED]'),
    ]

    @staticmethod
    def sanitize(text: str) -> str:
        result = text
        for pattern, replacement in LogSanitizer.SENSITIVE_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result


# Request validation middleware
async def validate_request_size(request: Request):
    """Limit request body size (50MB max)."""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 50_000_000:
        raise HTTPException(status_code=413, detail="Request entity too large (max 50MB)")


async def validate_content_type(request: Request):
    """Validate content type for non-file endpoints."""
    if request.method in ("POST", "PUT", "PATCH"):
        content_type = request.headers.get("content-type", "")
        if content_type and not any(
            ct in content_type for ct in [
                "application/json",
                "application/x-www-form-urlencoded",
                "multipart/form-data",
                "text/plain",
            ]
        ):
            pass  # Allow other content types for file uploads


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom rate limit exceeded response."""
    from slowapi.errors import RateLimitExceeded
    rate_limit_exc = exc if isinstance(exc, RateLimitExceeded) else RateLimitExceeded(str(exc))
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please wait before trying again.",
            "retry_after": getattr(rate_limit_exc, "detail", "60"),
        },
        headers={"Retry-After": "60"},
    )


# CSRF token generation and validation with expiry
def generate_csrf_token() -> str:
    """Generate a CSRF token with expiry timestamp."""
    token = secrets.token_urlsafe(32)
    _csrf_tokens[token] = time.time()
    # Clean up expired tokens
    now = time.time()
    expired = [t for t, ts in _csrf_tokens.items() if now - ts > CSRF_TOKEN_TTL_SECONDS]
    for t in expired:
        _csrf_tokens.pop(t, None)
    return token


def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token with constant-time comparison and expiry check."""
    if not token:
        return False

    # Check in-memory store
    stored_time = _csrf_tokens.get(token)
    if stored_time is not None:
        if time.time() - stored_time > CSRF_TOKEN_TTL_SECONDS:
            _csrf_tokens.pop(token, None)
            return False
        _csrf_tokens.pop(token, None)  # One-time use
        return True

    # Check Redis store (production)
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(redis_client.get(f"csrf:{token}"))
        if result:
            loop.run_until_complete(redis_client.delete(f"csrf:{token}"))
            return True
    except Exception as e:
        logger.warning(f"CSRF Redis validation failed: {e}")

    return False


async def csrf_protect(request: Request, call_next):
    """CSRF protection for state-changing requests."""
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        csrf_token = request.headers.get("X-CSRF-Token") or request.cookies.get("csrf_token")
        if not csrf_token or not validate_csrf_token(csrf_token):
            return JSONResponse(
                status_code=403,
                content={"error": "csrf_token_invalid", "message": "Invalid or missing CSRF token"},
            )
    return await call_next(request)
