@echo off
title ESCA HSE - AI Agent Service (Port 8000)
echo Starting Python FastAPI AI Agent on http://localhost:8000 ...
cd /d "%~dp0ai-agent"
if exist "venv\Scripts\python.exe" (
    call "venv\Scripts\activate.bat"
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    py -m venv venv
    call "venv\Scripts\activate.bat"
    pip install -r requirements.txt
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)
pause
