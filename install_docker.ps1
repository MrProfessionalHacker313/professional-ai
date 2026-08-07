# Docker Desktop Installation Script for Windows 11
# Run this script as Administrator

param(
    [switch]$Silent = $false
)

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click on PowerShell and select 'Run as Administrator', then run this script again." -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Docker Desktop Installation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is already installed
Write-Host "[*] Checking if Docker is already installed..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Docker is already installed!" -ForegroundColor Green
        Write-Host "    Version: $dockerVersion" -ForegroundColor Green
        Write-Host ""
        Write-Host "Docker Desktop is already installed on your system." -ForegroundColor Green
        pause
        exit 0
    }
} catch {
    # Docker not found, continue with installation
}

Write-Host "[X] Docker is not installed" -ForegroundColor Red
Write-Host ""

# Download Docker Desktop
Write-Host "[*] Downloading Docker Desktop..." -ForegroundColor Yellow
$dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$downloadPath = "$env:TEMP\DockerDesktopInstaller.exe"

try {
    # Use Invoke-WebRequest with progress
    Invoke-WebRequest -Uri $dockerUrl -OutFile $downloadPath -UseBasicParsing
    Write-Host "[OK] Download completed!" -ForegroundColor Green
    Write-Host "    Location: $downloadPath" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Failed to download Docker Desktop!" -ForegroundColor Red
    Write-Host "    Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host ""

# Install Docker Desktop
Write-Host "[*] Installing Docker Desktop..." -ForegroundColor Yellow
Write-Host "    This may take several minutes. Please wait..." -ForegroundColor Gray
Write-Host ""

if ($Silent) {
    # Silent installation
    Write-Host "[*] Running silent installation..." -ForegroundColor Yellow
    $installArgs = "install --quiet --accept-license"
    Start-Process -FilePath $downloadPath -ArgumentList $installArgs -Wait -NoNewWindow
} else {
    # Interactive installation
    Write-Host "[*] Starting Docker Desktop installer..." -ForegroundColor Yellow
    Write-Host "    Please follow the installation wizard:" -ForegroundColor Gray
    Write-Host "    1. Accept the license agreement" -ForegroundColor Gray
    Write-Host "    2. Keep default settings (recommended)" -ForegroundColor Gray
    Write-Host "    3. Click 'Install' or 'Finish'" -ForegroundColor Gray
    Write-Host ""
    Start-Process -FilePath $downloadPath -Wait
}

Write-Host ""
Write-Host "[OK] Installation process completed!" -ForegroundColor Green
Write-Host ""

# Clean up download
Write-Host "[*] Cleaning up temporary files..." -ForegroundColor Yellow
Remove-Item $downloadPath -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Cleanup completed!" -ForegroundColor Green
Write-Host ""

# Post-installation instructions
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. RESTART YOUR COMPUTER (required for Docker to work properly)" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. After restart, open Docker Desktop from Start Menu" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Wait for Docker to fully start (you'll see the whale icon in system tray)" -ForegroundColor Yellow
Write-Host ""
Write-Host "4. Verify installation by running: docker --version" -ForegroundColor Yellow
Write-Host ""
Write-Host "5. Run START.bat or START_SIMPLE.bat to start your Professional AI application" -ForegroundColor Yellow
Write-Host ""

if (-not $Silent) {
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    pause
}

exit 0