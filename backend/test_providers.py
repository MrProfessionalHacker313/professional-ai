#!/usr/bin/env python3
"""
Professional AI - Provider Test Script
Tests Gemini and Groq API keys and prints OK/FAIL + exact error.
Usage: python test_providers.py
"""

import asyncio
import os
import sys
import httpx
from typing import Optional


def load_env() -> dict:
    """Load .env file manually."""
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
    if not os.path.exists(env_path):
        env_path = os.path.join(os.path.dirname(__file__), ".env")
    
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    env_vars[key.strip()] = value.strip()
    return env_vars


async def test_gemini(api_key: Optional[str]) -> dict:
    """Test Gemini API with a simple prompt."""
    result = {
        "provider": "Gemini",
        "status": "FAIL",
        "error": None,
        "model": "gemini-2.0-flash",
    }
    
    if not api_key or len(api_key.strip()) < 10:
        result["error"] = f"API key missing or too short (length={len(api_key) if api_key else 0})"
        return result
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    payload = {
        "contents": [{"parts": [{"text": "Say 'OK' in exactly 2 letters."}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 10,
        },
    }
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                url,
                params={"key": api_key.strip()},
                json=payload,
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                result["status"] = "OK"
                result["response"] = content.strip()[:50]
            else:
                result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:
        result["error"] = str(exc)[:200]
    
    return result


async def test_groq(api_key: Optional[str]) -> dict:
    """Test Groq API with a simple prompt."""
    result = {
        "provider": "Groq",
        "status": "FAIL",
        "error": None,
        "model": "llama-3.3-70b-versatile",
    }
    
    if not api_key or len(api_key.strip()) < 10:
        result["error"] = f"API key missing or too short (length={len(api_key) if api_key else 0})"
        return result
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": "Say 'OK' in exactly 2 letters."}],
        "temperature": 0.0,
        "max_tokens": 10,
    }
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                result["status"] = "OK"
                result["response"] = content.strip()[:50]
            else:
                result["error"] = f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as exc:
        result["error"] = str(exc)[:200]
    
    return result


async def main():
    """Run all provider tests."""
    print("=" * 60)
    print("Professional AI - Provider Test")
    print("=" * 60)
    
    env = load_env()
    
    # Check connectivity
    print("\n[Connectivity Check]")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://www.google.com/generate_204")
            online = resp.status_code < 500
            print(f"  Internet: {'ONLINE' if online else 'OFFLINE/UNREACHABLE'}")
    except Exception as exc:
        print(f"  Internet: OFFLINE ({str(exc)[:100]})")
        online = False
    
    if not online:
        print("\n  WARNING: No internet connectivity. Cloud providers will fail.")
        print("  Local fallback will be used instead.\n")
    
    # Test Gemini
    print("\n[Gemini Test]")
    gemini_key = env.get("GEMINI_API_KEY") or env.get("GEMINI_KEYS", "").split(",")[0].strip()
    print(f"  Key configured: {'YES' if gemini_key else 'NO'}")
    if gemini_key:
        print(f"  Key length: {len(gemini_key)}")
        print(f"  Key prefix: {gemini_key[:10]}...")
    gemini_result = await test_gemini(gemini_key)
    status_icon = "[OK]" if gemini_result["status"] == "OK" else "[FAIL]"
    print(f"  Result: {status_icon} {gemini_result['status']}")
    if gemini_result.get("error"):
        print(f"  Error: {gemini_result['error']}")
    if gemini_result.get("response"):
        print(f"  Response: {gemini_result['response']}")
    
    # Test Groq
    print("\n[Groq Test]")
    groq_key = env.get("GROQ_API_KEY") or env.get("GROQ_KEYS", "").split(",")[0].strip()
    print(f"  Key configured: {'YES' if groq_key else 'NO'}")
    if groq_key:
        print(f"  Key length: {len(groq_key)}")
        print(f"  Key prefix: {groq_key[:10]}...")
    groq_result = await test_groq(groq_key)
    status_icon = "[OK]" if groq_result["status"] == "OK" else "[FAIL]"
    print(f"  Result: {status_icon} {groq_result['status']}")
    if groq_result.get("error"):
        print(f"  Error: {groq_result['error']}")
    if groq_result.get("response"):
        print(f"  Response: {groq_result['response']}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    gemini_ok = gemini_result["status"] == "OK"
    groq_ok = groq_result["status"] == "OK"
    
    if gemini_ok and groq_ok:
        print("[SUCCESS] CLOUD PROVIDERS RESTORED — Gemini + Groq work")
        print("   Local fallback only when truly offline.")
        return 0
    elif gemini_ok or groq_ok:
        print("[PARTIAL] One provider working, one failing.")
        if not gemini_ok:
            print(f"   Gemini: {gemini_result.get('error', 'unknown')}")
        if not groq_ok:
            print(f"   Groq: {groq_result.get('error', 'unknown')}")
        return 1
    else:
        print("[FAIL] BOTH CLOUD PROVIDERS FAILING")
        if not gemini_key and not groq_key:
            print("   No API keys configured in .env")
        else:
            if not gemini_ok:
                print(f"   Gemini: {gemini_result.get('error', 'unknown')}")
            if not groq_ok:
                print(f"   Groq: {groq_result.get('error', 'unknown')}")
        print("   System will use local fallback.")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)