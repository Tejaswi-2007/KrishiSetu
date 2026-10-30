@echo off
title KrishiSetu Launcher
color 0A

echo.
echo ==========================================
echo        KRISHISETU - STARTING APP
echo ==========================================
echo.

cd /d "%~dp0"

if not exist "backend\app\main.py" (
    echo ERROR: Backend entry point not found.
    pause
    exit /b 1
)

if not exist "backend\.venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found.
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo ERROR: Frontend package.json not found.
    pause
    exit /b 1
)

echo Checking PostgreSQL...

powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"

if errorlevel 1 (
    echo WARNING: PostgreSQL is not listening on port 5432.
    echo Start your PostgreSQL service before using KrishiSetu.
    pause
    exit /b 1
)

echo Starting FastAPI Backend...

start "KrishiSetu Backend" cmd /k "cd /d ""%~dp0backend"" && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo Waiting for backend...
timeout /t 5 /nobreak >nul

echo Starting React Frontend...

start "KrishiSetu Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev -- --host 127.0.0.1 --port 5174 --strictPort"

echo Waiting for frontend...
timeout /t 5 /nobreak >nul

echo Opening KrishiSetu...

start "" "http://127.0.0.1:5174/"

echo.
echo ==========================================
echo       KRISHISETU STARTUP COMPLETE
echo ==========================================
echo.
echo Frontend: http://127.0.0.1:5174
echo Backend:  http://127.0.0.1:8000/docs
echo.
echo Keep both server windows open.
echo Close them when finished.
echo.
pause
