@echo off
REM Setup script for Windows (if needed in the future)

echo Setting up Zalo Group Membership Checker...
echo.

echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo Failed to create virtual environment
    exit /b %errorlevel%
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies
    exit /b %errorlevel%
)

echo Installing Playwright browsers...
playwright install chromium
if %errorlevel% neq 0 (
    echo Failed to install Playwright browsers
    exit /b %errorlevel%
)

echo Creating directories...
if not exist "output" mkdir output
if not exist "logs" mkdir logs
if not exist "resources" mkdir resources

echo Creating sample Excel file...
python resources\create_sample_excel.py

echo.
echo Setup complete!
echo To run the application: python src\main.py
echo.
pause
