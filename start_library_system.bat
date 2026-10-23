@echo off
cd /d "%~dp0"
echo Starting Library Management System...

set PYTHON_CMD=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Python is not installed or not added to your system PATH.
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
)

%PYTHON_CMD% -c "import werkzeug" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing required dependencies from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
)

%PYTHON_CMD% main.py
if %errorlevel% neq 0 (
    echo.
    echo An error occurred while running the application.
    pause
)
