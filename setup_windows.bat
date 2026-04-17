@echo off
REM Windows Setup Script for Zalo Group Checker
REM This script helps set up the development environment on Windows

echo ========================================
echo Zalo Group Checker - Windows Setup
echo ========================================
echo.

REM Check Python version
echo [1/6] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org/
    pause
    exit /b 1
)
echo.

REM Upgrade pip
echo [2/6] Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo WARNING: Failed to upgrade pip
)
echo.

REM Create virtual environment
echo [3/6] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)
echo.

REM Activate virtual environment
echo [4/6] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Install pandas separately with pre-built wheel
echo [5/6] Installing pandas (pre-built wheel)...
pip install pandas==2.1.4 --only-binary :all:
if %errorlevel% neq 0 (
    echo WARNING: Failed to install pandas 2.1.4, trying older version...
    pip install pandas==2.0.3 --only-binary :all:
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install pandas
        echo Please see TROUBLESHOOTING.md for solutions
        pause
        exit /b 1
    )
)
echo.

REM Install remaining requirements
echo [6/6] Installing remaining dependencies...
pip install playwright openpyxl PyQt6 fuzzywuzzy python-Levenshtein xlrd
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Please see TROUBLESHOOTING.md for solutions
    pause
    exit /b 1
)
echo.

REM Install Playwright browsers
echo Installing Playwright Chromium browser...
echo This may take a few minutes...
playwright install chromium
if %errorlevel% neq 0 (
    echo WARNING: Failed to install Playwright browser
    echo You can install it manually later with: playwright install chromium
)
echo.

echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To run the application:
echo   1. Activate virtual environment: venv\Scripts\activate
echo   2. Run: python src\main.py
echo.
echo If you encountered any errors, see TROUBLESHOOTING.md
echo.
pause
