@echo off
chcp 65001 >nul
echo ========================================
echo   Professional AI - ULTRA FAST START
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Install from: https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.

REM Setup backend
echo [1/4] Setting up backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install -r requirements.txt -q
cd ..
echo [OK] Backend ready
echo.

REM Setup frontend
echo [2/4] Setting up frontend...
cd frontend
if not exist node_modules (
    echo Installing npm packages (first time only, 2-3 minutes)...
    call npm install
) else (
    echo [OK] Frontend packages already installed
)
cd ..
echo.

REM Check if PostgreSQL is running
echo [3/4] Checking database...
pg_isready -h localhost -p 5432 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL not running!
    echo Starting PostgreSQL...
    net start postgresql-x64-16 >nul 2>&1
    if errorlevel 1 (
        net start postgresql >nul 2>&1
        if errorlevel 1 (
            echo [ERROR] Could not start PostgreSQL. Please start it manually.
            echo.
        ) else (
            echo [OK] PostgreSQL started
        )
    ) else (
        echo [OK] PostgreSQL started
    )
) else (
    echo [OK] PostgreSQL is running
)
echo.

REM Start servers
echo [4/4] Starting servers...
echo.
echo ========================================
echo   BACKEND: http://localhost:8000
echo   FRONTEND: http://localhost:3000
echo ========================================
echo.
echo Starting backend server...
echo.

REM Start backend in background
cd backend
start "Backend Server" /B cmd /c "venv\Scripts\activate && python -m app.main"

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Check if backend is running
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend not responding yet, waiting more...
    timeout /t 3 /nobreak >nul
)

REM Start frontend
echo Starting frontend server...
cd frontend
start "Frontend Server" /B cmd /c "npm run dev"

REM Wait for frontend to compile
echo Waiting for frontend to compile...
timeout /t 8 /nobreak >nul

REM Open browser
echo.
echo Opening browser...
start http://localhost:3000

echo.
echo ========================================
echo   SERVERS STARTED!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Login with: redr28126@gmail.com
echo.
echo Press any key to stop all servers...
pause >nul

REM Kill all child processes
taskkill /FI "WINDOWTITLE eq Backend Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend Server*" /F >nul 2>&1

echo.
echo Servers stopped.
timeout /t 2 >nul