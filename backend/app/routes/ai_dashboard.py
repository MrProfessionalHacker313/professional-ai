"""
Professional AI - AI Dashboard Routes
Dashboard endpoints for monitoring AI provider usage, costs, and health.
Shows which provider is being used, cost per request, and health status of each API.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.config import settings
from app.services.ai_router import ai_router
from app.services.vault_health_monitor import vault_health_monitor
from app.services.vault_logger import vault_logger
from app.services.local_fallback import local_fallback_engine
from app.services.ai_providers_config import AI_PROVIDERS_CONFIG, DEFAULT_PROVIDER_ORDER, PROVIDER_FEATURES

router = APIRouter(prefix="/api/ai", tags=["ai-dashboard"])


class ProviderSummaryResponse(BaseModel):
    provider: str
    name: str
    status: str  # ok, fail, skipped
    healthy: bool
    model: str
    code_model: str
    keys_configured: int
    current_key_index: int
    consecutive_failures: int
    avg_response_time_ms: float
    cost_per_1k_input: float
    cost_per_1k_output: float
    rate_limit_rpm: int
    max_tokens: int
    features: List[str]
    total_calls: int = 0
    success_rate: float = 0.0
    total_cost_usd: float = 0.0


class CostSummaryResponse(BaseModel):
    total_cost_usd: float
    total_calls: int
    avg_cost_per_call: float
    by_provider: Dict[str, Dict[str, Any]]
    period_days: int


class AIHealthResponse(BaseModel):
    mode: str
    active_provider: Optional[str]
    providers: Dict[str, ProviderSummaryResponse]
    local_fallback: Dict[str, Any]
    last_check: Optional[str]


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_ai_dashboard(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive AI dashboard data:
    - All 10 provider health statuses
    - Cost per request and total costs
    - Provider usage statistics
    - Active provider being used
    """
    health = ai_router.get_health_status()
    providers = {p["provider"]: p for p in health.get("providers", [])}
    logs_stats = vault_logger.get_stats()
    recent_calls = vault_logger.get_recent_calls(limit=500)

    # Build provider summaries
    provider_summaries = {}
    total_cost = 0.0
    total_calls = 0
    active_provider = None

    for provider_id in DEFAULT_PROVIDER_ORDER:
        config = AI_PROVIDERS_CONFIG.get(provider_id, {})
        p_info = providers.get(provider_id, {})
        is_healthy = p_info.get("healthy", False)
        has_keys = len(p_info.get("keys", [])) > 0

        status = "ok" if is_healthy else "fail"
        if not has_keys:
            status = "skipped"

        # Calculate stats from recent calls
        provider_calls = [c for c in recent_calls if c.get("provider") == provider_id]
        provider_success = sum(1 for c in provider_calls if c.get("success"))
        provider_cost = sum(c.get("cost_usd", 0.0) for c in provider_calls)

        if is_healthy and active_provider is None:
            active_provider = provider_id

        provider_summaries[provider_id] = {
            "provider": provider_id,
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
            "total_calls": len(provider_calls),
            "success_rate": round(provider_success / len(provider_calls) * 100, 1) if provider_calls else 0.0,
            "total_cost_usd": round(provider_cost, 6),
        }

        total_cost += provider_cost
        total_calls += len(provider_calls)

    # Determine mode
    has_healthy_cloud = any(p.get("healthy") for p in providers.values())
    mode = "cloud" if has_healthy_cloud else "local"

    return {
        "mode": mode,
        "active_provider": active_provider,
        "providers": provider_summaries,
        "cost_summary": {
            "total_cost_usd": round(total_cost, 6),
            "total_calls": total_calls,
            "avg_cost_per_call": round(total_cost / total_calls, 6) if total_calls > 0 else 0.0,
            "period_days": days,
        },
        "local_fallback": {
            "status": "active" if health.get("local_fallback_enabled") else "inactive",
            "engine": health.get("local_fallback", {}).get("provider", "unknown"),
            "onnx_available": health.get("local_fallback", {}).get("onnx_available", False),
        },
        "recent_calls": recent_calls[:50],
        "last_check": vault_health_monitor._last_check,
    }


@router.get("/providers", response_model=Dict[str, Any])
async def get_ai_providers() -> Dict[str, Any]:
    """Get all AI provider configurations and metadata."""
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


