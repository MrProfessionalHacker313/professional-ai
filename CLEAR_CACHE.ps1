# Professional AI - Clear Cache Script
# Run this before starting the app to ensure fresh state

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Clearing All Cache" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clear Edge/Chrome cache for localhost
$edgeCachePaths = @(
    "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache",
    "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
)

Write-Host "[1/3] Clearing browser cache..." -ForegroundColor Yellow
foreach ($path in $edgeCachePaths) {
    if (Test-Path $path) {
        Remove-Item -Path "$path\*" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Cleared: $path" -ForegroundColor Green
    }
}

# Clear Next.js build cache
Write-Host "[2/3] Clearing Next.js build cache..." -ForegroundColor Yellow
$frontendDir = "C:\Users\GrafiX\Desktop\professional-ai\frontend"
if (Test-Path "$frontendDir\.next") {
    Remove-Item -Path "$frontendDir\.next" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Cleared .next directory" -ForegroundColor Green
}

# Clear Python cache
Write-Host "[3/3] Clearing Python cache..." -ForegroundColor Yellow
$backendDir = "C:\Users\GrafiX\Desktop\professional-ai\backend"
if (Test-Path "$backendDir\__pycache__") {
    Remove-Item -Path "$backendDir\__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Cleared __pycache__" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Cache Cleared Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Run: START_ONE_CLICK_NO_DOCKER.bat" -ForegroundColor White
Write-Host "2. Or run: START_FRESH.bat (clears cache + starts)" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Use INCOGNITO/PRIVATE mode to avoid old cookies:" -ForegroundColor Yellow
Write-Host "  - Edge: Ctrl+Shift+N" -ForegroundColor White
Write-Host "  - Chrome: Ctrl+Shift+N" -ForegroundColor White
Write-Host ""

pause
