@echo off
cd /d "%~dp0"
echo Starting Library Management System...

py -c "import werkzeug" 2>nul
if %errorlevel% neq 0 (
    python -c "import werkzeug" 2>nul
    if %errorlevel% neq 0 (
        echo Installing dependencies from requirements.txt...
        py -m pip install -r requirements.txt 2>nul || python -m pip install -r requirements.txt
    )
)

py main.py 2>nul || python main.py
if %errorlevel% neq 0 (
    echo.
    echo An error occurred while running the application.
    pause
)
