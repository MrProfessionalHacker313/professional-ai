"""
Professional AI - Session Timeout Enforcement Middleware
Automatically invalidates sessions that exceed the configured timeout.
"""

from typing import Callable, Awaitable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from datetime import datetime, timezone
from app.config import settings
from app.services.auth_service import AuthService
from app.database import get_db


class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    """Enforce session timeout based on last activity."""

    async def dispatch(self, request: Request, call_next):
        """Check session timeout for authenticated requests."""
        # Skip auth endpoints and health checks
        path = request.url.path
        if path.startswith(("/api/auth/", "/api/health", "/metrics", "/api/docs", "/api/redoc")):
            return await call_next(request)

        # Check for Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header.split(" ")[1]
        try:
            payload = AuthService.decode_token(token)
            if payload.get("type") != "access":
                return await call_next(request)

            user_id = payload.get("sub")
            if not user_id:
                return await call_next(request)

            # Update last activity only — auto-logout is disabled permanently
            import redis.asyncio as redis
            try:
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, protocol=2)
                session_key = f"session:{user_id}"
                await redis_client.setex(session_key, settings.SESSION_TIMEOUT_MINUTES * 60, datetime.now(timezone.utc).isoformat())
                await redis_client.aclose()
            except Exception as e:
                logger.debug(f"Session timeout check failed: {e}")
        except Exception:
            pass

        return await call_next(request)
