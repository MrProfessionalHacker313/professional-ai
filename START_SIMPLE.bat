@echo off
chcp 65001 >nul
echo ========================================
echo   Professional AI - STARTING
echo ========================================
echo.

REM Kill old processes
echo [1/5] Cleaning up...
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

echo Activating and installing dependencies...
call venv\Scripts\activate.bat
pip install -q fastapi uvicorn sqlalchemy asyncpg python-jose passlib bcrypt argon2-cffi pydantic-settings python-multipart httpx google-generativeai openai groq redis loguru slowapi prometheus-client python-dotenv aiosmtplib twilio qrcode pyotp bleach html5lib tenacity aiofiles python-json-logger pillow faster-whisper edge-tts pydub PyPDF2 pdfplumber python-docx pytesseract python-magic langdetect deep-translator
cd ..
echo [OK] Backend ready
echo.

REM Start backend
echo [3/5] Starting backend server...
cd backend
start "Backend Server" /B cmd /c "venv\Scripts\activate && python -m app.main"
cd ..
echo [OK] Backend starting on port 8000
echo.

REM Start frontend
echo [4/5] Starting frontend server...
cd frontend
if not exist node_modules (
    echo Installing npm packages (first time only)...
    call npm install
)
start "Frontend Server" /B cmd /c "npm run dev"
cd ..
echo [OK] Frontend starting on port 3000
echo.

REM Wait and open browser
echo [5/5] Waiting for servers to start...
timeout /t 10 /nobreak >nul
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
echo Press any key to stop servers...
pause >nul

REM Cleanup
taskkill /FI "WINDOWTITLE eq Backend Server*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend Server*" /F >nul 2>&1
exit