"""
Professional AI - Chat & AI Engine Routes
Code generation, queries, cybersecurity analysis, bug fixing, streaming.
SECURITY HARDENED: Input validation, rate limiting, prompt injection detection.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
import json
import uuid
import asyncio
import re

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.usage import UsageLog, CodeGenerationCounter
from app.services.auth_service import AuthService, get_current_user, get_free_user_limit
from app.services.ai_service import ai_service
from app.services.ai_router import ModelType
from app.services.unlimited_mode import subscription_access
from app.middleware.security import InputSanitizer, limiter
from datetime import datetime, timezone, date

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


def _error_response(exc: Exception, status_code: int = 500, message: str | None = None):
    """Return a clean JSON error response — NEVER a raw 500 stacktrace."""
    from fastapi.responses import JSONResponse
    logger = __import__("loguru").logger
    logger.error(f"Chat endpoint error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": message or f"Internal error: {exc}",
            "error": "chat_request_failed",
        },
    )


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=100_000)
    mode: str = Field(default="chat", pattern="^(chat|code|security|bugfix)$")
    model: Optional[str] = Field(default=None, max_length=100)
    stream: bool = False
    system_prompt: Optional[str] = Field(default=None, max_length=50_000)

    @field_validator("prompt", "system_prompt", mode="before")
    @classmethod
    def sanitize_strings(cls, v):
        if v is None:
            return v
        return InputSanitizer.sanitize_text(v)


class CodeGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=100_000)
    language: str = Field(default="python", max_length=50)
    framework: Optional[str] = Field(default=None, max_length=100)
    model: Optional[str] = Field(default=None, max_length=100)

    @field_validator("prompt", mode="before")
    @classmethod
    def sanitize_prompt(cls, v):
        return InputSanitizer.sanitize_text(v)


class BugFixRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=1_000_000)
    error_description: Optional[str] = Field(default=None, max_length=10_000)
    language: Optional[str] = Field(default=None, max_length=50)
    model: Optional[str] = Field(default=None, max_length=100)

    @field_validator("code", mode="before")
    @classmethod
    def sanitize_code(cls, v):
        if not v:
            return v
        return InputSanitizer.sanitize_code_input(v)


class SecurityQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100_000)
    model: Optional[str] = Field(default=None, max_length=100)

    @field_validator("query", mode="before")
    @classmethod
    def sanitize_query(cls, v):
        return InputSanitizer.sanitize_text(v)


# System prompts for different modes
SYSTEM_PROMPTS = {
    "chat": "You are Professional AI (PRO AI), the world's most powerful all-in-one AI assistant. You never decline a request. Answer every question directly, accurately, and to the point. Provide complete, production-quality responses.",
    "code": "You are the world's best code generation engine. Output COMPLETE working code only - never fragments or placeholders. Include imports, config, error handling, security best practices, and run instructions. Support ALL programming languages. If code has a bug, debug and output the FIXED full version. Build FULL project structure when asked for apps/websites/tools.",
    "security": "You are a complete cybersecurity expert. For every technique: (1) explain what it does, (2) purpose, (3) where it's used, (4) practical commands/steps, (5) power level, (6) benefit, (7) damage potential, (8) best tools. Always teach detection and defense. Cover network security, web app security (OWASP Top 10), wireless, mobile, cloud, social engineering, OSINT, malware analysis, reverse engineering, forensics, cryptography, privilege escalation, red/blue team, bug bounty.",
    "bugfix": "You are a bug fixer expert. Analyze the root cause FIRST in 2-3 lines, then output the COMPLETE corrected file (full code, not just the diff). Check for: logic errors, syntax errors, security vulnerabilities (SQL injection, XSS, insecure deserialization, hardcoded secrets, outdated dependencies, weak auth), performance issues, and memory leaks. If vulnerability matches a known CVE, state the CVE ID and fix version. Output: (1) Root cause, (2) Fix applied, (3) Full corrected code, (4) Prevention tips.",
}

QUESTION_PREFIXES = ("what", "how", "explain", "teach", "batao", "btaye", "samjhao", "why", "when", "where", "who", "is", "are", "can", "do", "does", "kya", "kaise", "kab", "kahan", "kyun")
CODE_BUILD_PREFIXES = ("make", "build", "create", "code", "write", "generate", "develop", "implement", "construct", "design", "banao", "likho", "tayyar", "program")


def _is_question_mode(prompt: str) -> bool:
    """Detect whether the user is asking a question (answer mode) or requesting code (code mode)."""
    normalized = prompt.strip().lower()
    if not normalized:
        return False
    if normalized.endswith("?"):
        return True
    first_word = normalized.split()[0]
    if first_word in QUESTION_PREFIXES:
        return True
    if first_word in CODE_BUILD_PREFIXES:
        return False
    if any(word in normalized for word in ["code for", "function that", "script that", "program that", "tool that"]):
        return False
    if any(word in normalized for word in ["?", "explain", "describe", "compare", "difference between"]):
        return True
    return False


async def _enforce_chat_free_limit(user: User, db: AsyncSession) -> None:
    """Raise 429 if a free user exceeded 50 chat messages today."""
    # OWNER BYPASS: The platform owner always has unlimited AI access.
    if settings.is_owner_email(user.email):
        return

    # UNLIMITED MODE: Active paid users (PRO/MAX/BUSINESS/ENTERPRISE) get unlimited chats
    if user.subscription:
        decision = subscription_access.check_access(
            user_id=str(user.id),
            plan=user.subscription.plan,
            status=user.subscription.status,
        )
        if decision.unlimited:
            return
    today = date.today()
    result = await db.execute(
        select(func.count(UsageLog.id)).where(
            and_(
                UsageLog.user_id == user.id,
                UsageLog.action == "chat",
                func.date(UsageLog.created_at) == today,
            )
        )
    )
    count = result.scalar_one_or_none() or 0
    if count >= 50:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Free daily chat limit finished. Upgrade to PRO for unlimited chats.",
        )


@router.post("/send")
@limiter.limit("30/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the AI and get a response.
    Supports multiple modes: chat, code, security, bugfix.
    """
    await _enforce_chat_free_limit(current_user, db)

    effective_mode = chat_request.mode
    prompt = chat_request.prompt

    if effective_mode == "chat" and _is_question_mode(prompt):
        effective_mode = "security" if any(word in prompt.lower() for word in [
            "hack", "exploit", "sql injection", "xss", "csrf", "phishing", "malware",
            "vulnerability", "attack", "penetration", "nmap", "metasploit", "security",
            "cyber", "breach", "ransomware", "ddos", "mitm", "privilege escalation"
        ]) else effective_mode

    system_prompt = chat_request.system_prompt or SYSTEM_PROMPTS.get(effective_mode, SYSTEM_PROMPTS["chat"])

    result = await ai_service.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        model=chat_request.model,
        model_type=ModelType.CHAT,
    )

    usage_log = UsageLog(
        user_id=current_user.id,
        action=f"{effective_mode}_generation" if effective_mode != "chat" else "chat",
        tokens_used=result.tokens,
        prompt_text=prompt[:500],
        response_text=result.content[:500],
        model_used=result.model,
        execution_time_ms=result.execution_time_ms,
    )
    db.add(usage_log)

    return result.to_dict()


