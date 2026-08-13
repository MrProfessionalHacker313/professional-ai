"""
Professional AI - Main Application Entry Point
FastAPI application with all routes, middleware, and startup/shutdown events.
SECURITY HARDENED: Debug mode guard, metrics auth, security headers, CORS strictness,
WAF, session timeout, HTTPS enforcement, automatic security scanning.
"""

from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from loguru import logger
import sys
import os
import time
import asyncio
import base64
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.database import init_db, close_db, check_db_connection
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RequestIdMiddleware,
    InputSanitizer,          # note: agar yeh yahan use nahi hota to isko bhi hata sakte hain
    limiter,
    rate_limit_exceeded_handler,
    LogSanitizer,
    validate_csrf_token,
)
from app.middleware.waf import WAFMiddleware
from app.middleware.session import SessionTimeoutMiddleware
from app.middleware.compression import CompressionMiddleware
from app.routes import auth, chat, admin, payments, credits, advanced_features, next_gen_features, offline, vault, media, auto_edit, blog, chat_history, prompt_forge, ai_dashboard, modules
from app.services.ai_service import ai_service
from app.services.ai_router import ai_router
from app.services.startup_seeder import run_startup_tasks
from app.services.cache_service import cache_service

# ===================================================================
# Frontend static serving (SABSE PEHLE DEFINE KARO - Bug 2 fix)
# ===================================================================
# Frontend static serving - check multiple possible locations
_app_dir = os.path.dirname(os.path.dirname(__file__))
_candidate_frontend_dirs = [
    os.path.join(_app_dir, "frontend", "out"),          # /app/frontend/out (Docker)
    os.path.join(_app_dir, "app", "frontend", "out"),   # /app/app/frontend/out (fallback)
    os.path.join(os.getcwd(), "frontend", "out"),       # cwd/frontend/out
]
frontend_out_dir = next((d for d in _candidate_frontend_dirs if os.path.exists(d)), _candidate_frontend_dirs[0])
frontend_serving_enabled = os.path.exists(frontend_out_dir) and settings.ENVIRONMENT != "development"


def _frontend_file_response(file_path: str) -> FileResponse:
    """Serve frontend files and disable HTML caching to prevent stale UI."""
    headers = {}
    if file_path.lower().endswith(".html"):
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
    return FileResponse(file_path, headers=headers)


# Initialize Sentry (optional)
if settings.ENVIRONMENT != "development" and os.getenv("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.loguru import LoguruIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.httpx import HttpxIntegration

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        environment=settings.ENVIRONMENT,
        release=f"professional-ai@{settings.APP_VERSION}",
        integrations=[
            LoguruIntegration(),
            SqlalchemyIntegration(),
            HttpxIntegration(),
        ],
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        send_default_pii=False,
    )
    logger.info("Sentry error tracking initialized")


# ===================================================================
# Prometheus Metrics
# ===================================================================
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)
ACTIVE_CONNECTIONS = Gauge(
    "http_active_connections",
    "Currently active HTTP connections",
)
DB_CONNECTION_POOL = Gauge(
    "db_connection_pool_size",
    "Database connection pool size",
)
AI_REQUEST_COUNT = Counter(
    "ai_requests_total",
    "Total AI provider requests",
    ["provider", "model"],
)
AI_REQUEST_DURATION = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["provider", "model"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Prometheus metrics middleware."""

    async def dispatch(self, request: Request, call_next):
        ACTIVE_CONNECTIONS.inc()
        start_time = time.time()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
            ).inc()
            ACTIVE_CONNECTIONS.dec()

        return response


# ===================================================================
# Logging Configuration
# ===================================================================

class SanitizeSink:
    """Custom log sink that sanitizes sensitive data."""

    def write(self, message: str) -> None:
        sanitized = LogSanitizer.sanitize(message)
        print(sanitized, end="")


def setup_logging():
    """Configure structured logging."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <white>{message}</white>",
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
    )
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
    )


