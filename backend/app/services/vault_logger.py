"""
Professional AI - Vault Call Logger (PERMANENT API VAULT)
Logs all API calls (provider, latency, cost) for the owner dashboard.
"""

import json
import time
import os
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timezone

from app.config import settings

logger = logging.getLogger(__name__)


class VaultCallLogger:
    """
    Logs every AI API call with provider, latency, and cost.
    Data is available to the owner dashboard via /api/vault/logs.
    """

    def __init__(self):
        self._enabled = settings.VAULT_LOG_ENABLED
        self._log_dir = Path("./data/vault_logs")
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._log_dir / "vault_calls.jsonl"
        self._in_memory: List[Dict[str, Any]] = []
        self._max_in_memory = 1000

    def log_call(
        self,
        provider: str,
        model: str,
        latency_ms: int,
        success: bool,
        cost_usd: float = 0.0,
        key_index: int = 0,
        error: Optional[str] = None,
    ):
        """Log a single API call."""
        if not self._enabled:
            return

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "success": success,
            "cost_usd": cost_usd,
            "key_index": key_index,
            "error": error,
        }

        # Keep in memory for dashboard
        self._in_memory.append(entry)
        if len(self._in_memory) > self._max_in_memory:
            self._in_memory = self._in_memory[-self._max_in_memory:]

        # Append to file
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.debug(f"Failed to write vault log: {e}")

    def get_recent_calls(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent calls (newest first)."""
        return list(reversed(self._in_memory[-limit:]))

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate stats for the dashboard."""
        if not self._in_memory:
            return {
                "total_calls": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "total_cost_usd": 0.0,
                "by_provider": {},
            }

        total = len(self._in_memory)
        success = sum(1 for c in self._in_memory if c["success"])
        total_latency = sum(c["latency_ms"] for c in self._in_memory)
        total_cost = sum(c["cost_usd"] for c in self._in_memory)

        by_provider: Dict[str, Dict[str, Any]] = {}
        for c in self._in_memory:
            p = c["provider"]
            if p not in by_provider:
                by_provider[p] = {"calls": 0, "success": 0, "latency_ms": 0, "cost_usd": 0}
            by_provider[p]["calls"] += 1
            by_provider[p]["success"] += 1 if c["success"] else 0
            by_provider[p]["latency_ms"] += c["latency_ms"]
            by_provider[p]["cost_usd"] += c["cost_usd"]

        for p in by_provider:
            by_provider[p]["avg_latency_ms"] = round(
                by_provider[p]["latency_ms"] / by_provider[p]["calls"], 1
            )
            by_provider[p]["success_rate"] = round(
                by_provider[p]["success"] / by_provider[p]["calls"] * 100, 1
            )

        return {
            "total_calls": total,
            "success_rate": round(success / total * 100, 1),
            "avg_latency_ms": round(total_latency / total, 1),
            "total_cost_usd": round(total_cost, 6),
            "by_provider": by_provider,
        }


# Global instance
vault_logger = VaultCallLogger()