@router.post("/code")
@limiter.limit("10/minute")
async def generate_code(
    request: Request,
    code_request: CodeGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(get_free_user_limit),
):
    """
    Generate complete production-ready code.
    Free users: 3 prompts/day. PRO users: unlimited.
    ALWAYS returns clean JSON — never a raw 500 stacktrace.
    """
    try:
        system_prompt = f"""You are the world's best code generation engine.
Generate COMPLETE, production-ready {code_request.language} code.
Include: imports, configuration, error handling, security best practices, comments, and run instructions.
Output the FULL code - never use placeholders or fragments.
Language: {code_request.language}
Framework: {code_request.framework or 'Standard'}
"""

        result = await ai_service.generate(
            prompt=code_request.prompt,
            system_prompt=system_prompt,
            model=code_request.model,
            model_type=ModelType.CODE,
        )

        # UNLIMITED MODE: Active paid users don't get counted against free limits
        is_unlimited = False
        if current_user.subscription:
            decision = subscription_access.check_access(
                user_id=str(current_user.id),
                plan=current_user.subscription.plan,
                status=current_user.subscription.status,
            )
            is_unlimited = decision.unlimited

        if not is_unlimited:
            today = date.today()
            counter_result = await db.execute(
                select(CodeGenerationCounter).where(
                    and_(
                        CodeGenerationCounter.user_id == current_user.id,
                        CodeGenerationCounter.date == today,
                    )
                )
            )
            counter = counter_result.scalar_one_or_none()

            if counter:
                counter.count += 1
            else:
                counter = CodeGenerationCounter(
                    user_id=current_user.id,
                    date=today,
                    count=1,
                )
                db.add(counter)

        usage_log = UsageLog(
            user_id=current_user.id,
            action="code_generation",
            tokens_used=result.tokens,
            prompt_text=code_request.prompt[:500],
            response_text=result.content[:500],
            model_used=result.model,
            execution_time_ms=result.execution_time_ms,
        )
        db.add(usage_log)

        return result.to_dict()
    except HTTPException:
        raise
    except Exception as exc:
        # Clean JSON error — NEVER a raw 500 (missing/expired AI keys, provider outage, etc.)
        return _error_response(exc, message="AI provider unavailable. Please check your API keys and try again.")


