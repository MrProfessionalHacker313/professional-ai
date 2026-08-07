# Professional AI - No Docker PowerShell Startup Script
# Starts backend + frontend without Docker (requires local PostgreSQL + Redis)

param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Professional AI - No Docker Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python not found!" -ForegroundColor Red
    Write-Host "Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to CHECK 'Add Python to PATH'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green

# Check Node.js
$nodeVersion = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Node.js not found!" -ForegroundColor Red
    Write-Host "Install from: https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Node.js found: $nodeVersion" -ForegroundColor Green

# Check if PostgreSQL is running on port 5432
Write-Host ""
Write-Host "Checking PostgreSQL..." -ForegroundColor Cyan
$pgPort = netstat -ano | Select-String ":5432.*LISTENING"
if (-not $pgPort) {
    Write-Host "[WARNING] PostgreSQL is not running on port 5432!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Professional AI requires PostgreSQL 16." -ForegroundColor Yellow
    Write-Host "Install from: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
    Write-Host "Or use Docker mode: run START.ps1 instead" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] PostgreSQL is running on port 5432" -ForegroundColor Green

# Check if Redis is running (optional but recommended)
Write-Host ""
Write-Host "Checking Redis..." -ForegroundColor Cyan
$redisPort = netstat -ano | Select-String ":6379.*LISTENING"
if (-not $redisPort) {
    Write-Host "[WARNING] Redis is not running on port 6379." -ForegroundColor Yellow
    Write-Host "  Some features may be slower without Redis cache." -ForegroundColor Yellow
    Write-Host "  Install Redis or use Docker mode for full performance." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "[OK] Redis is running on port 6379" -ForegroundColor Green
}

# Kill old processes
Write-Host ""
Write-Host "[1/5] Cleaning up old processes..." -ForegroundColor Cyan
taskkill /FI "PORT:8000" /F > $null 2>&1
taskkill /FI "PORT:3000" /F > $null 2>&1
Start-Sleep -Seconds 2
Write-Host "[OK] Cleanup done" -ForegroundColor Green

# Setup backend
Write-Host ""
Write-Host "[2/5] Setting up backend..." -ForegroundColor Cyan
$venvPath = Join-Path $ProjectRoot "backend\venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Gray
    Set-Location (Join-Path $ProjectRoot "backend")
    python -m venv venv
    Set-Location $ProjectRoot
}
Write-Host "  Activating virtual environment..." -ForegroundColor Gray
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
} else {
    $venvActivateBat = Join-Path $venvPath "Scripts\activate.bat"
    if (Test-Path $venvActivateBat) {
        & $venvActivateBat
    }
}
Write-Host "  Installing dependencies..." -ForegroundColor Gray
pip install -q -r (Join-Path $ProjectRoot "backend\requirements.txt")
Write-Host "[OK] Backend ready" -ForegroundColor Green

# Setup frontend
Write-Host ""
Write-Host "[3/5] Setting up frontend..." -ForegroundColor Cyan
$frontendNodeModules = Join-Path $ProjectRoot "frontend\node_modules"
if (-not (Test-Path $frontendNodeModules)) {
    Write-Host "  Installing npm packages (first time only, 2-3 minutes)..." -ForegroundColor Gray
    Set-Location (Join-Path $ProjectRoot "frontend")
    npm install
    Set-Location $ProjectRoot
} else {
    Write-Host "  [OK] Frontend packages already installed" -ForegroundColor Green
}
Write-Host "[OK] Frontend ready" -ForegroundColor Green

# Start backend
Write-Host ""
Write-Host "[4/5] Starting backend server..." -ForegroundColor Cyan
Set-Location (Join-Path $ProjectRoot "backend")
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:ProjectRoot
    Set-Location (Join-Path $using:ProjectRoot "backend")
    
    $venvPath = Join-Path $using:ProjectRoot "backend\venv"
    $venvActivate = Join-Path $venvPath "Scripts\activate.bat"
    if (Test-Path $venvActivate) {
        & $venvActivate
    }
    
    python -m app.main
}
Set-Location $ProjectRoot

Write-Host "  Waiting for backend to start..." -ForegroundColor Gray
$backendReady = $false
for ($i = 1; $i -le 10; $i++) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        # Still waiting
    }
    Write-Host "  Checking backend... ($($i * 2)s)" -ForegroundColor Gray
}

if ($backendReady) {
    Write-Host "[OK] Backend is running on http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Backend may still be starting..." -ForegroundColor Yellow
}

# Start frontend
Write-Host ""
Write-Host "[5/5] Starting frontend server..." -ForegroundColor Cyan
Set-Location (Join-Path $ProjectRoot "frontend")
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:ProjectRoot
    Set-Location (Join-Path $using:ProjectRoot "frontend")
    npm run dev
}
Set-Location $ProjectRoot

Write-Host "  Waiting for frontend to compile..." -ForegroundColor Gray
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  SERVERS STARTED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "  Login: redr28126@gmail.com (no password needed)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Cyan
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Press Ctrl+C to stop all servers" -ForegroundColor Yellow
Write-Host ""

# Wait for user to stop
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} catch {
    # User pressed Ctrl+C
} finally {
    Write-Host ""
    Write-Host "Stopping servers..." -ForegroundColor Cyan
    
    # Stop jobs
    if ($backendJob.State -eq "Running") {
        Stop-Job $backendJob
        Remove-Job $backendJob
    }
    if ($frontendJob.State -eq "Running") {
        Stop-Job $frontendJob
        Remove-Job $frontendJob
    }
    
    # Kill any remaining processes on ports 8000 and 3000
    taskkill /FI "PORT:8000" /F > $null 2>&1
    taskkill /FI "PORT:3000" /F > $null 2>&1
    
    Write-Host "Servers stopped." -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to exit"
}
