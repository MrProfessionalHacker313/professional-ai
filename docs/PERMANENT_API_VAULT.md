# PERMANENT API VAULT — Endpoints & Architecture

## ✅ PERMANENT API VAULT ACTIVE — providers fail over automatically, keys never run out, final fallback is on-device AI, the system NEVER stops and NEVER expires.

---

## Provider Chain (Multi-Layer, Auto-Failover)

| Layer | Provider | Model | Cost | Key Rotation |
|-------|----------|-------|------|--------------|
| 1 | **Gemini** (Google AI Studio) | `gemini-2.5-flash` (chat) / `gemini-2.5-pro` (code) | Free tier | `GEMINI_KEYS=key1,key2,key3` |
| 2 | **Groq** | `llama-3.3-70b-versatile` | Free tier | `GROQ_KEYS=key1,key2` |
| 3 | **OpenRouter** | `deepseek/deepseek-chat` / `qwen/qwen2.5-coder-32b-instruct` | Free models | `OPENROUTER_KEYS=key1,key2,key3` |
| 4 | **Local ONNX / Knowledge Engine** | `qwen2.5-0.5b-instruct` / `qwen2.5-coder-1.5b` | **ZERO cost, ZERO expiry** | N/A — always available |

**Routing:** Each provider has a **2-second timeout** → fail → next provider → if ALL cloud fail → **local model answers**. User never sees an error, never sees the switch.

---

## Endpoints

### Vault Status & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/vault/status` | Full vault status: provider chain, local fallback, call logs |
| `GET` | `/api/vault/health` | Provider health + health monitor status |
| `GET` | `/api/vault/logs` | Recent API call logs (provider, latency, cost) |
| `GET` | `/api/vault/key-refresh-reminder` | Monthly key refresh reminder with one-click links |
| `GET` | `/api/vault/local-fallback` | Local fallback engine status |

### Existing AI Endpoints (unchanged)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Chat with AI (uses vault provider chain) |
| `POST` | `/api/chat/stream` | Stream AI response (SSE) |
| `GET` | `/api/health` | Health check (includes offline mode status) |
| `GET` | `/api/health/ready` | Kubernetes readiness probe |
| `GET` | `/api/health/live` | Kubernetes liveness probe |

---

## Endless Keys System

```env
# Add unlimited keys per provider — no code change needed
GEMINI_KEYS=key1,key2,key3,key4,key5
GROQ_KEYS=key1,key2,key3
OPENROUTER_KEYS=key1,key2,key3,key4
```

- System uses `key1` → when rate-limited, switches to `key2`, `key3`, then next provider.
- Owner can add unlimited keys in `.env` / Secret Manager — **no code change**.
- Health monitor pings all providers every **60 seconds**, marks dead ones inactive, auto-revives when healthy.
- Monthly key refresh reminder in owner dashboard: *"Add free keys at aistudio.google.com / console.groq.com"* — one click each, keeps quota topped up forever at zero cost.

---

## No Expiry — No Break Guarantee

- Requests queue during any momentary outage (**max 5 seconds**) → then auto-resume with next provider.
- Never a mid-response cut.
- All API calls logged (provider, latency, cost) in owner dashboard.

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `backend/app/services/ai_router.py` | **Permanent Vault Router** — provider chain, timeout, failover, key rotation, local fallback |
| `backend/app/services/local_fallback.py` | **Local ONNX / knowledge engine** — final fallback, never stops |
| `backend/app/services/vault_logger.py` | **Call logger** — provider, latency, cost for owner dashboard |
| `backend/app/services/vault_health_monitor.py` | **Health monitor** — pings all providers every 60s, auto-revive |
| `backend/app/routes/vault.py` | **Vault endpoints** — status, health, logs, key refresh reminder |
| `backend/app/config.py` | **Vault config** — multi-key env vars, local fallback settings, routing settings |
| `backend/app/services/ai_service.py` | **Updated** — starts vault health monitor |
| `backend/app/main.py` | **Updated** — registers vault routes |
| `backend/.env.vault.example` | **Key management example** — multi-key setup guide |

---

## Configuration

```env
# Routing
VAULT_TIMEOUT_SECONDS=2.0          # Per-provider timeout before failover
VAULT_QUEUE_MAX_SECONDS=5.0        # Max queue time during outage
VAULT_HEALTH_CHECK_INTERVAL_SECONDS=60  # Health monitor ping interval
VAULT_LOG_ENABLED=true             # Log all API calls
VAULT_KEY_REFRESH_REMINDER_DAYS=30 # Monthly key refresh reminder

# Local fallback
LOCAL_FALLBACK_ENABLED=true
LOCAL_MODELS_DIR=./data/local_models
LOCAL_CHAT_MODEL=qwen2.5-0.5b-instruct
LOCAL_CODE_MODEL=qwen2.5-coder-1.5b
```

---

## Guarantee

> **✅ PERMANENT API VAULT ACTIVE — providers fail over automatically, keys never run out, final fallback is on-device AI, the system NEVER stops and NEVER expires.**