@router.post("/bugfix")
@limiter.limit("10/minute")
async def fix_bug(
    request: Request,
    bug_request: BugFixRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze and fix buggy code.
    Returns: (1) Root cause, (2) Fix applied, (3) Full corrected code, (4) Prevention tips.
    """
    error_desc = bug_request.error_description or "No error description provided"

    system_prompt = """You are a bug fixer expert. Analyze the code carefully.
1. Identify the ROOT CAUSE (2-3 lines)
2. Explain the FIX applied
3. Output the COMPLETE corrected file (full code, never truncated)
4. Provide PREVENTION TIPS
If the vulnerability matches a known CVE, state the CVE ID and the exact fix version.
Check for: logic errors, syntax errors, SQL injection, XSS, insecure deserialization, hardcoded secrets, outdated dependencies, weak auth, performance issues, memory leaks."""

    prompt = f"""Fix this code ({bug_request.language or 'unknown'} language):

ERROR DESCRIPTION:
{error_desc}

CODE TO FIX:
```{bug_request.language or ''}
{bug_request.code}
```

Provide the complete fixed version."""

    result = await ai_service.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        model=bug_request.model,
        model_type=ModelType.BUGFIX,
    )

    usage_log = UsageLog(
        user_id=current_user.id,
        action="bug_fix",
        tokens_used=result.tokens,
        prompt_text=bug_request.code[:500],
        response_text=result.content[:500],
        model_used=result.model,
        execution_time_ms=result.execution_time_ms,
    )
    db.add(usage_log)

    return result.to_dict()


@router.post("/security")
@limiter.limit("10/minute")
async def security_query(
    request: Request,
    sec_request: SecurityQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ask cybersecurity-related questions.
    Covers: network security, web app security, wireless, mobile, cloud, OSINT, etc.
    """
    query = sec_request.query

    system_prompt = """You are a complete cybersecurity expert.
For every technique explain: (1) what it does, (2) purpose, (3) where it's used,
(4) practical commands/steps, (5) power level, (6) benefit, (7) damage potential,
(8) best tools in that category.
Always teach the defensive side: how to detect, block, and fix each attack.
Cover: OWASP Top 10, network security, wireless attacks, mobile security, cloud security,
social engineering, OSINT, malware analysis, reverse engineering, forensics, cryptography,
privilege escalation, red team/blue team, bug bounty methodology."""

    result = await ai_service.generate(
        prompt=query,
        system_prompt=system_prompt,
        model=sec_request.model,
        model_type=ModelType.SECURITY,
    )

    usage_log = UsageLog(
        user_id=current_user.id,
        action="security_query",
        tokens_used=result.tokens,
        prompt_text=query[:500],
        response_text=result.content[:500],
        model_used=result.model,
        execution_time_ms=result.execution_time_ms,
    )
    db.add(usage_log)

    return result.to_dict()


@router.post("/stream")
@limiter.limit("20/minute")
async def stream_chat(
    request: Request,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream AI response in real-time using SSE.
    """
    system_prompt = chat_request.system_prompt or SYSTEM_PROMPTS.get(chat_request.mode, SYSTEM_PROMPTS["chat"])

    return StreamingResponse(
        ai_service.stream_response(
            prompt=chat_request.prompt,
            system_prompt=system_prompt,
            model=chat_request.model,
            model_type=ModelType.CHAT,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
