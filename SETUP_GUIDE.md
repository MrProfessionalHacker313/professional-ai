# Professional AI - Complete Setup Guide

## 🚀 Quick Start (3 Simple Steps)

### Step 1: Install Docker
Run `INSTALL_DOCKER.bat` or install Docker Desktop manually from:
https://www.docker.com/products/docker-desktop/

**After installation:**
- Restart your computer
- Open Docker Desktop
- Wait for it to fully load (whale icon in system tray)

### Step 2: Configure Google OAuth (Optional but Recommended)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable "Google+ API"
4. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/api/auth/callback/google`
   - Authorized JavaScript origins: `http://localhost:8000`
5. Copy Client ID and Client Secret
6. Edit `.env` file and replace:
   ```
   GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-actual-client-secret
   ```

### Step 3: Start the Application

**Option A: Double-click `START.bat`**

**Option B: Run from command prompt:**
```bash
docker-compose up --build
```

## ✅ Access Your AI

After startup completes (2-3 minutes), open your browser:

**Main Application:** http://localhost:8000
**Login Page:** http://localhost:8000/login
**Dashboard:** http://localhost:8000/dashboard
**AI Chat:** http://localhost:8000/chat

## 🔐 Owner Admin Access

Your email is configured as owner/admin: **redr28126@gmail.com**

**First Login:**
1. Go to http://localhost:8000/login
2. Click "Sign in with Google" (if configured)
3. Or register with email/password
4. Owner account will be auto-created with admin privileges

**Default Owner Credentials (if using email):**
- Email: redr28126@gmail.com
- Password: Check backend logs on first startup (temporary password)
- **Change password immediately after first login**

## 🎯 Features Available

### As Owner/Admin, you get:
- ✅ Unlimited AI chat (all modes)
- ✅ Code generation (unlimited)
- ✅ Security analysis
- ✅ Bug fixing
- ✅ All advanced features
- ✅ Admin panel access
- ✅ Priority support

### AI Modes:
1. **Chat Mode** - General conversation
2. **Code Mode** - Generate production-ready code
3. **Security Mode** - Cybersecurity analysis
4. **Bug Fix Mode** - Fix broken code

## 🔧 Configuration

### Add AI API Keys (Optional)
Edit `.env` to add API keys for better performance:

```env
# Gemini (Google AI)
GEMINI_API_KEY=your-key-here

# OpenAI
OPENAI_API_KEY=your-key-here

# Groq (Fast inference)
GROQ_API_KEY=your-key-here
```

**Get API Keys:**
- Gemini: https://makersuite.google.com/app/apikey
- OpenAI: https://platform.openai.com/api-keys
- Groq: https://console.groq.com/keys

### Email Configuration (Optional)
```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## 📱 Mobile & Desktop Access

### On Same Network:
1. Find your computer's IP address:
   ```bash
   ipconfig
   ```
2. Access from phone/tablet: `http://YOUR_IP:8000`

### Desktop App:
The app is PWA-ready. In Chrome/Edge:
1. Open http://localhost:8000
2. Click install icon in address bar
3. Install as desktop app

## 🛠️ Troubleshooting

### Docker not starting?
- Restart computer
- Enable virtualization in BIOS (if needed)
- Check Windows features: Hyper-V, WSL 2

### Port 8000 already in use?
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### AI not responding?
- Check if Ollama is running: `docker ps`
- View logs: `docker logs pro-ai-backend`
- Add cloud API keys (Gemini/OpenAI) for reliability

### Google Sign-In not working?
- Verify OAuth credentials in Google Cloud Console
- Check redirect URI matches exactly: `http://localhost:8000/api/auth/callback/google`
- Ensure Google+ API is enabled

## 📊 View Logs

```bash
# Backend logs
docker logs pro-ai-backend

# Database logs
docker logs pro-ai-postgres

# AI Engine logs
docker logs pro-ai-ollama

# All logs (follow)
docker-compose logs -f
```

## 🛑 Stop the Application

Press `Ctrl+C` in the terminal, or:
```bash
docker-compose down
```

## 🔄 Update and Restart

```bash
# Pull latest changes (if using git)
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build
```

## 📦 What's Running

Docker Compose starts these services:
- **PostgreSQL** (port 5432) - Database
- **Redis** (port 6379) - Cache & sessions
- **Ollama** (port 11434) - AI engine (Llama 3.1, Qwen 2.5, DeepSeek)
- **Backend** (port 8000) - FastAPI server

## 🌐 SEO & Google Visibility

Your AI is optimized for Google search:
- ✅ Complete SEO metadata
- ✅ Schema.org structured data
- ✅ Open Graph tags
- ✅ Twitter cards
- ✅ Sitemap ready
- ✅ Mobile responsive
- ✅ Fast loading

**To make it visible on Google:**
1. Deploy to production (Google Cloud, VPS, etc.)
2. Add domain (e.g., https://professionalai.com)
3. Submit to Google Search Console
4. Add sitemap.xml

## 🆘 Support

- Check logs first: `docker-compose logs -f`
- Review `.env` configuration
- Ensure all ports are available
- Restart Docker Desktop if needed

## 🎉 You're Ready!

Your Professional AI is now running with:
- ✅ Full authentication (email + Google OAuth)
- ✅ Admin/Owner access for redr28126@gmail.com
- ✅ Multi-mode AI chat
- ✅ Code generation
- ✅ Security analysis
- ✅ Bug fixing
- ✅ Docker containerization
- ✅ One-command startup
- ✅ SEO optimized
- ✅ Mobile & desktop ready

**Access now:** http://localhost:8000