# ===================================================================
# Application Lifecycle
# ===================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    if settings.DEBUG and settings.ENVIRONMENT == "production":
        logger.warning("DEBUG mode is enabled in production environment!")

    try:
        await init_db()
        logger.info("Database initialized")

        if not await check_db_connection():
            logger.warning("Database connection check failed on startup")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if settings.ENVIRONMENT == "production":
            raise

    try:
        await run_startup_tasks()
        logger.info("Startup seeder completed")
    except Exception as e:
        logger.error(f"Startup seeder failed: {e}")
        if settings.ENVIRONMENT == "production":
            raise

    try:
        from app.services.offline_engine import offline_engine
        await offline_engine.initialize()
        logger.info("Offline engine initialized")
    except Exception as e:
        logger.warning(f"Offline engine initialization failed: {e}")

    # Background security scan so health checks are not blocked.
    if settings.ENVIRONMENT == "production":
        async def run_startup_security_scan() -> None:
            try:
                from app.services.security_scanner import security_scanner
                scan_results = await security_scanner.run_full_scan()
                if scan_results.get("vulnerabilities"):
                    logger.warning(f"Security scan found {len(scan_results['vulnerabilities'])} vulnerabilities")
                else:
                    logger.info("Startup security scan completed")
            except Exception as e:
                logger.warning(f"Startup security scan failed: {e}")

        asyncio.create_task(run_startup_security_scan())

    try:
        await cache_service.connect()
        logger.info("Redis cache connected")
    except Exception as e:
        logger.warning(f"Redis cache connection failed: {e}")

    try:
        await ai_service.start_health_monitor()
        logger.info("AI provider monitors started")
    except Exception as e:
        logger.warning(f"Failed to start AI provider monitors: {e}")

    if settings.MEDIA_ENGINE_ENABLED:
        try:
            from app.services.media.bullmq_queue import media_queue_service
            await media_queue_service.start()
            logger.info("Media engine queue started")
        except Exception as e:
            logger.warning(f"Media engine queue start failed: {e}")

    yield

    try:
        await cache_service.disconnect()
    except Exception:
        pass

    try:
        await close_db()
    except Exception:
        pass

    try:
        from app.services.offline_engine import offline_engine
        await offline_engine.shutdown()
    except Exception:
        pass

    try:
        await ai_service.stop_health_monitor()
    except Exception:
        pass

    logger.info("Application shutdown complete")


# ===================================================================
# Create FastAPI Application
# ===================================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional AI - World's most powerful all-in-one AI assistant",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ===================================================================
# Middleware Stack (order matters - first added = outermost)
# ===================================================================

# 1. CORS - SABSE PEHLE (outermost) - Bug 3 fix
# allow_origin_regex handles random Cloudflare tunnel URLs (trycloudflare.com)
# Cloudflare tunnel URLs are random each time, so we use a regex to match any subdomain
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://.*\.trycloudflare\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "X-Request-Id"],
    expose_headers=["X-Request-Id", "Retry-After"],
    max_age=86400,
)

# 2. HTTPS redirect (if enabled)
if settings.HTTPS_ONLY and settings.ENVIRONMENT not in ("development", "test"):
    class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            host = (request.url.hostname or "").lower()
            is_loopback = host in {"127.0.0.1", "localhost"}
            forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
            if request.url.scheme == "http" and not is_loopback and forwarded_proto != "https":
                https_url = str(request.url).replace("http://", "https://", 1)
                return RedirectResponse(url=https_url, status_code=301)
            return await call_next(request)

    app.add_middleware(HTTPSRedirectMiddleware)

# 3. WAF - blocks SQL injection, XSS, path traversal, SSRF, command injection
if settings.WAF_ENABLED:
    app.add_middleware(WAFMiddleware)

# 4. Request ID tracking
app.add_middleware(RequestIdMiddleware)

# 5. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 6. Session timeout enforcement — disabled: users stay logged in until explicit logout
# app.add_middleware(SessionTimeoutMiddleware)

