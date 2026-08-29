# PowerShell Launcher for ESCA HSE Management System
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "       Starting ESCA HSE Management System (3 Services)               " -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

Write-Host "`n1. Launching Backend API (Spring Boot on Port 8080)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "`"$root\start-backend.bat`""

Write-Host "2. Launching AI Agent Service (FastAPI on Port 8000)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "`"$root\start-agent.bat`""

Write-Host "3. Launching Frontend Dashboard (React on Port 5180)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "`"$root\start-frontend.bat`""

Write-Host "`nAll 3 services are launching in separate windows." -ForegroundColor Cyan
Write-Host "Waiting for services to become ready (Spring Boot & Vite may take 10-15s)...`n" -ForegroundColor DarkGray

$frontendReady = $false
$backendReady = $false
$agentReady = $false
$maxAttempts = 30
$attempt = 0

while ($attempt -lt $maxAttempts -and -not ($frontendReady -and $backendReady)) {
    Start-Sleep -Seconds 1
    $attempt++

    if (-not $frontendReady) {
        try {
            $resp = Test-NetConnection -ComputerName 127.0.0.1 -Port 5180 -WarningAction SilentlyContinue -InformationLevel Quiet
            if ($resp) {
                $frontendReady = $true
                Write-Host " [OK] Frontend Dashboard is ready on http://localhost:5180" -ForegroundColor Green
            }
        } catch {}
    }

    if (-not $backendReady) {
        try {
            $resp = Invoke-RestMethod -Uri "http://localhost:8080/api/v1/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($resp -and $resp.status -eq "ready") {
                $backendReady = $true
                Write-Host " [OK] Backend API is ready on http://localhost:8080" -ForegroundColor Green
            }
        } catch {}
    }

    if (-not $agentReady) {
        try {
            $resp = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($resp -and $resp.status -eq "ok") {
                $agentReady = $true
                Write-Host " [OK] AI Agent is ready on http://localhost:8000" -ForegroundColor Green
            }
        } catch {}
    }
}

Write-Host "`n=======================================================================" -ForegroundColor Cyan
Write-Host "ESCA HSE Management System is LIVE:" -ForegroundColor Green
Write-Host "  - Frontend Dashboard:  http://localhost:5180" -ForegroundColor Cyan
Write-Host "  - Backend Health:      http://localhost:8080/api/v1/health" -ForegroundColor Cyan
Write-Host "  - AI Agent Health:     http://localhost:8000/health" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

# Open default browser to Frontend
Start-Process "http://localhost:5180"

