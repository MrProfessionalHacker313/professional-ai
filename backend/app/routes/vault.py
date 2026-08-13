"""
Professional AI - Permanent API Vault Routes
Endpoints for the owner dashboard to monitor the vault:
- Provider chain status
- Health monitor status
- Call logs (provider, latency, cost)
- Key refresh reminder
- AI Provider Dashboard (all 10 providers with cost tracking)
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta

from app.config import settings
from app.services.ai_router import ai_router
from app.services.vault_health_monitor import vault_health_monitor
from app.services.vault_logger import vault_logger
from app.services.local_fallback import local_fallback_engine
from app.services.ai_providers_config import AI_PROVIDERS_CONFIG, DEFAULT_PROVIDER_ORDER, PROVIDER_FEATURES

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
    One click each to add free keys at provider consoles.
    """
    links = []
    for provider_id in DEFAULT_PROVIDER_ORDER:
        config = AI_PROVIDERS_CONFIG.get(provider_id, {})
        if config:
            links.append({
                "provider": config.get("name", provider_id),
                "env_var": config.get("env_keys", config.get("env_key", "")),
                "description": f"Add {config.get('name', provider_id)} API keys (comma-separated)",
            })

    return {
        "reminder": (
            "Add API keys to keep quota topped up. "
            "One click each — no code change needed."
        ),
        "links": links,
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
    Provider status endpoint: GET /api/vault/ai-status
    Returns JSON with all 10 provider statuses, active provider, cost summary, and mode.
    """
    health = ai_router.get_health_status()
    providers = {p["provider"]: p for p in health.get("providers", [])}

    provider_statuses = {}
    total_cost_today = 0.0
    total_calls_today = 0
    active_provider = None

    for provider_id in DEFAULT_PROVIDER_ORDER:
        config = AI_PROVIDERS_CONFIG.get(provider_id, {})
        p_info = providers.get(provider_id, {})
        
        is_healthy = p_info.get("healthy", False)
        has_keys = len(p_info.get("keys", [])) > 0
        
        status = "ok" if is_healthy else "fail"
        if not has_keys:
            status = "skipped"
        
        provider_statuses[provider_id] = {
            "name": config.get("name", provider_id),
            "status": status,
            "healthy": is_healthy,
            "model": p_info.get("model", config.get("chat_model", "")),
            "code_model": p_info.get("code_model", config.get("code_model", "")),
            "keys_configured": len(p_info.get("keys", [])),
            "current_key_index": p_info.get("current_key_index", 0),
            "consecutive_failures": p_info.get("consecutive_failures", 0),
            "avg_response_time_ms": p_info.get("avg_response_time_ms", 0),
            "cost_per_1k_input": config.get("cost_per_1k_input", 0.0),
            "cost_per_1k_output": config.get("cost_per_1k_output", 0.0),
            "rate_limit_rpm": config.get("rate_limit_rpm", 0),
            "max_tokens": config.get("max_tokens", 0),
            "features": PROVIDER_FEATURES.get(provider_id, []),
        }

        if is_healthy and active_provider is None:
            active_provider = provider_id

    # Determine mode
    has_healthy_cloud = any(p.get("healthy") for p in providers.values())
    mode = "cloud" if has_healthy_cloud else "local"

    return {
        "mode": mode,
        "active_provider": active_provider,
        "providers": provider_statuses,
        "local_fallback": {
            "status": "active" if health.get("local_fallback_enabled") else "inactive",
            "engine": health.get("local_fallback", {}).get("provider", "unknown"),
        },
        "connectivity_check_url": settings.AI_CONNECTIVITY_CHECK_URL,
        "timeout_seconds": settings.AI_PROVIDER_TIMEOUT,
        "retries": settings.AI_PROVIDER_RETRIES,
    }


@router.get("/providers")
async def list_providers() -> Dict[str, Any]:
    """List all configured AI providers with metadata."""
    providers = []
    for provider_id in DEFAULT_PROVIDER_ORDER:
        config = AI_PROVIDERS_CONFIG.get(provider_id, {})
        providers.append({
            "id": provider_id,
            "name": config.get("name", provider_id),
            "chat_model": config.get("chat_model", ""),
            "code_model": config.get("code_model", ""),
            "base_url": config.get("base_url", ""),
            "cost_per_1k_input": config.get("cost_per_1k_input", 0.0),
            "cost_per_1k_output": config.get("cost_per_1k_output", 0.0),
            "rate_limit_rpm": config.get("rate_limit_rpm", 0),
            "max_tokens": config.get("max_tokens", 0),
            "supports_streaming": config.get("supports_streaming", False),
            "supports_vision": config.get("supports_vision", False),
            "supports_code": config.get("supports_code", False),
            "features": PROVIDER_FEATURES.get(provider_id, []),
        })
    return {
        "providers": providers,
        "default_order": DEFAULT_PROVIDER_ORDER,
    }
