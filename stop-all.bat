@echo off
title ESCA HSE - Stop All Services
echo =======================================================================
echo Stopping ESCA HSE Management System (Ports 8080, 8000, 5180)
echo =======================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-NetTCPConnection -LocalPort 8080, 8000, 5180 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }; Write-Host 'All ESCA HSE services stopped successfully.' -ForegroundColor Green"

echo.
echo =======================================================================
echo Backend (8080), AI Agent (8000), and Frontend (5180) have been terminated.
echo =======================================================================
pause
