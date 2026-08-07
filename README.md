# Professional AI (PRO AI)

**World's most powerful all-in-one AI assistant.** Code generation, cybersecurity analysis, bug fixing, and expert guidance — all in one production-ready SaaS platform.

## Features

- **🤖 Code Generation** — Complete, production-ready code in any language
- **🛡️ Cybersecurity Expert** — Ethical hacking, vulnerability analysis, defense
- **🐛 Bug Fixer** — Root cause analysis + complete corrected code
- **🌐 Multi-Provider AI** — Gemini, OpenAI, Groq, Ollama (auto-failover)
- **🔒 Enterprise Security** — AES-256-GCM, OAuth + 2FA + Passkeys, TLS 1.3
- **💳 Flexible Payments** — Stripe, PayPal, JazzCash, Easypaisa, Sadapay, NayaPay
- **🌍 35+ Languages** — Always free: Urdu, English, Hindi, Bengali
- **📱 PWA Ready** — Installable on mobile and desktop

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL with async SQLAlchemy
- **Cache:** Redis (rate limiting, session store)
- **Auth:** JWT, OAuth (Google, Microsoft, GitHub, Apple, Facebook)
- **AI:** Gemini API, OpenAI API, Groq API, Ollama (self-hosted)
- **Payments:** Stripe, PayPal, JazzCash, Easypaisa, Sadapay, NayaPay

### Frontend
- **Framework:** Next.js 14 (React 18)
- **Styling:** Tailwind CSS 3.4
- **Auth:** NextAuth.js
- **State:** React Context + Local Storage
- **HTTP:** Axios with interceptors

### Deployment
- **Cloud:** Google Cloud Run
- **Database:** Cloud SQL (PostgreSQL)
- **Cache:** Memorystore (Redis)
- **Storage:** Cloud Storage
- **Secrets:** Secret Manager
- **CDN:** Cloud CDN

## Project Structure

```
professional-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment configuration
│   │   ├── database.py          # Database engine & sessions
│   │   ├── middleware/
│   │   │   └── security.py      # Security headers, rate limiting
│   │   ├── models/
│   │   │   ├── user.py          # User, OAuth, 2FA, Passkeys, Sessions
│   │   │   ├── subscription.py  # Subscription & billing
│   │   │   ├── usage.py         # Usage logs & counters
│   │   │   ├── vault.py         # Encrypted vault storage
│   │   │   ├── revenue.py       # Revenue & refunds
│   │   │   └── support.py       # Support tickets
│   │   ├── services/
│   │   │   ├── auth_service.py   # Auth logic (JWT, OAuth, 2FA)
│   │   │   └── ai_service.py    # Multi-provider AI engine
│   │   └── routes/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── chat.py          # AI chat & code generation
│   │       ├── admin.py         # Admin panel endpoints
│   │       └── payments.py      # Subscription & payment endpoints
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx         # Landing page
│   │   │   ├── globals.css
│   │   │   ├── login/page.tsx   # Login/Register
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── pricing/page.tsx
│   │   │   └── admin/page.tsx
│   │   ├── components/
│   │   │   └── ui/
│   │   │       ├── ChatInterface.tsx
│   │   │       ├── Navbar.tsx
│   │   │       └── CodeBlock.tsx
│   │   └── lib/
│   │       └── api.ts           # API client
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── database/
│   └── schema.sql               # Complete PostgreSQL schema
├── deploy/
│   └── cloud-run.yaml           # Google Cloud Run config
└── docs/
    └── API.md                   # API documentation
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Backend Setup

```bash
# Clone and enter backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run database migration
# First, create the database:
# createdb professional_ai
# Then run the schema:
psql -d professional_ai -f ../database/schema.sql

# Start the server
python -m app.main
# Server runs at http://localhost:8000
```

### Frontend Setup

```bash
# Enter frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
# App runs at http://localhost:3000
```

### Docker Deployment

```bash
# Build backend image
docker build -t professional-ai-backend ./backend

# Run with Docker
docker run -p 8000:8000 --env-file ./backend/.env professional-ai-backend
```

### Google Cloud Deployment

```bash
# Set project
gcloud config set project PROJECT_ID

# Enable required services
gcloud services enable run.googleapis.com sqladmin.googleapis.com redis.googleapis.com

# Create Cloud SQL instance
gcloud sql instances create professional-ai-db --database-version=POSTGRES_15 --tier=db-custom-2-7680

# Create database
gcloud sql databases create professional_ai --instance=professional-ai-db

# Run schema
gcloud sql connect professional-ai-db --user=postgres < database/schema.sql

# Create Redis instance
gcloud redis instances create professional-ai-redis --size=1 --region=us-central1

# Deploy backend
gcloud run deploy professional-ai-backend \
  --source=./backend \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated

# Deploy frontend
cd frontend && npm run build
gcloud run deploy professional-ai-frontend \
  --source=. \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated
```

## API Documentation

See [docs/API.md](docs/API.md) for complete API documentation.

## Environment Variables

See [backend/.env.example](backend/.env.example) for all required environment variables.

## License

Proprietary. All rights reserved.