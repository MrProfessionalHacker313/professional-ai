@echo off
chcp 65001 >nul
echo ========================================
echo   Professional AI - STARTING
echo ========================================
echo.

REM Kill old processes
echo [1/4] Cleaning up...
taskkill /FI "PORT:8000" /F >nul 2>&1
taskkill /FI "PORT:3000" /F >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Cleanup done
echo.

REM Setup backend
echo [2/4] Setting up backend...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
cd ..
echo [OK] Backend ready
echo.

REM Start backend
echo [3/4] Starting backend server...
cd backend
start "Backend" /B cmd /c "venv\Scripts\activate && python -m app.main"
cd ..
echo [OK] Backend starting on port 8000
echo.

REM Start frontend
echo [4/4] Starting frontend server...
cd frontend
if not exist node_modules (
    echo Installing npm packages (first time only, 2-3 minutes)...
    call npm install
)
start "Frontend" /B cmd /c "npm run dev"
cd ..
echo [OK] Frontend starting on port 3000
echo.

REM Wait and open browser
echo.
echo ========================================
echo   SERVERS STARTED!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Login: redr28126@gmail.com (no password)
echo.
echo Opening browser in 10 seconds...
echo.

timeout /t 10 /nobreak >nul
start http://localhost:3000

echo.
echo Press any key to stop all servers...
pause >nul

REM Cleanup
taskkill /FI "WINDOWTITLE eq Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend*" /F >nul 2>&1
exit