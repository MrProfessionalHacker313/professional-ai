# ✅ LIGHT ENGINE ACTIVE — no Ollama on your PC, Gemini+Groq free tiers power everything, fast, no crashes.

## What Changed

The AI engine now runs in **LIGHT MODE**:
- **Ollama is DISABLED by default** (`OLLAMA_ENABLED=false`) — zero RAM usage, never starts on your PC.
- **Cloud free-tier providers** power everything: Gemini → Groq → OpenRouter.
- **Automatic failover**: if one provider fails/rate-limits/times out (2s), it auto-switches to the next.
- **If ALL fail**: you get "AI engine busy, try again" with a retry button — you never see downtime.
- **Repeated questions are cached locally** for instant answers.
- **Offline mode**: shows saved/cached answers + queues the question, answers when back online. No heavy local models.

---

## Step 1: Create Your Free API Keys (2 minutes)

### 1. Gemini API Key (Google AI Studio — FREE)
1. Go to: **https://aistudio.google.com/apikey**
2. Sign in with your Google account (or create one — free).
3. Click **"Create API key"**.
4. Copy the key (starts with `AIza...`).

### 2. Groq API Key (FREE, very fast)
1. Go to: **https://console.groq.com/keys**
2. Sign up / sign in (free).
3. Click **"Create API Key"**.
4. Copy the key (starts with `gsk_...`).

### 3. OpenRouter API Key (OPTIONAL — free models)
1. Go to: **https://openrouter.ai/keys**
2. Sign up / sign in (free).
3. Click **"Create Key"**.
4. Copy the key (starts with `sk-or-...`).

---

## Step 2: Paste Keys Into .env

Open your **`.env`** file (in the project root) and add:

```env
# ===================================================================
# AI ENGINE (LIGHT MODE)
# ===================================================================
AI_PROVIDER=auto
OLLAMA_ENABLED=false

# 1. Gemini (Google AI Studio - free tier)
GEMINI_API_KEY=PASTE_YOUR_GEMINI_KEY_HERE

# 2. Groq (free tier, very fast)
GROQ_API_KEY=PASTE_YOUR_GROQ_KEY_HERE

# 3. OpenRouter (optional - free models)
OPENROUTER_API_KEY=PASTE_YOUR_OPENROUTER_KEY_HERE
```

> **Tip**: You only need **Gemini** and **Groq** keys. OpenRouter is optional extra backup.

---

## Step 3: Restart the Backend

```bash
# Stop the current backend, then:
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You should see in the logs:
```
Light AI engine initialized with 2 providers: ['gemini', 'groq']
```

---

## How It Works

| Provider | Chat Model | Code Model | Speed |
|----------|-----------|------------|-------|
| **Gemini** (1st) | `gemini-2.5-flash` | `gemini-2.5-pro` | Fast |
| **Groq** (2nd) | `llama-3.3-70b-versatile` | `llama-3.3-70b-versatile` | Very Fast |
| **OpenRouter** (3rd) | `deepseek/deepseek-chat` | `qwen/qwen2.5-coder-32b-instruct` | Fast |

- **First provider** must respond in **under 3 seconds**.
- **Failover** adds **2 more seconds**.
- If **all fail** → `"AI engine busy, try again"` with retry button.

---

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `AI_PROVIDER` | `auto` | `auto` = Gemini→Groq→OpenRouter. Or force: `gemini`, `groq`, `openrouter` |
| `OLLAMA_ENABLED` | `false` | Set to `true` ONLY on a strong server for final fallback |
| `AI_TIMEOUT_SECONDS` | `3.0` | First provider timeout |
| `AI_FAILOVER_TIMEOUT_SECONDS` | `2.0` | Extra time for failover providers |
| `AI_CACHE_TTL_SECONDS` | `3600` | Cache repeated questions for 1 hour |
| `AI_MAX_TOKENS_CHAT` | `2048` | Max tokens for chat |
| `AI_MAX_TOKENS_CODE` | `8192` | Max tokens for code generation |

---

## Security Answers Mode

When you ask a question (what/how/explain/batao/kaise), the engine routes to **ANSWER MODE**:
- Theory + practical commands + purpose + power + defense.
- Code is generated **only** when you explicitly ask to build.

---

## Troubleshooting

**"No AI providers configured"**
→ You haven't added your API keys to `.env`. Follow Step 1 & 2.

**"AI engine busy, try again"**
→ All providers failed. Check your internet, or that your keys are valid. The retry button will try again.

**Want to use Ollama on a strong server later?**
→ Set `OLLAMA_ENABLED=true` in `.env`. It will be used as the final fallback after all cloud providers fail.