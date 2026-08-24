@echo off
title ESCA HSE - System Launcher
echo =======================================================================
echo Starting ESCA HSE Management System (3 Services)
echo =======================================================================
echo.
echo 1. Launching Backend Service (Spring Boot on Port 8080)...
start "ESCA HSE - Backend API (8080)" cmd /k "%~dp0start-backend.bat"

echo 2. Launching AI Agent Service (FastAPI on Port 8000)...
start "ESCA HSE - AI Agent (8000)" cmd /k "%~dp0start-agent.bat"

echo 3. Launching Frontend Dashboard (React on Port 5180)...
start "ESCA HSE - Frontend (5180)" cmd /k "%~dp0start-frontend.bat"

echo.
echo =======================================================================
echo All 3 services have been launched in separate windows!
echo Once started, open your browser at:
echo   - Frontend Dashboard:  http://localhost:5180
echo   - Backend Health:      http://localhost:8080/api/v1/health
echo   - AI Agent Health:     http://localhost:8000/health
echo =======================================================================
timeout /t 5
