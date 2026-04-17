#!/bin/bash
# Build script for creating macOS .app bundle (alias for build_app.sh)
# Previously bundled full Playwright Chromium; now bundles ChromeDriver only.
# Users need Google Chrome installed — ChromeDriver is included in the app.
# Usage: ./build_app_with_browser.sh

set -e

echo "============================================"
echo " Building Zalo Group Checker for macOS"
echo " (with bundled ChromeDriver)"
echo "============================================"
echo ""

# Delegate to the main build script
exec "$(dirname "$0")/build_app.sh"
