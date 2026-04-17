# Deployment Package Files

Để build ứng dụng thành file .app, bạn cần tạo các files sau:

## 1. ZaloGroupChecker.spec

File cấu hình PyInstaller để build .app bundle:

```python
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for building macOS .app bundle

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
        'Levenshtein',
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
    console=False,  # No terminal window
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
    icon=None,  # Add icon: 'resources/icon.icns'
    bundle_identifier='com.zalogroupchecker.app',
    info_plist={
        'CFBundleName': 'Zalo Group Checker',
        'CFBundleDisplayName': 'Zalo Group Checker',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'NSHumanReadableCopyright': 'Copyright © 2026',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Excel File',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': [
                    'org.openxmlformats.spreadsheetml.sheet',
                    'com.microsoft.excel.xls',
                ],
            }
        ],
    },
)
```

## 2. build_app.sh

Script tự động build .app:

```bash
#!/bin/bash
# Automated build script for creating macOS .app bundle

set -e  # Exit on error

echo "🔨 Building Zalo Group Checker for macOS..."
echo ""

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install PyInstaller
echo "📦 Installing PyInstaller..."
pip install --upgrade pyinstaller

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Build the app
echo "🏗️ Building .app bundle..."
pyinstaller ZaloGroupChecker.spec

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo "📁 App location: dist/ZaloGroupChecker.app"
    
    if [ -d "dist/ZaloGroupChecker.app" ]; then
        APP_SIZE=$(du -sh dist/ZaloGroupChecker.app | cut -f1)
        echo "📊 App size: $APP_SIZE"
        
        # Create DMG if create-dmg installed
        if command -v create-dmg &> /dev/null; then
            echo "📀 Creating DMG installer..."
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
            
            if [ -f "dist/ZaloGroupChecker-1.0.0.dmg" ]; then
                DMG_SIZE=$(du -sh dist/ZaloGroupChecker-1.0.0.dmg | cut -f1)
                echo "✅ DMG created: $DMG_SIZE"
            fi
        fi
        
        echo ""
        echo "🎉 Build complete!"
        echo "Test: open dist/ZaloGroupChecker.app"
    fi
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

## 3. HUONG_DAN_SU_DUNG.txt

Hướng dẫn chi tiết bằng tiếng Việt cho người dùng cuối - xem file [`plans/BUILD_MACOS_APP.md`](BUILD_MACOS_APP.md) phần "INSTALL_GUIDE.txt Template".

## Các bước thực hiện

### Bước 1: Tạo các file cần thiết

Chuyển sang Code mode và tạo:
- `ZaloGroupChecker.spec`
- `build_app.sh` 
- `HUONG_DAN_SU_DUNG.txt`

### Bước 2: Build ứng dụng

```bash
# Activate virtual environment
source venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Build
./build_app.sh
```

Hoặc thủ công:
```bash
pyinstaller ZaloGroupChecker.spec
```

### Bước 3: Test

```bash
# Test from command line
./dist/ZaloGroupChecker.app/Contents/MacOS/ZaloGroupChecker

# Or open normally
open dist/ZaloGroupChecker.app
```

### Bước 4: Tạo DMG (Optional)

```bash
# Install create-dmg
brew install create-dmg

# Create DMG
create-dmg \
  --volname "Zalo Group Checker" \
  --window-size 800 450 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  "ZaloGroupChecker-1.0.0.dmg" \
  "dist/"
```

### Bước 5: Phân phối

Package gồm:
- `ZaloGroupChecker-1.0.0.dmg` (hoặc .app)
- `HUONG_DAN_SU_DUNG.txt`
- `sample_usernames.xlsx`
- `README.pdf` (optional)

## Lưu ý quan trọng

⚠️ **Playwright Browser**: Người dùng vẫn phải cài Playwright browsers một lần:
```bash
pip3 install playwright
playwright install chromium
```

⚠️ **Kích thước**: File .app sẽ rất lớn (200-500MB) do chứa tất cả dependencies.

⚠️ **macOS Security**: Lần đầu chạy sẽ bị cảnh báo "unidentified developer". Người dùng phải:
- Vào System Preferences > Security & Privacy
- Click "Open Anyway"

⚠️ **Code Signing**: Để tránh cảnh báo, cần:
- Apple Developer Account ($99/năm)
- Code sign và notarize app

## Next Steps

Sau khi có file .app:

1. ✅ Test trên macOS sạch
2. ✅ Tạo hướng dẫn tiếng Việt
3. ✅ Package thành DMG
4. ✅ Upload lên cloud storage
5. ✅ Chia sẻ link download

Xem chi tiết tại [`plans/BUILD_MACOS_APP.md`](BUILD_MACOS_APP.md)
