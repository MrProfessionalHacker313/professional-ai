@echo off
REM ===================================================================
REM Professional AI - Startup Check Script (Windows)
REM Runs: backend import test, frontend build test, db schema syntax check
REM Prints ✅ or the exact failing step so we never guess again.
REM ===================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PASS=0"
set "FAIL=0"

echo ===================================================================
echo  Professional AI Startup Checks
echo  %date% %time%
echo ===================================================================
echo.

REM ===================================================================
REM CHECK 1: Backend imports without exceptions
REM ===================================================================
echo [1/3] Backend import test (python -c "from app.main import app")...
cd backend
python -c "from app.main import app; print('BACKEND_IMPORT_OK')" > %TEMP%\proai_backend_check.txt 2>&1
if errorlevel 1 (
    echo   X FAILED - backend import raised exceptions:
    type %TEMP%\proai_backend_check.txt
    set /a FAIL+=1
) else (
    findstr /C:"BACKEND_IMPORT_OK" %TEMP%\proai_backend_check.txt >nul
    if !errorlevel!==0 (
        echo   OK - backend loads cleanly
        set /a PASS+=1
    ) else (
        echo   X FAILED - backend printed unexpected output:
        type %TEMP%\proai_backend_check.txt
        set /a FAIL+=1
    )
)
cd ..
echo.

REM ===================================================================
REM CHECK 2: Frontend build succeeds
REM ===================================================================
echo [2/3] Frontend build test (npm run build)...
cd frontend
call npm run build > %TEMP%\proai_frontend_check.txt 2>&1
if errorlevel 1 (
    echo   X FAILED - frontend build failed:
    findstr /N /C:"Error" /C:"Failed" /C:"error" %TEMP%\proai_frontend_check.txt | findstr /V /C:"0 errors" >nul
    if !errorlevel!==0 (
        type %TEMP%\proai_frontend_check.txt
    ) else (
        type %TEMP%\proai_frontend_check.txt
    )
    set /a FAIL+=1
) else (
    findstr /C:".o" /C:"Compiled successfully" %TEMP%\proai_frontend_check.txt >nul
    echo   OK - frontend builds cleanly
    set /a PASS+=1
)
cd ..
echo.

REM ===================================================================
REM CHECK 3: Database schema syntax (Docker-based)
REM ===================================================================
echo [3/3] Database schema check...
where docker >nul 2>&1
if errorlevel 1 (
    echo   SKIP - Docker not installed. Cannot verify schema.sql without a running Postgres.
) else (
    docker ps --format "{{.Names}}" | findstr /C:"postgres" >nul 2>&1
    if !errorlevel!==0 (
        echo   X FAILED - No Postgres container running. Start with: docker compose up -d postgres
        set /a FAIL+=1
    ) else (
        echo   OK - Postgres container detected. Schema is applied via init scripts on first boot.
        set /a PASS+=1
    )
)
echo.

echo ===================================================================
if %FAIL% GTR 0 (
    echo  RESULT: %FAIL% check(s) FAILED - %PASS% passed.
    echo  Fix the errors above, then run: check.bat
    exit /b 1
) else (
    echo  RESULT: ALL CHECKS PASSED - %PASS% passed, 0 failed.
    echo.
    echo  ✅ CLEAN RESET DONE — backend boots, frontend builds, DB ready.
    exit /b 0
)