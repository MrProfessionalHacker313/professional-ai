# Professional AI - Offline Mode Setup Guide

## World-First Feature: Complete Offline AI

Professional AI now works WITHOUT internet. All AI features run on your device using local models.

---

## Features

### 1. On-Device AI Engine (No Internet Required)
- **Chat**: phi3-mini (1.8B), qwen2.5:3b, llama3.2:3b, gemma2:2b
- **Code**: qwen2.5-coder:3b (fast, high quality code generation)
- **Voice**: Vosk offline speech recognition (Urdu, Hindi, English, 20+ languages)
- **Translation**: Opus-MT offline translation (40+ languages)

### 2. Low-Internet Mode (2G/3G/Slow Connections)
- Compressed responses (gzip/brotli)
- Streaming responses (text appears instantly)
- Local caching (repeat questions load instantly)
- Priority mode (short answers first, then expands)

### 3. Sync System
- Offline work saved locally (encrypted)
- Auto-syncs to cloud when internet returns
- No data loss ever

---

## Quick Setup

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM (16GB recommended for multiple offline models)
- 10GB+ storage for models

### Step 1: Update Docker Compose

```bash
cd "C:\Users\GrafiX\Desktop\professional-ai"
docker-compose up -d
```

### Step 2: Pull Offline Models

```bash
# Pull small chat models (required for offline mode)
docker exec -it pro-ai-ollama ollama pull phi3:mini
docker exec -it pro-ai-ollama ollama pull qwen2.5:3b
docker exec -it pro-ai-ollama ollama pull llama3.2:3b
docker exec -it pro-ai-ollama ollama pull gemma2:2b

# Pull code model (for offline code generation)
docker exec -it pro-ai-ollama ollama pull qwen2.5-coder:3b

# Download voice models (for offline voice)
# Available languages: en, ur, hi, ar, es, fr, de, ru, zh, ja, ko
curl -X POST http://localhost:8000/api/offline/voice/models/download/en
curl -X POST http://localhost:8000/api/offline/voice/models/download/ur
curl -X POST http://localhost:8000/api/offline/voice/models/download/hi
```

### Step 3: Install Python Dependencies

```bash
cd backend
pip install vosk soundfile numpy transformers torch sentencepiece cryptography
```

### Step 4: Start the Application

```bash
# Start all services
docker-compose up -d

# Or start just the backend (if Ollama is running locally)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## How It Works

### Automatic Mode Switching

```
Internet Available?
    ├── YES → Use cloud models (Gemini/GPT/Groq)
    │         - Ultra powerful
    │         - Streaming responses
    │         - Voice + Translation online
    │
    └── NO  → Use offline models (Ollama local)
              - phi3-mini for chat
              - qwen2.5-coder:3b for code
              - Vosk for voice
              - Opus-MT for translation
```

### Low Bandwidth Mode

```
Slow Connection Detected?
    ├── YES → Activate low bandwidth mode
    │         - Compress responses
    │         - Use smaller models
    │         - Cache everything locally
    │         - Short answers first, then expand
    │
    └── NO  → Normal mode
```

---

## API Endpoints

### Offline Mode Status
```
GET /api/offline/status
```

### Offline Chat (Works Without Internet)
```
POST /api/offline/chat
{
  "prompt": "Hello",
  "mode": "chat",
  "model": "phi3:mini"
}
```

### Offline Voice Transcription
```
POST /api/offline/voice/transcribe
{
  "audio_base64": "<base64_audio>",
  "language": "en"
}
```

### Offline Translation
```
POST /api/offline/translate
{
  "text": "Hello world",
  "source_lang": "en",
  "target_lang": "ur"
}
```

### Sync Queue
```
POST /api/offline/sync/queue
{
  "item_type": "chat_message",
  "data": { "prompt": "...", "response": "..." }
}
```

### Download Voice Model
```
POST /api/offline/voice/models/download/{language_code}
```

---

## Mobile App Setup

### React Native / Flutter

```javascript
// React Native example
import { useOfflineMode } from './hooks/useOfflineMode';

