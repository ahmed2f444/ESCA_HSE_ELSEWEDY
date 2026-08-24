@echo off
title ESCA HSE - Backend API (Port 8080)
echo Starting Spring Boot Backend API on http://localhost:8080 ...
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%backend"

if exist "%ROOT_DIR%tools\maven\bin\mvn.cmd" (
    set "PATH=%ROOT_DIR%tools\maven\bin;%PATH%"
    call "%ROOT_DIR%tools\maven\bin\mvn.cmd" spring-boot:run
) else if exist "mvnw.cmd" (
    call mvnw.cmd spring-boot:run
) else (
    mvn spring-boot:run
)
pause
