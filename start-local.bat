@echo off
chcp 65001 >nul
echo ========================================
echo   PROFESSIONAL AI - LOCAL START (NO DOCKER)
echo ========================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed. Please install Python 3.11+ first.
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed. Please install Node.js 18+ first.
    pause
    exit /b 1
)

REM Create .env if it doesn't exist
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

REM Install backend dependencies if needed
if not exist "backend\.venv" (
    echo Installing backend dependencies...
    pushd backend
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    popd
)

REM Install frontend dependencies if needed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    pushd frontend
    call npm install
    popd
)

echo.
echo Starting Professional AI...
echo.
echo Choose mode:
echo   1. Development mode (Frontend: localhost:3000, Backend: localhost:8000)
echo   2. Production mode (All on localhost:8000)
echo.

set /p mode="Enter choice (1 or 2): "

if "%mode%"=="2" (
    echo.
    echo Building frontend for production...
    pushd frontend
    call npm run build
    popd

    echo Starting backend (production mode - serves frontend on port 8000)...
    start "Professional AI Backend" cmd /c "cd backend && .\.venv\Scripts\activate && set ENVIRONMENT=production && set DEBUG=false && uvicorn app.main:app --host 0.0.0.0 --port 8000"

    echo.
    echo PROFESSIONAL AI RUNNING at http://localhost:8000
    echo.
    echo Press any key to open browser...
    pause >nul
    start http://localhost:8000
) else (
    echo.
    echo Starting backend (development mode)...
    start "Professional AI Backend" cmd /c "cd backend && .\.venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

    echo Starting frontend (development mode)...
    start "Professional AI Frontend" cmd /c "cd frontend && npm run dev"

    echo.
    echo PROFESSIONAL AI RUNNING:
    echo   Frontend: http://localhost:3000
    echo   Backend:  http://localhost:8000
    echo.
    echo Press any key to open browser...
    pause >nul
    start http://localhost:3000
)

pause
