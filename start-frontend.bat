@echo off
title ESCA HSE - Frontend Dashboard (Port 5180)
echo Starting React Vite Dashboard on http://localhost:5180 ...
cd /d "%~dp0frontend"

if not exist "node_modules\.bin\vite.cmd" (
    echo [INFO] Installing frontend dependencies...
    call npm install
)

echo [INFO] Starting Vite development server on port 5180...
call npm run dev
pause