# 7. Compression (Brotli/Gzip) - reduces response size by 60-80%
app.add_middleware(CompressionMiddleware, minimum_size=1024)

# 8. Prometheus metrics
app.add_middleware(PrometheusMiddleware)

# 9. Custom CSRF protection
class CSRFProtectMiddleware(BaseHTTPMiddleware):
    # Endpoints that use signed payloads / external callbacks - exempt from CSRF
    CSRF_EXEMPT_PATHS = (
        "/api/payments/stripe/webhook",
        "/api/payments/paypal/webhook",
        "/api/payments/jazzcash/webhook",
        "/api/payments/easypaisa/webhook",
        "/api/payments/sadapay/webhook",
        "/api/payments/nayapay/webhook",
        "/api/auth/oauth/",
        "/api/auth/owner/",
        "/api/auth/refresh",
    )

    @staticmethod
    def _has_valid_bearer(request: Request) -> bool:
        """
        A valid Bearer access token is already protected against CSRF
        (browsers do not auto-send Authorization headers). If the token
        decodes successfully, we SKIP the CSRF check entirely so a valid
        logged-in session NEVER gets a 403.
        """
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return False
        token = auth.split(" ", 1)[1] if " " in auth else ""
        if not token:
            return False
        try:
            from jose import jwt as jose_jwt
            payload = jose_jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_aud": False, "verify_iss": False},
            )
            return payload.get("type") == "access" and bool(payload.get("sub"))
        except Exception:
            return False

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in self.CSRF_EXEMPT_PATHS):
            return await call_next(request)

        if request.url.path == "/api/auth/csrf-token" and request.method == "GET":
            return await call_next(request)

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # A valid logged-in session (Bearer access token) is NEVER blocked by CSRF.
            if self._has_valid_bearer(request):
                return await call_next(request)

            csrf_token = request.headers.get("X-CSRF-Token") or request.cookies.get("csrf_token")
            if not csrf_token or not validate_csrf_token(csrf_token):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid or missing CSRF token. Please refresh the page.", "error": "csrf_token_invalid"},
                )
        return await call_next(request)


if settings.ENVIRONMENT not in ("development", "test"):
    app.add_middleware(CSRFProtectMiddleware)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ===================================================================
# Metrics Endpoint (with authentication)
# ===================================================================

metrics_app = make_asgi_app()

if settings.METRICS_AUTH_ENABLED and settings.ENVIRONMENT not in ("development", "test"):
    class MetricsAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if request.url.path == "/metrics":
                auth = request.headers.get("authorization")
                if not auth or not auth.startswith("Basic "):
                    return JSONResponse(
                        status_code=401,
                        content={"error": "metrics_auth_required"},
                        headers={"WWW-Authenticate": "Basic"},
                    )
                try:
                    import hmac as _hmac
                    encoded = auth.split(" ")[1]
                    decoded = base64.b64decode(encoded).decode()
                    username, password = decoded.split(":", 1)
                    # Constant-time comparison to prevent timing attacks
                    user_match = _hmac.compare_digest(username, settings.METRICS_USERNAME)
                    pass_match = _hmac.compare_digest(password, settings.METRICS_PASSWORD)
                    if not (user_match and pass_match):
                        return JSONResponse(
                            status_code=401,
                            content={"error": "invalid_credentials"},
                            headers={"WWW-Authenticate": "Basic"},
                        )
                except Exception:
                    return JSONResponse(
                        status_code=401,
                        content={"error": "invalid_auth"},
                        headers={"WWW-Authenticate": "Basic"},
                    )
            return await call_next(request)

    app.add_middleware(MetricsAuthMiddleware)

app.mount("/metrics", metrics_app)

# ===================================================================
# Include Routers
# ===================================================================

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(chat_history.router)
app.include_router(admin.router)
app.include_router(payments.router)
app.include_router(credits.router)
app.include_router(modules.router)
app.include_router(advanced_features.router)
app.include_router(next_gen_features.router)
app.include_router(prompt_forge.router)
app.include_router(offline.router)
app.include_router(vault.router)
app.include_router(ai_dashboard.router)
app.include_router(media.router)
app.include_router(auto_edit.router)
app.include_router(blog.router)


