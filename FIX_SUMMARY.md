# Professional AI - Fix Summary & Quick Commands

## 🔧 Problems Fixed

### 1. Docker Not Starting
**Error:** `unable to get image 'postgres:16-alpine': failed to connect to the docker API`
**Fix:** Docker Desktop needs to be running before starting Professional AI

### 2. PowerShell Command Not Found
**Error:** `START_DOCKER.bat : The term 'START_DOCKER.bat' is not recognized`
**Fix:** PowerShell doesn't run .bat files from current directory. Use `.\START_DOCKER.bat` or use the new PowerShell script

### 3. AI Not Opening / Frontend Not Loading
**Root Cause:** `docker-compose.yml` mein frontend service missing tha
**Fix:** Added frontend service on port 3000 with hot-reload

### 4. Google/GitHub Login Failing
**Root Cause:** OAuth redirect URI mismatch and missing env vars
**Fix:** 
- Backend ab frontend ka actual `redirect_uri` use karta hai
- All OAuth env vars (GOOGLE_CLIENT_ID, GITHUB_CLIENT_ID, etc.) now passed to backend in Docker

### 5. Admin Login Failing
**Root Cause:** Owner email login was working but frontend was redirecting to wrong URL
**Fix:** Frontend now correctly opens at http://localhost:3000

---

## ✅ Quick Start Commands (PowerShell)

### Option 1: With Docker (RECOMMENDED - Fastest)

**Step 1: Start Docker Desktop**
```powershell
# Start Docker Desktop (if not already running)
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

**Step 2: Wait for Docker to be ready (30-60 seconds)**
```powershell
# Check if Docker is running
docker info
```

**Step 3: Start Professional AI**
```powershell
cd C:\Users\GrafiX\Desktop\professional-ai
.\START_DOCKER.bat
```

**OR use PowerShell script (auto-starts Docker if needed):**
```powershell
cd C:\Users\GrafiX\Desktop\professional-ai
.\START.ps1
```

**Access URLs:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/api/health

**Login:**
- Owner/Admin: `redr28126@gmail.com` (no password needed - just enter email)
- Regular users: Register with email or use Google/GitHub OAuth

**Stop:**
```powershell
cd C:\Users\GrafiX\Desktop\professional-ai
docker compose down
```

---

### Option 2: Without Docker (Manual Setup)

**Prerequisites:**
1. PostgreSQL 16 must be installed and running on port 5432
2. Redis must be installed and running on port 6379 (optional but recommended)
3. Python 3.11+ installed
4. Node.js 18+ installed

**Start Professional AI:**
```powershell
cd C:\Users\GrafiX\Desktop\professional-ai
.\START_ONE_CLICK_NO_DOCKER.bat
```

**OR use PowerShell script:**
```powershell
cd C:\Users\GrafiX\Desktop\professional-ai
.\START_NO_DOCKER.ps1
```

**Access URLs:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

**Stop:**
Press `Ctrl+C` in the terminal window

---

## 🔐 Google OAuth Setup (If Not Working)

If Google/GitHub login still doesn't work:

### 1. Get Google OAuth Credentials
1. Go to: https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID
3. Add these Authorized Redirect URIs:
   - `http://localhost:3000/auth/callback/google`
   - `http://localhost:8000/auth/callback/google`
4. Copy Client ID and Client Secret

### 2. Update backend/.env
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 3. For GitHub OAuth
1. Go to: https://github.com/settings/developers
2. Create OAuth App
3. Authorization callback URL: `http://localhost:3000/auth/callback/github`
4. Copy Client ID and Client Secret

### 5. Update backend/.env
```env
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### 6. Restart Professional AI
```powershell
# If using Docker
cd C:\Users\GrafiX\Desktop\professional-ai
docker compose down
docker compose up --build

# If using No Docker
# Stop the current process (Ctrl+C) and run START_ONE_CLICK_NO_DOCKER.bat again
```

---

## 🐛 Troubleshooting

### Docker Desktop Not Starting
```powershell
# Check if Docker is installed
docker --version

# If not installed, download from:
# https://www.docker.com/products/docker-desktop/

# After installation, restart computer
```

### Port 8000 or 3000 Already in Use
```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Same for port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### PostgreSQL Not Running
```powershell
# Start PostgreSQL service
net start postgresql-x64-16

# Or check if it's installed
Get-Service -Name "*postgres*" | Select-Object Name, Status
```

### Redis Not Running
```powershell
# Start Redis service
net start redis

# Or install Redis from: https://redis.io/download
```

### Backend Not Responding
```powershell
# Check backend logs
cd C:\Users\GrafiX\Desktop\professional-ai
docker compose logs backend

# Or if no Docker, check the terminal where backend is running
```

---

## 📋 Complete File List (What Was Fixed)

### Modified Files:
1. `docker-compose.yml` - Added frontend service, OAuth env vars, fixed database name
2. `backend/Dockerfile` - Added multi-stage build for frontend
3. `backend/app/routes/auth.py` - Fixed OAuth redirect_uri handling
4. `START_DOCKER.bat` - New one-command Docker startup
5. `START_ONE_CLICK_NO_DOCKER.bat` - Added PostgreSQL/Redis checks
6. `START.ps1` - NEW PowerShell script (auto-starts Docker)
7. `START_NO_DOCKER.ps1` - NEW PowerShell script for no-Docker mode
8. All `START_*.bat` files - Fixed to open http://localhost:3000

### Key Changes:
- Frontend now runs on port 3000 (was missing in Docker)
- Backend serves on port 8000
- OAuth redirect_uri comes from frontend request (not hardcoded)
- All OAuth credentials passed via environment variables
- Database name standardized to `professional_ai`
- Owner email login: just enter email, no password needed

---

## 🚀 Recommended Setup (Permanent)

### For Daily Use (Docker Mode):
1. Make sure Docker Desktop is running
2. Double-click: `START_DOCKER.bat`
3. Browser opens automatically at http://localhost:3000
4. Login with: `redr28126@gmail.com`

### For Development (No Docker):
1. Ensure PostgreSQL and Redis are running
2. Double-click: `START_ONE_CLICK_NO_DOCKER.bat`
3. Browser opens automatically at http://localhost:3000

### Stop Services:
```powershell
# Docker mode
cd C:\Users\GrafiX\Desktop\professional-ai
docker compose down

# No Docker mode
# Press Ctrl+C in the terminal
```

---

## ✅ Verification Checklist

After starting, verify these URLs:

- [ ] http://localhost:3000 - Frontend loads
- [ ] http://localhost:8000/api/health - Returns {"status": "healthy"}
- [ ] http://localhost:3000/login - Login page loads
- [ ] Owner login with `redr28126@gmail.com` works (no password)
- [ ] Google OAuth works (if configured)
- [ ] GitHub OAuth works (if configured)
- [ ] Admin panel accessible at http://localhost:3000/admin (after owner login)

---

## 🎯 One-Line Command Summary

### Docker Mode (with auto-start):
```powershell
cd C:\Users\GrafiX\Desktop\professional-ai; .\START.ps1
```

### Docker Mode (manual):
```powershell
cd C:\Users\GrafiX\Desktop\professional-ai; docker compose up --build
```

### No Docker Mode:
```powershell
cd C:\Users\GrafiX\Desktop\professional-ai; .\START_NO_DOCKER.ps1
```

---

## 📞 Support

If issues persist:
1. Check Docker Desktop is running: `docker info`
2. Check PostgreSQL is running: `netstat -ano | findstr :5432`
3. Check Redis is running: `netstat -ano | findstr :6379`
4. View logs: `docker compose logs -f`
