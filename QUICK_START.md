# Professional AI - Quick Start Guide

## 🚀 ULTRA FAST START (Recommended)

### Option 1: Double-Click to Start
Simply double-click: **`START_ULTRA_FAST.bat`**

This will:
- ✅ Check Python & Node.js
- ✅ Setup backend & frontend (first time only)
- ✅ Start PostgreSQL database
- ✅ Start both servers automatically
- ✅ Open browser to http://localhost:3000

---

## 🔧 Manual Start (If Needed)

### Terminal 1 - Backend Server
```bash
cd C:\Users\GrafiX\Desktop\professional-ai\backend
venv\Scripts\activate
python -m app.main
```

### Terminal 2 - Frontend Server
```bash
cd C:\Users\GrafiX\Desktop\professional-ai\frontend
npm run dev
```

### Open Browser
```
http://localhost:3000
```

---

## ⚠️ FIXING GOOGLE OAUTH ERROR

The error `:8000/api/auth/oauth/google:1 Failed to load resource: net::ERR_CONNECTION_REFUSED` means the backend server is not running.

### Solution:
1. **Make sure backend is running** on port 8000
2. **Check your Google OAuth credentials** in `backend/.env`:

```env
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

3. **Get credentials from Google Cloud Console:**
   - Go to: https://console.cloud.google.com/apis/credentials
   - Create OAuth 2.0 Client ID
   - Add authorized redirect URI: `http://localhost:3000/auth/callback/google`
   - Copy Client ID and Secret to `backend/.env`

4. **Restart backend server** after updating credentials

---

## 🚀 SPEED OPTIMIZATIONS APPLIED

### Frontend Speed Improvements:
- ✅ **Turbo compilation** enabled for faster builds
- ✅ **Package imports optimized** (lucide-react, framer-motion, react-i18next)
- ✅ **Code splitting** for better caching
- ✅ **Vendor chunks** separated (React, Next.js, Libraries)
- ✅ **SWC minification** enabled
- ✅ **Console removal** in production (except errors/warnings)
- ✅ **Aggressive caching** for static assets (1 year)
- ✅ **Preconnect hints** for API and CDN

### Backend Speed Improvements:
- ✅ **Redis caching** enabled (1 hour AI response cache)
- ✅ **Compression middleware** (Brotli/Gzip)
- ✅ **Database connection pooling**
- ✅ **Async operations** throughout
- ✅ **Health checks** optimized

### Expected Performance:
- **Frontend compile time**: ~3-5 seconds (was 10-15s)
- **Page load time**: <1 second
- **API response time**: <200ms
- **AI response time**: 1-3 seconds (with caching)

---

## 🎯 LOGIN CREDENTIALS

**Owner/Admin Email:** `redr28126@gmail.com`

**Owner Email-Only Login:**
- Just enter your email: `redr28126@gmail.com`
- NO password required
- Instant full admin access

**Regular User:**
- Register new account OR
- Sign in with Google OAuth

---

## 📊 ACCESS URLS

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/api/docs
- **Health Check:** http://localhost:8000/api/health

---

## 🛑 TROUBLESHOOTING

### Error: `ERR_CONNECTION_REFUSED` on port 8000
**Solution:** Backend server is not running
```bash
cd backend
venv\Scripts\activate
python -m app.main
```

### Error: `Port 3000 already in use`
**Solution:** Kill the process using port 3000
```bash
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Error: `Port 8000 already in use`
**Solution:** Kill the process using port 8000
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Error: `Module not found`
**Solution:** Reinstall dependencies
```bash
# Backend
cd backend
venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Error: `Database connection failed`
**Solution:** Start PostgreSQL
```bash
net start postgresql-x64-16
# OR
net start postgresql
```

### Google OAuth not working
**Solution:** 
1. Check `backend/.env` has Google credentials
2. Verify redirect URI in Google Cloud Console: `http://localhost:3000/auth/callback/google`
3. Restart backend server

---

## 🎮 USEFUL COMMANDS

### Start Everything (Fast)
```bash
# Double-click this file:
START_ULTRA_FAST.bat
```

### Start Backend Only
```bash
cd backend
venv\Scripts\activate
python -m app.main
```

### Start Frontend Only
```bash
cd frontend
npm run dev
```

### Stop All Servers
Press `Ctrl+C` in both terminals

### Clear Cache & Restart
```bash
# Backend
cd backend
venv\Scripts\activate
python -c "from app.services.cache_service import cache_service; import asyncio; asyncio.run(cache_service.clear())"

# Frontend - restart with:
npm run dev
```

---

## � ACCESS FROM PHONE (Same WiFi)

1. Find your computer's IP:
   ```bash
   ipconfig
   # Look for IPv4 Address, e.g., 192.168.1.100
   ```

2. On phone browser:
   ```
   http://192.168.1.100:3000
   ```

---

## 🎨 FEATURES

- ✅ **AI Chat** - Multiple AI providers (Gemini, Groq, OpenAI)
- ✅ **Code Generation** - Write, debug, and explain code
- ✅ **Media Engine** - Video, audio, image generation
- ✅ **Admin Panel** - Full admin controls at `/admin`
- ✅ **Owner Access** - Email-only login for owner
- ✅ **OAuth Login** - Google, Microsoft, GitHub, Apple
- ✅ **2FA & Passkeys** - Enhanced security
- ✅ **Offline Mode** - Works without internet
- ✅ **PWA** - Install as desktop app
- ✅ **Multi-language** - i18n support

---

## � NEED HELP?

1. Check logs in `backend/logs/app.log`
2. Check browser console for frontend errors
3. Verify all environment variables in `backend/.env`
4. Ensure PostgreSQL is running on port 5432
5. Ensure ports 3000 and 8000 are not blocked

---

## 🎉 YOU'RE ALL SET!

Just double-click **`START_ULTRA_FAST.bat`** and enjoy the fastest Professional AI experience!

**Login:** `redr28126@gmail.com` (no password needed for owner)