# Building macOS .app Bundle - Deployment Guide

## Overview

Hướng dẫn này giúp bạn đóng gói ứng dụng Zalo Group Membership Checker thành file `.app` để người dùng có thể tải về và sử dụng trực tiếp trên macOS mà không cần cài đặt Python.

## Prerequisites

- macOS 11.0 or higher
- Python 3.9+
- All project dependencies installed
- PyInstaller

## Method 1: PyInstaller (Recommended)

PyInstaller đóng gói Python app thành standalone executable với tất cả dependencies.

### Step 1: Install PyInstaller

```bash
# Activate virtual environment
source venv/bin/activate

# Install PyInstaller
pip install pyinstaller
```

### Step 2: Create PyInstaller Spec File

Tạo file [`ZaloGroupChecker.spec`](ZaloGroupChecker.spec):

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('resources', 'resources'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'playwright',
        'playwright.sync_api',
        'pandas',
        'openpyxl',
        'fuzzywuzzy',
        'xlrd',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ZaloGroupChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ZaloGroupChecker',
)

app = BUNDLE(
    coll,
    name='ZaloGroupChecker.app',
    icon=None,  # Add icon path if you have one: 'icon.icns'
    bundle_identifier='com.zalogroupchecker.app',
    info_plist={
        'CFBundleName': 'Zalo Group Checker',
        'CFBundleDisplayName': 'Zalo Group Checker',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
    },
)
```

### Step 3: Build the .app

```bash
# Clean previous builds (optional)
rm -rf build dist

# Build the app
pyinstaller ZaloGroupChecker.spec

# The .app will be in dist/ZaloGroupChecker.app
```

### Step 4: Test the .app

```bash
# Run from terminal to see any errors
./dist/ZaloGroupChecker.app/Contents/MacOS/ZaloGroupChecker

# Or double-click in Finder
open dist/
```

### Step 5: Post-Build Setup

Người dùng vẫn cần cài Playwright browsers một lần:

```bash
# Install Playwright CLI globally
pip3 install playwright

# Install chromium browser
playwright install chromium
```

## Method 2: py2app (Native macOS)

py2app là công cụ chuyên biệt cho macOS, tạo ra .app bundle thuần túy.

### Step 1: Install py2app

```bash
pip install py2app
```

### Step 2: Create setup.py

Tạo file [`setup_app.py`](setup_app.py):

```python
from setuptools import setup

