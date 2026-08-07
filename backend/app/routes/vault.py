"""
Professional AI - Permanent API Vault Routes
Endpoints for the owner dashboard to monitor the vault:
- Provider chain status
- Health monitor status
- Call logs (provider, latency, cost)
- Key refresh reminder
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

from app.config import settings
from app.services.ai_router import ai_router
from app.services.vault_health_monitor import vault_health_monitor
from app.services.vault_logger import vault_logger
from app.services.local_fallback import local_fallback_engine

router = APIRouter(prefix="/api/vault", tags=["vault"])


@router.get("/status")
async def vault_status() -> Dict[str, Any]:
    """Get full vault status for the owner dashboard."""
    return ai_router.get_vault_status()


@router.get("/health")
async def vault_health() -> Dict[str, Any]:
    """Get provider health status."""
    return {
        "status": ai_router.get_health_status(),
        "monitor": vault_health_monitor.get_status(),
    }


@router.get("/logs")
async def vault_logs(limit: int = 100) -> Dict[str, Any]:
    """Get recent API call logs."""
    return {
        "stats": vault_logger.get_stats(),
        "recent_calls": vault_logger.get_recent_calls(limit=limit),
    }


@router.get("/key-refresh-reminder")
async def key_refresh_reminder() -> Dict[str, Any]:
    """
    Monthly key refresh reminder for the owner dashboard.
    One click each to add free keys at aistudio.google.com / console.groq.com.
    """
    return {
        "reminder": (
            "Add free keys to keep quota topped up forever at zero cost. "
            "One click each — no code change needed."
        ),
        "links": [
            {
                "provider": "Gemini",
                "url": "https://aistudio.google.com/apikey",
                "env_var": "GEMINI_KEYS",
                "description": "Add free Gemini API keys (comma-separated)",
            },
            {
                "provider": "Groq",
                "url": "https://console.groq.com/keys",
                "env_var": "GROQ_KEYS",
                "description": "Add free Groq API keys (comma-separated)",
            },
            {
                "provider": "OpenRouter",
                "url": "https://openrouter.ai/keys",
                "env_var": "OPENROUTER_KEYS",
                "description": "Add free OpenRouter API keys (comma-separated)",
            },
        ],
        "refresh_interval_days": settings.VAULT_KEY_REFRESH_REMINDER_DAYS,
        "last_reminder": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/local-fallback")
async def local_fallback_status() -> Dict[str, Any]:
    """Get local fallback engine status."""
    return local_fallback_engine.get_status()


@router.get("/ai-status")
async def ai_status() -> Dict[str, Any]:
    """
    Provider status endpoint: GET /api/ai/status
    Returns JSON: {gemini: ok/fail + reason, groq: ok/fail + reason, local: active/inactive, mode: cloud/local}
    """
    health = ai_router.get_health_status()
    providers = {p["provider"]: p for p in health.get("providers", [])}
    
    gemini = providers.get("gemini", {})
    groq = providers.get("groq", {})
    
    # Determine mode
    has_healthy_cloud = any(p.get("healthy") for p in providers.values())
    mode = "cloud" if has_healthy_cloud else "local"
    
    return {
        "mode": mode,
        "gemini": {
            "status": "ok" if gemini.get("healthy") else "fail",
            "reason": "healthy" if gemini.get("healthy") else (
                "no_valid_keys" if not gemini.get("keys") else (
                    f"all_keys_failed (consecutive_failures={gemini.get('consecutive_failures', 0)})"
                )
            ),
            "model": gemini.get("model"),
            "keys_configured": len(gemini.get("keys", [])),
            "current_key_index": gemini.get("current_key_index"),
        },
        "groq": {
            "status": "ok" if groq.get("healthy") else "fail",
            "reason": "healthy" if groq.get("healthy") else (
                "no_valid_keys" if not groq.get("keys") else (
                    f"all_keys_failed (consecutive_failures={groq.get('consecutive_failures', 0)})"
                )
            ),
            "model": groq.get("model"),
            "keys_configured": len(groq.get("keys", [])),
            "current_key_index": groq.get("current_key_index"),
        },
        "local": {
            "status": "active" if health.get("local_fallback_enabled") else "inactive",
            "engine": health.get("local_fallback", {}).get("provider", "unknown"),
        },
        "connectivity_check_url": settings.AI_CONNECTIVITY_CHECK_URL,
        "timeout_seconds": settings.AI_PROVIDER_TIMEOUT,
        "retries": settings.AI_PROVIDER_RETRIES,
    }
