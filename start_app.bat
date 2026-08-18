@echo off
title AuraPrice Dynamic Price Optimization Platform
color 0B
echo ======================================================================
echo           AuraPrice Dynamic Price Optimization Engine
echo ======================================================================
echo.
echo [*] Checking Python environment...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python is not found in your system PATH!
    echo [!] Please install Python 3.10+ or check your installation.
    pause
    exit /b 1
)

echo [*] Starting backend server and opening your browser...
echo [*] Local URL: http://localhost:8000
echo [*] OpenAPI Docs: http://localhost:8000/docs
echo.
echo [i] Keep this terminal window open while using the platform.
echo [i] Press CTRL+C in this window to stop the server anytime.
echo ======================================================================
echo.

python app.py
pause

