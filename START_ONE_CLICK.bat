@echo off
chcp 65001 >nul
echo ========================================
echo   Professional AI - ONE CLICK START
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    pause
    exit /b 1
)

REM Kill any existing processes on ports 8000 and 3000
echo Cleaning up old processes...
taskkill /FI "PORT:8000" /F >nul 2>&1
taskkill /FI "PORT:3000" /F >nul 2>&1
timeout /t 1 /nobreak >nul

REM Start Backend
echo Starting Backend Server (Port 8000)...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
start "Backend" /B python -m app.main
cd ..

REM Wait for backend
echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start Frontend
echo Starting Frontend Server (Port 3000)...
cd frontend
start "Frontend" /B npm run dev
cd ..

REM Wait for frontend
echo Waiting for frontend to compile...
timeout /t 8 /nobreak >nul

REM Open browser
echo.
echo ========================================
echo   OPENING BROWSER...
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Login: redr28126@gmail.com (no password)
echo.

start http://localhost:3000

echo.
echo Press any key to stop all servers...
pause >nul

REM Cleanup
taskkill /FI "WINDOWTITLE eq Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend*" /F >nul 2>&1
exit