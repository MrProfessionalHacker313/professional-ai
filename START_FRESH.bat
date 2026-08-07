@echo off
chcp 65001 >nul
echo ========================================
echo   Professional AI - FRESH START
echo   Clear Cache + Start Servers
echo ========================================
echo.

echo [1/4] Killing old processes...
taskkill /FI "PORT:8000" /F >nul 2>&1
taskkill /FI "PORT:3000" /F >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Old processes stopped
echo.

echo [2/4] Clearing browser cache and cookies...
powershell -Command "Clear-Host; Write-Host 'Clearing Edge/Chrome cache...' -ForegroundColor Yellow; $edgePaths = @($env:LOCALAPPDATA + '\Microsoft\Edge\User Data\Default\Cache', $env:LOCALAPPDATA + '\Google\Chrome\User Data\Default\Cache'); foreach ($p in $edgePaths) { if (Test-Path $p) { Remove-Item -Path "$p\*" -Recurse -Force -ErrorAction SilentlyContinue } }; Write-Host 'Cache cleared for localhost:3000 and localhost:8000' -ForegroundColor Green"
echo [OK] Browser cache cleared
echo.

echo [3/4] Starting Backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Installing/updating dependencies...
pip install -q -r requirements.txt
cd ..

echo Starting backend server...
cd backend
start "Backend Server" /B cmd /c "venv\Scripts\activate && python -m app.main"
cd ..

echo Waiting for backend...
timeout /t 6 /nobreak >nul
echo [OK] Backend started at http://localhost:8000
echo.

echo [4/4] Starting Frontend...
cd frontend
if not exist node_modules (
    echo Installing npm packages...
    call npm install
)
echo Starting frontend server...
start "Frontend Server" /B cmd /c "npm run dev"
cd ..

echo Waiting for frontend...
timeout /t 10 /nobreak >nul
echo [OK] Frontend started at http://localhost:3000
echo.

echo ========================================
echo   SERVERS READY!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Login: redr28126@gmail.com (no password)
echo.
echo Opening browser in INCOGNITO mode (no cache)...
start msedge --inprivate http://localhost:3000

echo.
echo Press any key to stop all servers...
pause >nul

echo.
echo Stopping servers...
taskkill /FI "WINDOWTITLE eq Backend Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend Server*" /F >nul 2>&1
echo.
echo Servers stopped.
timeout /t 2 >nul
