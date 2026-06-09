@echo off
title Briefing.DS Dashboard Launcher
echo ==========================================================
echo  Starting Briefing.DS Local Dashboard Server...
echo ==========================================================
echo.

:: Change directory to the folder containing this batch file
cd /d "%~dp0"

:: Start the Python server
python server.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to start server. Please verify Python is installed and added to PATH.
    pause
)
