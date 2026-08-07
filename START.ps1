# Professional AI - PowerShell Startup Script
# Automatically starts Docker if needed and launches the full stack

param()

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Professional AI - PowerShell Starter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not installed!" -ForegroundColor Red
    Write-Host "Install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    Write-Host "Then restart your computer and run this script again." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Docker found: $dockerVersion" -ForegroundColor Green

# Check if Docker Compose is available
$composeVersion = docker compose version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker Compose not found!" -ForegroundColor Red
    Write-Host "Please update Docker Desktop to the latest version." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Docker Compose found" -ForegroundColor Green

# Check if Docker daemon is running
$dockerInfo = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[WARNING] Docker daemon is not running!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Attempting to start Docker Desktop..." -ForegroundColor Cyan
    
    # Try to start Docker Desktop
    $dockerDesktopPaths = @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Docker\Docker Desktop.exe"
    )
    
    $dockerDesktopStarted = $false
    foreach ($path in $dockerDesktopPaths) {
        if (Test-Path $path) {
            Write-Host "Starting Docker Desktop from: $path" -ForegroundColor Cyan
            Start-Process $path
            $dockerDesktopStarted = $true
            break
        }
    }
    
    if (-not $dockerDesktopStarted) {
        Write-Host ""
        Write-Host "[ERROR] Docker Desktop not found!" -ForegroundColor Red
        Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
        Write-Host "After installation, restart your computer and run this script again." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host ""
    Write-Host "Waiting for Docker Desktop to start (this may take 30-60 seconds)..." -ForegroundColor Cyan
    Write-Host ""
    
    $maxWaitSeconds = 120
    $waitedSeconds = 0
    $checkInterval = 5
    
    while ($waitedSeconds -lt $maxWaitSeconds) {
        Start-Sleep -Seconds $checkInterval
        $waitedSeconds += $checkInterval
        
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Docker Desktop is now running!" -ForegroundColor Green
            break
        }
        
        Write-Host "  Still waiting... ($waitedSeconds seconds)" -ForegroundColor Yellow
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[ERROR] Docker Desktop did not start within $maxWaitSeconds seconds." -ForegroundColor Red
        Write-Host "Please start Docker Desktop manually and try again." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[OK] Docker daemon is running" -ForegroundColor Green
}

Write-Host ""
Write-Host "[1/4] Stopping old containers..." -ForegroundColor Cyan
docker compose down > $null 2>&1
Write-Host "[OK] Cleanup done" -ForegroundColor Green

Write-Host ""
Write-Host "[2/4] Building and starting all services..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Services that will start:" -ForegroundColor White
Write-Host "  - PostgreSQL database (port 5432)" -ForegroundColor Gray
Write-Host "  - Redis cache (port 6379)" -ForegroundColor Gray
Write-Host "  - Backend API (port 8000)" -ForegroundColor Gray
Write-Host "  - Frontend (port 3000)" -ForegroundColor Gray
Write-Host "  - Media Worker" -ForegroundColor Gray
Write-Host ""
Write-Host "First build may take 2-3 minutes." -ForegroundColor Yellow
Write-Host "After that, startup is instant." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Start browser in background after delay
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 10
    Start-Process "http://localhost:3000"
} | Out-Null

docker compose up --build

Write-Host ""
Write-Host "Services stopped." -ForegroundColor Cyan
Read-Host "Press Enter to exit"
