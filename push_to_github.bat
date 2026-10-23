@echo off
cd /d "%~dp0"
echo ========================================================
echo Deploying Library Management System to GitHub
echo Remote URL: https://github.com/manisha35938-gif/LMS.git
echo ========================================================
echo.

git push -u origin main
if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo Deployment successful! Code is live on GitHub.
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo Push did not complete.
    echo If GitHub asks for authentication:
    echo 1. Sign in with your browser when prompted, or
    echo 2. Generate a Personal Access Token (classic) on GitHub:
    echo    https://github.com/settings/tokens
    echo    and paste it when prompted for your password.
    echo ========================================================
)
echo.
pause

