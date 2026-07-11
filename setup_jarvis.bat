@echo off
setlocal enabledelayedexpansion
title JARVIS Initial Setup

echo ===================================================
echo               JARVIS SETUP WIZARD
echo ===================================================
echo.

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from python.org and ensure "Add Python to PATH" is checked.
    pause
    exit /b
)
echo [OK] Python detected.
echo.

:: Install Dependencies
echo Installing required dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt -q
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b
    )
    echo [OK] Dependencies installed successfully.
) else (
    echo [WARNING] requirements.txt not found. Skipping dependency installation.
)
echo.

:: Check for .env file
if not exist ".env" (
    echo [WARNING] No .env file found. JARVIS may fail to launch if the API keys are missing.
) else (
    echo [OK] .env configuration file detected.
)
echo.

echo ===================================================
echo Starting JARVIS...
echo ===================================================
python main.py
pause
