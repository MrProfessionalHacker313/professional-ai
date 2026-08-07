@echo off
chcp 65001 >nul
echo ========================================
echo   Docker Installation Checker
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if not errorlevel 1 (
    echo [OK] Docker is already installed!
    docker --version
    echo.
    echo Starting Professional AI...
    call START.bat
    exit /b 0
)

echo [X] Docker is not installed
echo.
echo ========================================
echo   Docker Desktop Installation Required
echo ========================================
echo.
echo Please follow these steps:
echo.
echo 1. Download Docker Desktop from:
echo    https://www.docker.com/products/docker-desktop/
echo.
echo 2. Run the installer and follow the setup wizard
echo.
echo 3. After installation, RESTART YOUR COMPUTER
echo.
echo 4. Open Docker Desktop from Start Menu
echo.
echo 5. Wait for Docker to fully start (whale icon in system tray)
echo.
echo 6. Run this script again or run START.bat
echo.
echo ========================================
echo.

REM Try to open Docker download page
start https://www.docker.com/products/docker-desktop/

echo.
echo Press any key to exit...
pause >nul
exit /b 1