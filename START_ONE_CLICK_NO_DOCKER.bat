@echo off
chcp 65001 >nul
echo ========================================
echo   Professional AI - ONE CLICK START
echo   (No Docker Required)
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Install from: https://www.python.org/downloads/
    echo Make sure to CHECK "Add Python to PATH"
    pause
    exit /b 1
)
echo [OK] Python found
echo.

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Install from: https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.

REM Check PostgreSQL
echo Checking PostgreSQL...
netstat -ano | findstr ":5432.*LISTENING" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL is not running or not installed!
    echo.
    echo Professional AI requires PostgreSQL 16.
    echo Install from: https://www.postgresql.org/download/windows/
    echo Or use Docker: double-click START_DOCKER.bat
    echo.
    pause
    exit /b 1
)
echo [OK] PostgreSQL found
echo.

REM Check Redis (optional)
echo Checking Redis...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Redis is not running. Some features may be slower.
    echo Install Redis or use Docker for full performance.
    echo.
) else (
    echo [OK] Redis found
    echo.
)

REM Kill old processes
echo [1/5] Cleaning up old processes...
taskkill /FI "PORT:8000" /F >nul 2>&1
taskkill /FI "PORT:3000" /F >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Cleanup done
echo.

REM Setup backend
echo [2/5] Setting up backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install -q -r requirements.txt
cd ..
echo [OK] Backend ready
echo.

REM Setup frontend
echo [3/5] Setting up frontend...
cd frontend
if not exist node_modules (
    echo Installing npm packages (first time only, 2-3 minutes)...
    call npm install
) else (
    echo [OK] Frontend packages already installed
)
cd ..
echo.

REM Start backend
echo [4/5] Starting backend server...
cd backend
start "Backend Server" /B cmd /c "venv\Scripts\activate && python -m app.main"
cd ..

REM Wait for backend
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start frontend
echo [5/5] Starting frontend server...
cd frontend
start "Frontend Server" /B cmd /c "npm run dev"
cd ..

REM Wait for frontend
echo Waiting for frontend to compile...
timeout /t 8 /nobreak >nul

REM Open browser
echo.
echo ========================================
echo   SERVERS STARTED!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Login: redr28126@gmail.com (no password needed)
echo.
echo Opening browser...
start http://localhost:3000

echo.
echo Press any key to stop all servers...
pause >nul

REM Cleanup
taskkill /FI "WINDOWTITLE eq Backend Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend Server*" /F >nul 2>&1

echo.
echo Servers stopped.
timeout /t 2 >nul