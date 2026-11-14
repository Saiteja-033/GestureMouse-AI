@echo off
title GestureMouse AI - Build Standalone Executable
cd /d "%~dp0"

echo ========================================================
echo  GestureMouse AI - Packaging Windows Executable
echo ========================================================
echo.

python -m pip install pyinstaller
python build_exe.py

echo.
echo ========================================================
echo  Process complete! Check the dist\GestureMouseAI folder.
echo ========================================================
pause
