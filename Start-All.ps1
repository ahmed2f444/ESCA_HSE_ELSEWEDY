# PowerShell Launcher for ESCA HSE Management System
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "Starting ESCA HSE Management System (3 Services)" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

Write-Host "1. Launching Backend API (Spring Boot on Port 8080)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "`"$root\start-backend.bat`""

Write-Host "2. Launching AI Agent Service (FastAPI on Port 8000)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "`"$root\start-agent.bat`""

Write-Host "3. Launching Frontend Dashboard (React on Port 5180)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "`"$root\start-frontend.bat`""

Write-Host "`nAll 3 services are launching in separate windows." -ForegroundColor Green
Write-Host "Once ready, open: http://localhost:5180" -ForegroundColor Green
