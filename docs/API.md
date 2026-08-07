# Professional AI - API Documentation

## Base URL
Development: `http://localhost:8000`
Production: `https://api.professionalai.com`

## Authentication
All protected endpoints require a Bearer JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | Login with email/password | No |
| POST | `/api/auth/refresh` | Refresh access token | No |
| POST | `/api/auth/logout` | Logout user | Yes |
| GET | `/api/auth/me` | Get current user profile | Yes |
| POST | `/api/auth/oauth/{provider}` | OAuth login URL | No |
| POST | `/api/auth/2fa/setup` | Setup TOTP 2FA | Yes |
| POST | `/api/auth/2fa/verify` | Verify and enable 2FA | Yes |
| POST | `/api/auth/2fa/disable` | Disable 2FA | Yes |

### AI Chat (`/api/chat`)

| Method | Endpoint | Description | Auth | Rate Limit |
|--------|----------|-------------|------|------------|
| POST | `/api/chat/send` | Send message to AI | Yes | 100/min |
| POST | `/api/chat/code` | Generate code | Yes | 3/day (free) |
| POST | `/api/chat/bugfix` | Fix buggy code | Yes | 100/min |
| POST | `/api/chat/security` | Security query | Yes | 100/min |
| POST | `/api/chat/stream` | Stream AI response | Yes | 100/min |

### Payments (`/api/payments`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/payments/create-subscription` | Create PRO subscription | Yes |
| POST | `/api/payments/cancel` | Cancel subscription | Yes |
| GET | `/api/payments/status` | Get subscription status | Yes |
| POST | `/api/payments/retry-failed` | Retry failed payment | Yes |
| POST | `/api/payments/stripe/webhook` | Stripe webhook | No (signature) |

### Admin (`/api/admin`) - Owner Only

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/users` | List all users |
| POST | `/api/admin/approve/{email}` | Approve user |
| POST | `/api/admin/disapprove/{email}` | Disapprove user |
| POST | `/api/admin/ban/{email}` | Ban user |
| GET | `/api/admin/revenue` | View revenue stats |
| POST | `/api/admin/refund/{transaction_id}` | Process refund |
| GET | `/api/admin/vault/{email}` | View user vault |
| GET | `/api/admin/analytics` | Usage analytics |
| GET | `/api/admin/tickets` | List support tickets |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |

### Next-Gen Features (`/api/features`)

#### Language Brain

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/features/language/detect` | Detect input language | Yes |
| POST | `/api/features/language/auto-translate` | Auto-translate text | Yes |
| GET | `/api/features/language/profile` | Get user language profile | Yes |
| POST | `/api/features/language/reply-native` | Auto-reply in user's native language | Yes |

#### Live Hacking Lab (Educational/Safe)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/features/hacking-lab/sessions` | Create safe lab session (`sqli`, `xss`, `brute_force`) | Yes |
| POST | `/api/features/hacking-lab/attack` | Run simulated attack step with defensive feedback | Yes |
| GET | `/api/features/hacking-lab/sessions` | List lab sessions | Yes |
| GET | `/api/features/hacking-lab/sessions/{session_id}` | Get session details/progress | Yes |

#### Screenshot -> App

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/features/screenshot-to-app` | Generate app from screenshot (`framework`, `styling`, `include_api`, `include_auth`) | Yes |
| GET | `/api/features/screenshot-to-app/{app_id}` | Get app generation status | Yes |

#### AI Detective

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/features/detective/analyze-file` | Analyze suspicious file | Yes |
| POST | `/api/features/detective/analyze-link` | Analyze suspicious URL | Yes |
| POST | `/api/features/detective/analyze-email` | Analyze suspicious email | Yes |
| GET | `/api/features/detective/history` | List past analyses | Yes |

#### Voice Command + Voice Clone

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/features/voice-command/start` | Start voice command session | Yes |
| POST | `/api/features/voice-command/process` | Process voice command (audio or text fallback) | Yes |
| GET | `/api/features/voice-command/history` | Voice command history | Yes |
| POST | `/api/features/voice-clone/create` | Create voice clone (explicit consent required) | Yes |
| POST | `/api/features/voice-clone/synthesize` | Synthesize speech from clone | Yes |
| GET | `/api/features/voice-clone/clones` | List user voice clones | Yes |

#### Memory Vault / Multi-Task / Teacher / Business

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/features/memory-vault/backup` | Encrypted memory backup | Yes |
| POST | `/api/features/memory-vault/restore` | Restore memory backup | Yes |
| GET | `/api/features/memory-vault/backups` | List backups | Yes |
| POST | `/api/features/multi-task/execute` | Execute task batch | Yes |
| GET | `/api/features/multi-task/batches` | List batches | Yes |
| GET | `/api/features/multi-task/batches/{batch_id}` | Get batch details | Yes |
| POST | `/api/features/teacher/courses` | Create AI course | Yes |
| GET | `/api/features/teacher/courses` | List courses | Yes |
| GET | `/api/features/teacher/courses/{course_id}/progress` | Course progress | Yes |
| POST | `/api/features/business/plan` | Generate business plan | Yes |
| POST | `/api/features/business/strategy` | Generate marketing strategy | Yes |
| GET | `/api/features/business/plans` | List plans | Yes |

#### Formats / Compatibility / Smart Router / News

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/features/format/generate` | Generate/convert files (includes JSON<->CSV path) | Yes |
| GET | `/api/features/format/files` | List generated files | Yes |
| GET | `/api/features/format/files/{file_id}/download` | Download generated file metadata | Yes |
| POST | `/api/features/compatibility/check` | Check target compatibility | Yes |
| POST | `/api/features/compatibility/fix` | Apply compatibility fix workflow | Yes |
| GET | `/api/features/compatibility/history` | Compatibility history | Yes |
| GET | `/api/features/smart-router/device-profile` | Get device profile | Yes |
| POST | `/api/features/smart-router/select-model` | Select model by task + device hints | Yes |
| POST | `/api/features/smart-router/route` | Create smart route record | Yes |
| GET | `/api/features/smart-router/models` | List available router models | Yes |
| POST | `/api/features/news/subscribe` | Subscribe to topics | Yes |
| POST | `/api/features/news/digest` | Generate digest from subscriptions | Yes |
| GET | `/api/features/news/history` | Digest history | Yes |
| GET | `/api/features/news/latest` | Latest articles list | Yes |

### Frontend SEO Routes (Generated by Next.js)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/robots.txt` | Crawl policy and sitemap reference |
| GET | `/sitemap.xml` | Sitemap with localized URLs |

## Request/Response Examples

### Register
```json
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "display_name": "John Doe"
}
```

### Login
```json
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "totp_code": "123456"  // optional, required if 2FA enabled
}
```

### Generate Code
```json
POST /api/chat/code
{
  "prompt": "Build a REST API with FastAPI",
  "language": "python",
  "framework": "FastAPI"
}
```

### Fix Bug
```json
POST /api/chat/bugfix
{
  "code": "def add(a, b): return a + b",
  "error_description": "TypeError when adding strings",
  "language": "python"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad request |
| 401 | Unauthorized |
| 403 | Forbidden (banned/disabled) |
| 404 | Not found |
| 409 | Conflict (email exists) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable (AI providers) |

## Rate Limits
- General: 100 requests/minute per user
- Code generation (free): 3 prompts/day
- Code generation (PRO): Unlimited