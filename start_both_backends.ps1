# PowerShell script to start both backend services
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Both Backend Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "This will start:" -ForegroundColor Yellow
Write-Host "1. Main Flask Backend on Port 5000" -ForegroundColor Green
Write-Host "2. Nutrition Backend on Port 8002" -ForegroundColor Green
Write-Host ""

Write-Host "Starting Main Backend (Port 5000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python app_simple.py" -WindowStyle Normal

Write-Host "Waiting 5 seconds for main backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "Starting Nutrition Backend (Port 8002)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; python nutrition_backend_new.py" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Both services are starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Main Backend: http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Nutrition Backend: http://127.0.0.1:8002" -ForegroundColor Green
Write-Host ""
Write-Host "Keep both PowerShell windows open!" -ForegroundColor Red
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
