@echo off
chcp 65001 >nul
echo ========================================
echo Professional AI Desktop - Windows Build
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Installing dependencies...
call npm install

echo.
echo [2/3] Building Windows installer...
call npm run dist -- --win

echo.
echo [3/3] Done!
echo.
echo Installer location: desktop\release\Professional AI Setup.exe
echo.
pause
