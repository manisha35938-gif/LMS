@echo off
cd /d "%~dp0"
echo ========================================================
echo          Library Management System Launcher
echo ========================================================
echo.
echo   [1] Start Web Application (Recommended for Browser / Vercel)
echo   [2] Start Desktop GUI Application (Tkinter Window)
echo.
set /p choice="Select an option (1 or 2, default is 1): "
if "%choice%"=="2" (
    call start_desktop.bat
) else (
    call start_web.bat
)
