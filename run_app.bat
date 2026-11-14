@echo off
title GestureMouse AI - Hand Gesture Virtual Mouse & Fruit Ninja
cd /d "%~dp0"

echo ========================================================
echo   GestureMouse AI - Initializing Application
echo ========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python was not found on your PATH.
    echo Please install Python 3.11+ from https://www.python.org/
    echo and make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Checking dependencies...
python -c "import cv2, mediapipe, pyautogui, customtkinter, pygame" 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing missing requirements from requirements.txt...
    python -m pip install -r requirements.txt
)

echo Starting GestureMouse AI...
python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [Notice] Application closed.
    pause
)
