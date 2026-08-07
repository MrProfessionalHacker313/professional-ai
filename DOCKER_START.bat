@echo off
chcp 65001 >nul
echo ========================================
echo   Professional AI - DOCKER START
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found! Install from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo [OK] Docker found
echo.

docker compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose not found!
    pause
    exit /b 1
)
echo [OK] Docker Compose found
echo.

REM Start services
echo Starting Professional AI with Docker...
echo.
echo This will start:
echo   - PostgreSQL database
echo   - Redis cache
echo   - Backend API (port 8000)
echo   - Media Worker
echo.
echo Press Ctrl+C to stop all services
echo.

docker compose up --build

pause