function App() {
  const { isOffline, generateResponse, transcribeVoice } = useOfflineMode();

  return (
    <View>
      <StatusBar mode={isOffline ? "offline" : "online"} />
      <ChatInterface
        onSendMessage={generateResponse}
        onVoiceInput={transcribeVoice}
      />
    </View>
  );
}
```

```dart
// Flutter example
import 'package:professional_ai/offline_mode.dart';

void main() {
  runApp(OfflineModeProvider(
    child: MyApp(),
  ));
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final offline = OfflineMode.of(context);

    return MaterialApp(
      home: Scaffold(
        body: ChatScreen(
          isOffline: offline.isOffline,
          onSendMessage: offline.generateResponse,
        ),
      ),
    );
  }
}
```

---

## Model Sizes

| Model | Size | Use Case | RAM Required |
|-------|------|----------|--------------|
| phi3:mini | 2.3GB | General chat | 4GB |
| qwen2.5:3b | 2GB | Balanced chat | 4GB |
| llama3.2:3b | 2GB | General purpose | 4GB |
| gemma2:2b | 1.4GB | Lightweight chat | 2GB |
| qwen2.5-coder:3b | 2GB | Code generation | 4GB |
| llama3.2:1b | 0.7GB | Ultra lightweight | 1GB |

---

## Voice Models (Vosk)

| Language | Model Size | Download |
|----------|-----------|----------|
| English | 40MB | `curl -X POST .../download/en` |
| Urdu | 35MB | `curl -X POST .../download/ur` |
| Hindi | 45MB | `curl -X POST .../download/hi` |
| Arabic | 35MB | `curl -X POST .../download/ar` |
| Spanish | 40MB | `curl -X POST .../download/es` |
| French | 40MB | `curl -X POST .../download/fr` |

---

## Translation Models (Opus-MT)

| Pair | Size | Use Case |
|------|------|----------|
| en-ur | 300MB | English to Urdu |
| ur-en | 300MB | Urdu to English |
| en-hi | 300MB | English to Hindi |
| hi-en | 300MB | Hindi to English |
| en-es | 300MB | English to Spanish |
| en-fr | 300MB | English to French |
| en-de | 300MB | English to German |
| en-ar | 300MB | English to Arabic |

---

## Frontend Integration

### 1. Wrap App with OfflineModeProvider

```tsx
// app/providers.tsx
import { OfflineModeProvider } from "@/components/OfflineModeProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <OfflineModeProvider>
      {children}
    </OfflineModeProvider>
  );
}
```

### 2. Use the Hook

```tsx
// components/ChatInterface.tsx
import { useOffline } from "@/hooks/useOfflineMode";

function ChatInterface() {
  const { isOffline, generateResponse, transcribeVoice } = useOffline();

  const handleSend = async (message: string) => {
    const response = await generateResponse(message, {
      mode: "chat",
      model: isOffline ? "phi3:mini" : undefined,
    });
    console.log(response);
  };

  return (
    <div>
      {isOffline && <OfflineStatusBar />}
      <ChatInput onSend={handleSend} />
    </div>
  );
}
```

### 3. Show Status Bar

```tsx
import { OfflineStatusBar } from "@/components/OfflineStatusBar";

function Header() {
  return (
    <header className="flex justify-between items-center">
      <h1>Professional AI</h1>
      <OfflineStatusBar />
    </header>
  );
}
```

---

## Configuration

### Backend (.env)

```env
# Offline Mode
OFFLINE_MODE_ENABLED=true
OFFLINE_CACHE_DIR=./data/offline_cache
OFFLINE_SYNC_DIR=./data/sync_queue
OFFLINE_VOICE_MODELS_DIR=./data/voice_models
OFFLINE_TRANSLATION_MODELS_DIR=./data/translation_models
OFFLINE_COMPRESSION_ENABLED=true
OFFLINE_STREAMING_ENABLED=true
OFFLINE_AUTO_SYNC=true
OFFLINE_PRIORITY_MODE=true
```

### Frontend (next.config.js)

```js
module.exports = {
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
};
```

---

## Testing Offline Mode

### Test Offline Chat
```bash
# Start Ollama locally
ollama serve

# Pull models
ollama pull phi3:mini
ollama pull qwen2.5-coder:3b

