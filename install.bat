@echo off
setlocal enabledelayedexpansion

echo === lollmsBot Windows Installer ===
echo Target directory: %CD%

REM === 1. Python detection ===
echo Checking Python...

python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version') do set "PY_VERSION=%%i"
    echo Found Python !PY_VERSION!
    if "!PY_VERSION:~0,4!" geq "3.10" (
        set "PYTHON=python"
        goto :has_python
    )
)

echo Python ^>= 3.10 not found. Please install from:
echo   https://www.python.org/downloads/ or Microsoft Store
echo   Then rerun install.bat
pause
exit /b 1

:has_python

REM === 2. Venv setup ===
if exist .venv (
    echo Removing existing venv...
    rmdir /s /q .venv
)

echo Creating virtual environment...
%PYTHON% -m venv .venv --upgrade-deps  REM <-- This fixes the pip issue

REM Activate venv
call .venv\Scripts\activate.bat

REM === FORCE pip upgrade (Windows venv fix) ===
echo Fixing pip...
call .venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel --no-cache-dir

REM Verify pip is working
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Pip upgrade failed. Manual fix needed.
    pause
    exit /b 1
)

REM === 3. Install ===
echo Installing lollmsBot...
pip install -e . --no-cache-dir

REM === 4. Test ===
echo Testing installation...
lollmsbot --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ CLI works - lollmsBot ready!
) else (
    echo ✗ CLI failed
)

echo.
echo === Installation complete! ===
echo To run:
echo   .venv\Scripts\activate.bat
echo   lollmsbot gateway
echo.
echo Create .env:
echo LOLLMS_HOST_ADDRESS=^<your-lollms-url^>
echo LOLLMSBOT_PORT=8800
pause