# ===================================================================
# Health & Root Endpoints
# ===================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring."""
    db_healthy = await check_db_connection()

    offline_status = {}
    try:
        from app.services.offline_engine import offline_engine
        offline_status = await offline_engine.get_status()
    except Exception:
        offline_status = {"error": "Offline engine not available"}

    return {
        "status": "healthy" if db_healthy else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_healthy else "disconnected",
        "offline_mode": offline_status.get("mode", "unknown"),
        "connectivity": offline_status.get("connectivity", {}),
    }


@app.get("/api/health/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    db_healthy = await check_db_connection()
    if not db_healthy:
        raise HTTPException(status_code=503, detail="Database not ready")
    return {"status": "ready"}


@app.get("/api/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/api/plans")
async def plans_alias(
    request: Request,
    currency: str = Query("USD"),
    country_code: str = Query("US"),
    payment_method: str = Query("stripe"),
):
    """Backward-compatible alias for pricing endpoint."""
    from app.routes.payments import get_plans

    return await get_plans(
        request=request,
        currency=currency,
        country_code=country_code,
        payment_method=payment_method,
    )


@app.get("/")
async def root(request: Request):
    """Root endpoint - serve frontend in production, API info in development."""
    if frontend_serving_enabled:
        index_path = os.path.join(frontend_out_dir, "index.html")
        if os.path.exists(index_path):
            return _frontend_file_response(index_path)
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else "disabled in production",
        "health": "/api/health",
        "metrics": "/metrics",
    }


# ===================================================================
# Test endpoint - CATCH-ALL KE PEHLE DEFINE KARO (Bug 1 fix)
# ===================================================================
@app.get("/test-frontend-file")
async def test_frontend_file():
    index_path = os.path.join(frontend_out_dir, "index.html")
    return {"index_exists": os.path.exists(index_path), "frontend_out_dir": frontend_out_dir}


# ===================================================================
# Global Exception Handlers
# ===================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Sanitize HTTP exception responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": str(exc.detail),
            "error": "http_error",
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler — NEVER allow a raw 500 stacktrace to reach the browser.
    Returns clean JSON: {"detail": "Internal error: <message>"} and logs the full traceback.
    """
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal error: {exc}",
            "error": "internal_server_error",
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


# ===================================================================
# Catch-all: Frontend SPA serving - SABSE LAST (Bug 1 fix)
# Only registered when frontend build exists.
# ===================================================================
if frontend_serving_enabled:
    logger.info("Frontend build detected — serving static files in single-server mode")

    @app.get("/{full_path:path}")
    async def serve_frontend(request: Request, full_path: str):
        if full_path.startswith(("api/", "docs", "redoc", "metrics")):
            return JSONResponse(status_code=404, content={"error": "not_found"})

        if full_path:
            if ".." in full_path or full_path.startswith("/") or "\\" in full_path:
                return JSONResponse(status_code=403, content={"error": "forbidden"})

            resolved_frontend = os.path.realpath(frontend_out_dir)
            candidate = os.path.realpath(os.path.join(frontend_out_dir, full_path))
            if not candidate.startswith(resolved_frontend):
                return JSONResponse(status_code=403, content={"error": "forbidden"})

            file_path = os.path.join(frontend_out_dir, full_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return _frontend_file_response(file_path)

            html_path = os.path.join(frontend_out_dir, f"{full_path}.html")
            if os.path.exists(html_path) and os.path.isfile(html_path):
                return _frontend_file_response(html_path)

        index_path = os.path.join(frontend_out_dir, "index.html")
        if os.path.exists(index_path):
            return _frontend_file_response(index_path)

        return JSONResponse(status_code=404, content={"error": "not_found"})


# ===================================================================
# Development Server
# ===================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=True,
    )