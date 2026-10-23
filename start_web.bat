@echo off
cd /d "%~dp0"
echo ========================================================
echo Starting Library Management System Web Application
echo Local URL: http://127.0.0.1:5000
echo Default Login: admin / admin123
echo ========================================================
echo.

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

%PYTHON_CMD% -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Flask and dependencies...
    %PYTHON_CMD% -m pip install -r requirements.txt
)

start "" http://127.0.0.1:5000
%PYTHON_CMD% run.py
if %errorlevel% neq 0 (
    pause
)
