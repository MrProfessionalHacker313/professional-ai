@echo off
chcp 65001 >nul
echo ========================================
echo   Professional AI - ONE CLICK DOCKER
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found!
    echo Install Docker Desktop from: https://www.docker.com/products/docker-desktop/
    echo Make sure Docker is RUNNING before starting Professional AI.
    pause
    exit /b 1
)
echo [OK] Docker found
echo.

docker compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose not found!
    echo Please update Docker Desktop to the latest version.
    pause
    exit /b 1
)
echo [OK] Docker Compose found
echo.

REM Stop old containers
echo [1/4] Stopping old containers...
docker compose down >nul 2>&1
echo [OK] Cleanup done
echo.

REM Build and start
echo [2/4] Building and starting all services...
echo.
echo Services that will start:
echo   - PostgreSQL database (port 5432)
echo   - Redis cache (port 6379)
echo   - Backend API (port 8000)
echo   - Frontend (port 3000)
echo   - Media Worker
echo.
echo First build may take 2-3 minutes.
echo After that, startup is instant.
echo.
echo Press Ctrl+C to stop all services
echo.

REM Open browser in background after a short delay
start "Browser" /B cmd /c "timeout /t 8 /nobreak >nul && start http://localhost:3000"

docker compose up --build

pause
