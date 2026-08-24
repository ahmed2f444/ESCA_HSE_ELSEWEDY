@echo off
title ESCA HSE - Frontend Dashboard (Port 5180)
echo Starting React Vite Dashboard on http://localhost:5180 ...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo Installing npm dependencies...
    npm install
)
npm run dev -- --port 5180
pause
