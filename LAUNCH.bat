@echo off
chcp 65001 >nul
title Professional AI
echo ========================================
echo   Professional AI - LAUNCHING
echo ========================================
echo.

REM Check if backend venv exists
if not exist backend\venv\Scripts\activate.bat (
    echo [SETUP] First time setup - Creating virtual environment...
    cd backend
    python -m venv venv
    cd ..
    echo [SETUP] Installing backend dependencies (this takes 2-3 minutes)...
    cd backend
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
    echo [SETUP] Backend setup complete!
    echo.
)

REM Kill old processes
echo [1/3] Starting servers...
taskkill /FI "PORT:8000" /F >nul 2>&1
taskkill /FI "PORT:3000" /F >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start Backend
echo [2/3] Backend starting on port 8000...
cd backend
start "Backend" /B cmd /c "venv\Scripts\activate && python -m app.main"
cd ..

REM Wait for backend
echo Waiting for backend...
timeout /t 5 /nobreak >nul

REM Start Frontend
echo [3/3] Frontend starting on port 3000...
cd frontend
if not exist node_modules (
    echo [SETUP] First time setup - Installing frontend dependencies...
    call npm install
)
start "Frontend" /B cmd /c "npm run dev"
cd ..

REM Wait and open
echo.
echo ========================================
echo   READY!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Login: redr28126@gmail.com (no password needed)
echo.
echo Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:8000

echo.
echo Press any key to stop all servers...
pause >nul

taskkill /FI "WINDOWTITLE eq Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend*" /F >nul 2>&1
exit