"""
Professional AI - WAF (Web Application Firewall) Middleware
Blocks common attack patterns: SQL injection, XSS, path traversal, SSRF, command injection.
"""

import re
import time
from typing import Callable, Awaitable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from app.config import settings


class WAFMiddleware(BaseHTTPMiddleware):
    """Web Application Firewall middleware that blocks common attacks."""

    ATTACK_PATTERNS = [
        # SQL Injection
        (r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b\s*\(|\b(OR|AND)\b\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?)", "SQL injection attempt"),
        (r"(UNION\s+SELECT|UNION\s+ALL\s+SELECT)", "SQL injection UNION attempt"),
        (r"(--|\#|\/\*|\*\/)", "SQL comment injection"),
        (r"(;\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER))", "SQL stacked queries"),
        (r"('|\")\s*(OR|AND)\s*('|\")?\s*\w+\s*=\s*\w+", "SQL tautology"),
        
        # XSS
        (r"<script[^>]*>.*?</script>", "XSS script tag"),
        (r"javascript\s*:", "XSS javascript protocol"),
        (r"on\w+\s*=\s*['\"][^'\"]*['\"]", "XSS event handler"),
        (r"<iframe[^>]*>", "XSS iframe"),
        (r"<object[^>]*>", "XSS object tag"),
        (r"<embed[^>]*>", "XSS embed tag"),
        (r"<form[^>]*action\s*=\s*['\"](?!https?://(localhost|127\.0\.0\.1|app\.))", "XSS form action"),
        
        # Path Traversal
        (r"(\.\.\/|\.\.\\)", "Path traversal attempt"),
        (r"(\.\.%2F|\.\.%5C)", "URL-encoded path traversal"),
        
        # Command Injection
        (r"(;|\||&&|\|\|)\s*(cat|ls|dir|rm|del|curl|wget|nc|netcat|bash|sh|cmd|powershell)", "Command injection"),
        (r"\$\([^)]+\)", "Command substitution"),
        (r"`[^`]+`", "Backtick command execution"),
        
        # XXE
        (r"<!DOCTYPE[^>]*SYSTEM[^>]*>", "XXE DOCTYPE"),
        (r"<!ENTITY[^>]*>", "XXE entity definition"),
        
        # SSRF
        (r"(localhost|127\.0\.0\.1|0\.0\.0\.0|169\.254\.169\.254|metadata\.google\.internal)", "SSRF internal address"),
        
        # File inclusion
        (r"(php://|file://|ftp://|gopher://|dict://)", "File inclusion protocol"),
        
        # Clickjacking
        (r"<frameset[^>]*>", "Clickjacking frameset"),
    ]

    def __init__(self, app):
        super().__init__(app)
        self.compiled_patterns = [(re.compile(p, re.IGNORECASE | re.DOTALL), msg) for p, msg in self.ATTACK_PATTERNS]

    async def dispatch(self, request: Request, call_next):
        """Check request for attack patterns."""
        # Check query params
        query_string = str(request.query_params)
        for pattern, msg in self.compiled_patterns:
            if pattern.search(query_string):
                logger.warning(f"WAF blocked request: {msg} from {request.client.host if request.client else 'unknown'}")
                raise HTTPException(status_code=403, detail="Request blocked by security policy")

        # Check request body for non-GET requests
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            try:
                body = await request.body()
                body_str = body.decode("utf-8", errors="ignore") if body else ""
                for pattern, msg in self.compiled_patterns:
                    if pattern.search(body_str):
                        logger.warning(f"WAF blocked request body: {msg} from {request.client.host if request.client else 'unknown'}")
                        raise HTTPException(status_code=403, detail="Request blocked by security policy")
            except Exception:
                pass

        return await call_next(request)
