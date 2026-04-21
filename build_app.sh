#!/bin/bash
# Build script for creating macOS .app bundle
# Bundles ChromeDriver; users only need Google Chrome installed.
# Usage: ./build_app.sh

set -e

echo "============================================"
echo " Building Zalo Group Checker for macOS"
echo "============================================"
echo ""

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "[ERROR] Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate virtual environment (macOS path)
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "[INFO] Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
pip install --upgrade pyinstaller --quiet

# Download ChromeDriver for bundling
echo "[INFO] Downloading ChromeDriver for bundling..."
python resources/download_chromedriver.py || {
    echo "[WARNING] ChromeDriver download failed."
    echo "          App will fall back to webdriver-manager at runtime."
}

# Clean previous builds
echo "[INFO] Cleaning previous builds..."
rm -rf build dist

# Build the app
echo ""
echo "[INFO] Building .app bundle..."
echo "       This may take several minutes..."
echo ""

pyinstaller ZaloGroupChecker.spec --noconfirm

if [ -d "dist/ZaloGroupChecker.app" ]; then
    echo ""
    echo "============================================"
    echo " Build Successful!"
    echo "============================================"
    APP_SIZE=$(du -sh dist/ZaloGroupChecker.app | cut -f1)
    echo "[OK] App: dist/ZaloGroupChecker.app ($APP_SIZE)"
    echo ""

    # Create ZIP for distribution
    echo "[INFO] Creating ZIP archive..."
    cd dist
    zip -r ZaloGroupChecker-macOS.zip ZaloGroupChecker.app
    cd ..
    echo "[OK] ZIP: dist/ZaloGroupChecker-macOS.zip"

    # Optionally create DMG
    if command -v create-dmg &> /dev/null; then
        echo "[INFO] Creating DMG installer..."
        rm -f "dist/ZaloGroupChecker-1.0.0.dmg"
        create-dmg \
          --volname "Zalo Group Checker" \
          --window-pos 200 120 \
          --window-size 800 450 \
          --icon-size 100 \
          --icon "ZaloGroupChecker.app" 200 190 \
          --hide-extension "ZaloGroupChecker.app" \
          --app-drop-link 600 185 \
          "dist/ZaloGroupChecker-1.0.0.dmg" \
          "dist/"
        echo "[OK] DMG: dist/ZaloGroupChecker-1.0.0.dmg"
    else
        echo "[INFO] create-dmg not installed. Skipping DMG. Install with: brew install create-dmg"
    fi

    echo ""
    echo "============================================"
    echo " DISTRIBUTION NOTES:"
    echo "============================================"
    echo " 1. Test: open dist/ZaloGroupChecker.app"
    echo " 2. Distribute: dist/ZaloGroupChecker-macOS.zip"
    echo " 3. Users do NOT need Python installed"
    echo " 4. Users DO need Google Chrome installed"
    echo "    Download: https://www.google.com/chrome/"
    echo " 5. First launch: Right-click -> Open (bypass Gatekeeper)"
    echo "============================================"
else
    echo ""
    echo "[ERROR] Build failed! dist/ZaloGroupChecker.app not found."
    exit 1
fi

deactivate
