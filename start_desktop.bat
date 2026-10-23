@echo off
cd /d "%~dp0"
echo Starting Library Management System Desktop GUI...

set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Python is not installed or not in PATH.
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
)

%PYTHON_CMD% desktop/main.py
if %errorlevel% neq 0 (
    echo.
    echo An error occurred running the desktop application.
    pause
)