APP = ['src/main.py']
DATA_FILES = [
    ('', ['config.json']),
    ('resources', ['resources/sample_usernames.csv']),
]
OPTIONS = {
    'argv_emulation': True,
    'packages': [
        'PyQt6',
        'playwright',
        'pandas',
        'openpyxl',
        'fuzzywuzzy',
    ],
    'includes': [
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    'plist': {
        'CFBundleName': 'Zalo Group Checker',
        'CFBundleDisplayName': 'Zalo Group Checker',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
```

### Step 3: Build

```bash
# Clean build
rm -rf build dist

# Build for distribution
python setup_app.py py2app

# The .app will be in dist/
```

## Creating Installer Package

### Option A: DMG Image (Simple)

Tạo DMG file để người dùng dễ dàng cài đặt:

```bash
# Install create-dmg
brew install create-dmg

# Create DMG
create-dmg \
  --volname "Zalo Group Checker" \
  --volicon "icon.icns" \
  --window-pos 200 120 \
  --window-size 800 450 \
  --icon-size 100 \
  --icon "ZaloGroupChecker.app" 200 190 \
  --hide-extension "ZaloGroupChecker.app" \
  --app-drop-link 600 185 \
  --background "background.png" \
  "ZaloGroupChecker-1.0.0.dmg" \
  "dist/"
```

### Option B: PKG Installer

Tạo PKG installer chuyên nghiệp:

```bash
# Build PKG
pkgbuild \
  --root dist/ZaloGroupChecker.app \
  --identifier com.zalogroupchecker.app \
  --version 1.0.0 \
  --install-location /Applications/ZaloGroupChecker.app \
  ZaloGroupChecker-1.0.0.pkg
```

## Distribution Strategy

### For End Users

Cung cấp 3 files:

1. **ZaloGroupChecker.app** hoặc **ZaloGroupChecker.dmg**
2. **INSTALL_GUIDE.txt** - Hướng dẫn cài đặt
3. **sample_usernames.xlsx** - File mẫu

### INSTALL_GUIDE.txt Template

```
HƯỚNG DẪN CÀI ĐẶT ZALO GROUP CHECKER
=====================================

BƯỚC 1: Cài đặt ứng dụng
-------------------------
1. Mở file ZaloGroupChecker.dmg
2. Kéo ZaloGroupChecker.app vào thư mục Applications
3. Đóng cửa sổ DMG

BƯỚC 2: Cài đặt Playwright Browser (CHỈ LẦN ĐẦU)
------------------------------------------------
1. Mở Terminal
2. Chạy lệnh: pip3 install playwright
3. Chạy lệnh: playwright install chromium

LƯU Ý: Nếu chưa cài Python, tải từ: https://www.python.org/downloads/

BƯỚC 3: Chạy ứng dụng
--------------------
1. Mở Applications folder
2. Double-click vào ZaloGroupChecker
3. Nếu macOS cảnh báo "from unidentified developer":
   - Vào System Preferences > Security & Privacy
   - Click "Open Anyway"

SỬ DỤNG:
--------
1. Chọn file Excel chứa danh sách username
2. Nhập link group Zalo
3. Click "Start Checking"
4. Đăng nhập Zalo Web khi trình duyệt mở
5. Đợi quá trình hoàn tất
6. Kết quả được lưu trong thư mục output

HỖ TRỢ:
-------
- Email: support@example.com
- Xem file README.md để biết thêm chi tiết
```

## Solving Common Issues

### Issue 1: "App is damaged and can't be opened"

**Giải pháp:**
```bash
# Remove quarantine attribute
xattr -cr /Applications/ZaloGroupChecker.app
```

### Issue 2: Permission Denied

**Giải pháp:**
```bash
# Fix permissions
chmod +x /Applications/ZaloGroupChecker.app/Contents/MacOS/ZaloGroupChecker
```

### Issue 3: Playwright Browser Not Found

**Giải pháp:** Người dùng phải cài playwright browsers:
```bash
playwright install chromium
```

### Issue 4: Large App Size

PyInstaller apps có thể lớn (200-500MB). Để giảm:
- Sử dụng `--onefile` mode
- Exclude unnecessary packages
- Use UPX compression

```bash
pyinstaller --onefile --windowed --name ZaloGroupChecker src/main.py
```

## Code Signing (Optional but Recommended)

Để app không bị cảnh báo "unidentified developer":

### Step 1: Get Developer Certificate

1. Enroll in Apple Developer Program ($99/year)
2. Create Developer ID Application certificate
3. Download and install certificate

### Step 2: Sign the App

```bash
# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" \
  dist/ZaloGroupChecker.app

# Verify signature
codesign --verify --verbose dist/ZaloGroupChecker.app
spctl --assess --verbose dist/ZaloGroupChecker.app
```

### Step 3: Notarize (macOS 10.15+)

```bash
# Create zip for notarization
ditto -c -k --keepParent dist/ZaloGroupChecker.app ZaloGroupChecker.zip

# Submit for notarization
xcrun notarytool submit ZaloGroupChecker.zip \
  --apple-id "your@email.com" \
  --team-id "YOUR_TEAM_ID" \
  --password "app-specific-password"

# Staple the notarization
xcrun stapler staple dist/ZaloGroupChecker.app
```

## Automated Build Script

Tạo file [`build_app.sh`](build_app.sh):

```bash
#!/bin/bash

echo "🔨 Building Zalo Group Checker for macOS..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Activate virtual environment
source venv/bin/activate

# Install/update PyInstaller
echo "📦 Installing PyInstaller..."
pip install --upgrade pyinstaller

# Build the app
echo "🏗️ Building .app bundle..."
pyinstaller ZaloGroupChecker.spec

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    echo "📁 App location: dist/ZaloGroupChecker.app"
    
    # Create DMG (if create-dmg is installed)
    if command -v create-dmg &> /dev/null; then
        echo "📀 Creating DMG..."
        create-dmg \
          --volname "Zalo Group Checker" \
          --window-pos 200 120 \
          --window-size 800 450 \
          --icon-size 100 \
          --icon "ZaloGroupChecker.app" 200 190 \
          --app-drop-link 600 185 \
          "dist/ZaloGroupChecker-1.0.0.dmg" \
          "dist/"
        
        echo "✅ DMG created: dist/ZaloGroupChecker-1.0.0.dmg"
    fi
    
    echo ""
    echo "📦 Distribution files ready:"
    ls -lh dist/
else
    echo "❌ Build failed!"
    exit 1
fi
```

Sử dụng:
```bash
chmod +x build_app.sh
./build_app.sh
```

## Final Distribution Checklist

- [ ] Build .app successfully
- [ ] Test .app on clean macOS system
- [ ] Create DMG or PKG installer
- [ ] Write installation guide
- [ ] Prepare sample Excel file
- [ ] Test installation process
- [ ] (Optional) Code sign the app
- [ ] (Optional) Notarize for macOS 10.15+
- [ ] Create README for users
- [ ] Zip all files for distribution

## Distribution Package Structure

```
ZaloGroupChecker-1.0.0/
├── ZaloGroupChecker-1.0.0.dmg   (or .app)
├── INSTALL_GUIDE.txt
├── README.pdf
├── sample_usernames.xlsx
└── LICENSE.txt
```

Compress thành ZIP:
```bash
zip -r ZaloGroupChecker-1.0.0.zip ZaloGroupChecker-1.0.0/
```

## Next Steps

1. Build app using PyInstaller
2. Test thoroughly on different macOS versions
3. Create DMG installer
4. Write user documentation in Vietnamese
5. Distribute via website/email/cloud storage

---

**Note**: Người dùng vẫn cần cài Playwright browsers một lần. Để tránh điều này, bạn cần bundle Playwright browsers vào .app (phức tạp hơn và tăng kích thước app lên đáng kể).
