@echo off
REM Build script for Windows - creates standalone .exe using spec file
REM Bundles ChromeDriver; users only need Google Chrome installed.
REM Usage: Double-click or run from project root: build_app_windows.bat

echo ============================================
echo  Building Zalo Group Checker for Windows
echo ============================================
echo.

REM Check if virtual environment exists, create if not
if not exist "venv\" (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        echo         Make sure Python 3.9+ is installed and in PATH.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo [INFO] Installing dependencies...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

REM Install PyInstaller
echo [INFO] Installing PyInstaller...
python -m pip install --upgrade pyinstaller --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

REM Download ChromeDriver for bundling
echo [INFO] Downloading ChromeDriver for bundling...
python resources/download_chromedriver.py
if %errorlevel% neq 0 (
    echo [WARNING] ChromeDriver download failed.
    echo           App will fall back to webdriver-manager at runtime.
    echo           Users may need internet connection on first run.
)

REM Clean previous builds
echo [INFO] Cleaning previous builds...
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist

REM Check for spec file
if not exist "ZaloGroupChecker_windows.spec" (
    echo [ERROR] ZaloGroupChecker_windows.spec not found!
    pause
    exit /b 1
)

REM Build using spec file
echo.
echo [INFO] Building Windows executable...
echo       This may take 3-10 minutes, please wait...
echo.

pyinstaller ZaloGroupChecker_windows.spec --noconfirm

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo  Build Successful!
    echo ============================================
    echo.

    if exist "dist\ZaloGroupChecker\" (
        echo [OK] Executable folder: dist\ZaloGroupChecker\
        echo [OK] Main executable:   dist\ZaloGroupChecker\ZaloGroupChecker.exe
        echo.
        echo ============================================
        echo  DISTRIBUTION NOTES:
        echo ============================================
        echo  1. Test the app: dist\ZaloGroupChecker\ZaloGroupChecker.exe
        echo  2. ZIP the ENTIRE dist\ZaloGroupChecker\ folder for distribution
        echo     ^(all files in the folder are required - do NOT just send the .exe^)
        echo  3. Users do NOT need Python installed
        echo  4. Users DO need Google Chrome installed ^(any recent version^)
        echo     Download Chrome: https://www.google.com/chrome/
        echo ============================================
    ) else (
        echo [WARNING] dist\ZaloGroupChecker folder not found after build.
    )
) else (
    echo.
    echo ============================================
    echo  Build FAILED!
    echo ============================================
    echo  Check the error messages above.
    echo  Common issues:
    echo    - Missing dependencies: pip install -r requirements.txt
    echo    - PyInstaller error: pip install --upgrade pyinstaller
    echo    - ChromeDriver: python resources/download_chromedriver.py
    echo    - Spec file error: check ZaloGroupChecker_windows.spec
    echo ============================================
)

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo.
pause
