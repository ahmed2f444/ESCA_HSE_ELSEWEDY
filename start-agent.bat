@echo off
title ESCA HSE - AI Agent Service (Port 8000)
echo Starting Python FastAPI AI Agent on http://localhost:8000 ...
cd /d "%~dp0ai-agent"

if not exist "venv\Scripts\python.exe" (
    echo [INFO] Creating Python virtual environment...
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        py -m venv venv
    ) else (
        python -m venv venv
    )
    call "venv\Scripts\activate.bat"
    echo [INFO] Installing AI Agent dependencies...
    python -m pip install -r requirements.txt
) else (
    call "venv\Scripts\activate.bat"
)

echo [INFO] Starting FastAPI server on port 8000...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause

