@echo off
title ESCA HSE - AI Agent Service (Port 8000)
echo =======================================================================
echo Starting Python FastAPI AI Agent on http://localhost:8000 ...
echo =======================================================================
cd /d "%~dp0ai-agent"

if not exist "venv\Scripts\python.exe" (
    echo [INFO] Creating Python virtual environment...
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        py -m venv venv
    ) else (
        python -m venv venv
    )
    echo [INFO] Installing AI Agent dependencies...
    ".\venv\Scripts\python.exe" -m pip install -r requirements.txt
)

echo [INFO] Starting FastAPI server on port 8000...
".\venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] AI Agent server exited with code %ERRORLEVEL%.
)
pause


