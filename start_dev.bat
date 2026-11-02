@echo off
echo =================================================================
echo   AUTONOMOUS DEVOPS & CI/CD TELEMETRY PLATFORM DEV LAUNCHER
echo =================================================================
echo Starting FastAPI Backend and React Frontend concurrently...
echo.

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run_dev.py
) else (
    python run_dev.py
)

