# Professional AI - How to Run (Without Docker)

## 🎯 SIMPLE 3-STEP PROCESS

### STEP 1: Install Requirements

**Install Python 3.11+:**
- Download: https://www.python.org/downloads/
- Check "Add Python to PATH" during installation
- Click "Install Now"

**Install Node.js 18+:**
- Download: https://nodejs.org/
- Download "LTS" version
- Install with default settings

**After installation:**
- Close all terminal windows
- Open a NEW terminal (Command Prompt or PowerShell)

---

### STEP 2: Start the Application

**Option A: Double-click the file**
```
START_NOW.bat
```

**Option B: Run in terminal (2 commands in 2 terminals)**

**Terminal 1 (Backend):**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```

---

### STEP 3: Open in Browser

```
http://localhost:8000
```

---

## ✅ That's It!

Your AI is now running with:
- Full authentication
- Google Sign-In (if configured)
- Admin access for redr28126@gmail.com
- AI Chat, Code Generation, Security Analysis, Bug Fixing
- Mobile & Desktop access

---

## 🔧 First Time Setup (If Needed)

### If backend fails with "module not found":
```bash
cd backend
pip install -r requirements.txt
```

### If frontend fails with "module not found":
```bash
cd frontend
npm install
```

### If port 8000 is already in use:
Edit `backend/app/config.py` and change the port, or close the app using port 8000.

---

## 📱 Access from Phone (Same WiFi)

1. Find your computer IP:
```bash
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100)

2. On phone browser:
```
http://192.168.1.100:8000
```
(Replace with your actual IP)

---

## 🎯 Quick Test

1. Open http://localhost:8000/login
2. Register with email or use Google Sign-In
3. Go to http://localhost:8000/chat
4. Type: "Write Python code to say hello world"
5. See AI generate complete code!

---

## 🛑 How to Stop

Press `Ctrl+C` in both terminals

---

## 🔄 How to Restart

**Terminal 1:**
```bash
cd backend
venv\Scripts\activate
python -m app.main
```

**Terminal 2:**
```bash
cd frontend
npm run dev
```

---

## ❓ Troubleshooting

### "python is not recognized"
- Reinstall Python and check "Add to PATH"
- Restart terminal

### "npm is not recognized"
- Reinstall Node.js
- Restart terminal

### "pip install fails"
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

### "AI not responding"
- Check backend terminal for errors
- Make sure both terminals are running
- Try refreshing the browser

---

## 📋 Complete Command List

### First time setup:
```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Every time you run:
```bash
# Terminal 1 - Backend
cd backend
venv\Scripts\activate
python -m app.main

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### To stop:
Press `Ctrl+C` in both terminals

---

## 🎉 YOU'RE READY!

**Just run:** `START_NOW.bat` or follow the 2-terminal method above

**Then open:** http://localhost:8000

**Login with:** redr28126@gmail.com (owner/admin access)