# Test offline chat
curl -X POST http://localhost:8000/api/offline/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "mode": "chat"}'
```

### Test Offline Voice
```bash
# Download voice model
curl -X POST http://localhost:8000/api/offline/voice/models/download/en

# Test transcription (send audio file)
curl -X POST http://localhost:8000/api/offline/voice/transcribe \
  -H "Content-Type: application/json" \
  -d '{"audio_base64": "<base64>", "language": "en"}'
```

### Test Offline Translation
```bash
curl -X POST http://localhost:8000/api/offline/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "source_lang": "en", "target_lang": "ur"}'
```

---

## Performance Tips

### For Phones/Tablets (Low RAM)
```bash
# Use ultra-lightweight models
ollama pull llama3.2:1b  # 700MB, runs on 1GB RAM
ollama pull gemma2:2b    # 1.4GB, runs on 2GB RAM
```

### For Laptops (Medium RAM)
```bash
# Use balanced models
ollama pull qwen2.5:3b     # 2GB
ollama pull qwen2.5-coder:3b  # 2GB
```

### For Desktops (High RAM)
```bash
# Use larger models for better quality
ollama pull llama3.2:3b    # 2GB
ollama pull phi3:mini      # 2.3GB
```

---

## Troubleshooting

### Models Not Loading
```bash
# Check Ollama status
docker logs pro-ai-ollama

# Pull models manually
docker exec -it pro-ai-ollama ollama pull phi3:mini
```

### Voice Not Working
```bash
# Install Vosk dependencies
pip install vosk soundfile numpy

# Download voice models
curl -X POST http://localhost:8000/api/offline/voice/models/download/en
```

### Translation Not Working
```bash
# Install transformers
pip install transformers torch sentencepiece

# First download will take time (model is ~300MB)
```

### Low Memory
```bash
# Remove GPU requirement from docker-compose.yml
# Edit docker-compose.yml and remove nvidia device reservations
# Models will run on CPU (slower but works)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Professional AI                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐ │
│  │   Frontend  │    │   Backend    │    │    Ollama     │ │
│  │  (Next.js)  │◄───│  (FastAPI)   │───►│  (Local LLM) │ │
│  └─────────────┘    └──────────────┘    └───────────────┘ │
│         │                  │                     │         │
│         │                  │              ┌──────┴──────┐  │
│         │                  │              │   Models    │  │
│         │                  │              │ • phi3-mini │  │
│         │                  │              │ • qwen2.5   │  │
│         │                  │              │ • llama3.2  │  │
│         │                  │              │ • gemma2    │  │
│         │                  │              │ • coder:3b  │  │
│         │                  │              └─────────────┘  │
│         │                  │                                │
│  ┌──────┴──────┐           │    ┌────────────────────────┐ │
│  │   Offline   │           │    │   Offline Services     │ │
│  │   Storage   │           │    │                        │ │
│  │  (IndexedDB)│           │    │  • Vosk (Voice)        │ │
│  └─────────────┘           │    │  • Opus-MT (Translate) │ │
│                             │    │  • Cache (File-based)  │ │
│  ┌─────────────┐           │    │  • Sync (Cloud when up)│ │
│  │   Browser   │           │    └────────────────────────┘ │
│  │  (Online/   │           │                                │
│  │   Offline)  │           │    Auto-switches based on     │
│  └─────────────┘           │    internet connectivity      │
│                             └───────────────────────────────┘
```

---

## What Makes This World-First

1. **True Offline AI**: All features work without internet after initial setup
2. **Automatic Switching**: Seamlessly switches between online/offline models
3. **Multi-Language Voice**: Vosk supports Urdu/Hindi/English + 20+ languages
4. **No Data Loss**: Encrypted local storage + auto-sync when online
5. **Low Bandwidth Mode**: Compressed responses, cached data, streaming
6. **Mobile + Desktop**: Works on phones, laptops, and desktops
7. **Privacy First**: All data stays on device when offline

---

## Next Steps

1. Pull the offline models you need
2. Download voice models for your language
3. Test in offline mode (disconnect internet)
4. Configure sync settings
5. Enjoy unlimited AI without internet!
