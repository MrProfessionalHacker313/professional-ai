@echo off
chcp 65001 >nul
echo ========================================
echo   Professional AI - Starting Without Docker
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python: 
python --version
echo.

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Install from: https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js: 
node --version
echo.

REM Setup backend
echo [1/3] Setting up backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q
cd ..
echo [OK] Backend ready
echo.

REM Setup frontend
echo [2/3] Setting up frontend...
cd frontend
if not exist node_modules (
    echo Installing npm packages (this takes 2-3 minutes)...
    call npm install
) else (
    echo [OK] Frontend packages already installed
)
cd ..
echo.

REM Start backend
echo [3/3] Starting servers...
echo.
echo ========================================
echo   BACKEND STARTED at http://localhost:8000
echo ========================================
echo.
echo NOW OPEN A NEW TERMINAL and run:
echo   cd frontend
echo   npm run dev
echo.
echo Then open browser: http://localhost:3000
echo ========================================
echo.

cd backend
call venv\Scripts\activate.bat
python -m app.main

pause