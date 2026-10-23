@echo off
cd /d "%~dp0"
echo ========================================================
echo Building Standalone Library Management System Executable
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

echo Checking for PyInstaller...
%PYTHON_CMD% -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    %PYTHON_CMD% -m pip install pyinstaller
)

echo Building executable...
%PYTHON_CMD% -m PyInstaller --noconfirm --onedir --windowed --add-data "database\library.db;database" --name "LibraryManagementSystem" desktop\main.py

echo.
if exist "dist\LibraryManagementSystem\LibraryManagementSystem.exe" (
    echo ========================================================
    echo Build successful!
    echo Standalone executable located in:
    echo   dist\LibraryManagementSystem\LibraryManagementSystem.exe
    echo ========================================================
) else (
    echo Build failed. Please review the output above.
)
echo.
pause

