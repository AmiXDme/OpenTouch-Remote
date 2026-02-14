@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo    OpenTouch-Remote Launcher
echo ==========================================
echo.

:: Check if uv is installed
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 'uv' tool not found. 
    echo Please install uv from https://github.com/astral-sh/uv
    echo.
    pause
    exit /b 1
)

echo [INFO] Starting OpenTouch-Remote...
echo [INFO] Syncing dependencies and launching server...
echo.

:: Run the application using uv
uv run main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Server exited with code %ERRORLEVEL%
    pause
)

endlocal
