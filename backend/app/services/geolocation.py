"""
Professional AI - IP Geolocation Service
Auto-detects user country via ipapi.co (free, no key required).
Falls back to X-Forwarded-For / CF-IPCountry headers.

PRICING GEO-FIX:
- Detection is ALWAYS server-side (never trusts client-supplied country).
- Per-IP cache to avoid hammering ipapi.co.
- On API failure, returns None (caller must default to USD, never PKR).
"""

from typing import Optional
from fastapi import Request
from loguru import logger
import httpx
import time


# Per-IP cache: {ip: {"ts": float, "country": Optional[str]}}
_GEO_CACHE: dict = {}
_GEO_TTL = 3600  # 1 hour cache per IP
_MAX_CACHE_ENTRIES = 5000


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for") or request.headers.get("x-real-ip")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


def _cache_get(ip: str) -> Optional[str]:
    entry = _GEO_CACHE.get(ip)
    if not entry:
        return None
    if time.time() - entry["ts"] > _GEO_TTL:
        _GEO_CACHE.pop(ip, None)
        return None
    return entry.get("country")


def _cache_set(ip: str, country: Optional[str]) -> None:
    # Prevent unbounded growth
    if len(_GEO_CACHE) >= _MAX_CACHE_ENTRIES:
        # Drop oldest entries
        oldest = sorted(_GEO_CACHE.keys(), key=lambda k: _GEO_CACHE[k]["ts"])[: len(_GEO_CACHE) // 2]
        for k in oldest:
            _GEO_CACHE.pop(k, None)
    _GEO_CACHE[ip] = {"ts": time.time(), "country": country}


async def detect_country_from_request(request: Request) -> dict:
    """
    Server-side country detection. Returns {"country": Optional[str], "ip": str}.

    Priority:
      1. Per-IP cache
      2. Trusted proxy headers (CF-IPCountry / x-vercel-ip-country)
      3. ipapi.co/json/<ip> (server-side, free)

    On total failure returns {"country": None} — caller MUST default to USD.
    """
    ip = _client_ip(request)

    if ip in {"127.0.0.1", "::1", "localhost"}:
        return {"country": None, "ip": ip}

    cached = _cache_get(ip)
    if cached:
        return {"country": cached, "ip": ip}

    country = None

    # Trusted proxy headers (only when present and valid)
    header_country = request.headers.get("cf-ipcountry") or request.headers.get("x-vercel-ip-country")
    if header_country and header_country.strip().upper() not in {"", "UNKNOWN", "XX"}:
        candidate = header_country.strip().upper()
        if len(candidate) == 2 and candidate.isalpha():
            country = candidate

    # Server-side ipapi.co lookup (authoritative)
    if not country:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"https://ipapi.co/{ip}/json/", follow_redirects=True)
                if resp.status_code == 200:
                    data = resp.json()
                    code = (data.get("country_code") or "").strip().upper()
                    if len(code) == 2 and code.isalpha():
                        country = code
        except Exception as exc:
            logger.debug(f"ipapi.co lookup failed for {ip}: {exc}")

    _cache_set(ip, country)
    return {"country": country, "ip": ip}


def pricing_country_code(detected_country: Optional[str]) -> str:
    """Return a 2-letter country code, defaulting to US (never PKR by default)."""
    if detected_country and len(detected_country) == 2 and detected_country.isalpha():
        return detected_country.upper()
    return "US"


def pricing_currency_for_country(country_code: Optional[str]) -> str:
    """
    PRICING GEO-FIX:
    Only Pakistan (PK) gets PKR. Every other country (or None/unknown) gets USD.
    Never defaults to PKR.
    """
    if country_code and country_code.upper() == "PK":
        return "PKR"
    return "USD"