@router.get("/health", response_model=Dict[str, Any])
async def get_ai_health() -> Dict[str, Any]:
    """Get AI provider health status."""
    health = ai_router.get_health_status()
    monitor_status = vault_health_monitor.get_status()

    providers = {}
    for provider_id in DEFAULT_PROVIDER_ORDER:
        config = AI_PROVIDERS_CONFIG.get(provider_id, {})
        p_info = next((p for p in health.get("providers", []) if p["provider"] == provider_id), {})
        
        providers[provider_id] = {
            "name": config.get("name", provider_id),
            "healthy": p_info.get("healthy", False),
            "model": p_info.get("model", config.get("chat_model", "")),
            "consecutive_failures": p_info.get("consecutive_failures", 0),
            "avg_response_time_ms": p_info.get("avg_response_time_ms", 0),
            "keys": p_info.get("keys", []),
        }

    return {
        "status": health,
        "providers": providers,
        "monitor": monitor_status,
        "local_fallback": health.get("local_fallback", {}),
    }


@router.get("/costs", response_model=Dict[str, Any])
async def get_ai_costs(
    days: int = Query(7, ge=1, le=90),
) -> Dict[str, Any]:
    """Get AI cost breakdown by provider for the last N days."""
    recent_calls = vault_logger.get_recent_calls(limit=2000)
    
    cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
    recent_calls = [
        c for c in recent_calls
        if datetime.fromisoformat(c.get("timestamp", "1970-01-01T00:00:00+00:00")).timestamp() > cutoff
    ]

    by_provider = {}
    total_cost = 0.0
    total_calls = 0
    success_calls = 0

    for call in recent_calls:
        provider_name = call.get("provider", "unknown")
        if provider_name not in by_provider:
            by_provider[provider_name] = {
                "calls": 0,
                "success": 0,
                "total_cost_usd": 0.0,
                "avg_latency_ms": 0.0,
                "total_latency_ms": 0.0,
            }
        
        by_provider[provider_name]["calls"] += 1
        total_calls += 1
        
        if call.get("success"):
            by_provider[provider_name]["success"] += 1
            success_calls += 1
        
        cost = call.get("cost_usd", 0.0)
        by_provider[provider_name]["total_cost_usd"] += cost
        total_cost += cost
        
        latency = call.get("latency_ms", 0)
        by_provider[provider_name]["total_latency_ms"] += latency

    for provider_name, stats in by_provider.items():
        if stats["calls"] > 0:
            stats["avg_latency_ms"] = round(stats["total_latency_ms"] / stats["calls"], 1)
            stats["success_rate"] = round(stats["success"] / stats["calls"] * 100, 1)
        else:
            stats["avg_latency_ms"] = 0.0
            stats["success_rate"] = 0.0
        stats["total_cost_usd"] = round(stats["total_cost_usd"], 6)
        del stats["total_latency_ms"]

    return {
        "total_cost_usd": round(total_cost, 6),
        "total_calls": total_calls,
        "success_calls": success_calls,
        "success_rate": round(success_calls / total_calls * 100, 1) if total_calls > 0 else 0.0,
        "avg_cost_per_call": round(total_cost / total_calls, 6) if total_calls > 0 else 0.0,
        "by_provider": by_provider,
        "period_days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/current-provider")
async def get_current_provider() -> Dict[str, Any]:
    """Get the currently active AI provider."""
    health = ai_router.get_health_status()
    providers = {p["provider"]: p for p in health.get("providers", [])}
    
    active_provider = None
    for provider_id in DEFAULT_PROVIDER_ORDER:
        p_info = providers.get(provider_id, {})
        if p_info.get("healthy", False) and len(p_info.get("keys", [])) > 0:
            active_provider = provider_id
            break

    config = AI_PROVIDERS_CONFIG.get(active_provider, {}) if active_provider else {}

    return {
        "active_provider": active_provider,
        "name": config.get("name", active_provider),
        "model": config.get("chat_model", ""),
        "code_model": config.get("code_model", ""),
        "mode": "cloud" if active_provider else "local",
        "fallback_engine": health.get("local_fallback", {}).get("provider", "unknown") if not active_provider else None,
    }
