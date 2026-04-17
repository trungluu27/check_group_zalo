# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for building macOS .app bundle
# Same as ZaloGroupChecker.spec — kept for backward compatibility.
# "with_browser" now means "with bundled ChromeDriver" (not full Chromium).
# Users need Google Chrome installed; ChromeDriver is bundled in the app.
#
# Prerequisites (run once before building):
#   python resources/download_chromedriver.py
#
# Usage:
#   source venv/bin/activate
#   pyinstaller ZaloGroupChecker_with_browser.spec --noconfirm

from pathlib import Path

block_cipher = None

# -----------------------------------------------------------------------
# Bundle the ChromeDriver binary
# -----------------------------------------------------------------------
chromedriver_dir = Path('resources/chromedriver')
chromedriver_binaries = []

if chromedriver_dir.exists():
    for f in chromedriver_dir.iterdir():
        if f.is_file():
            chromedriver_binaries.append((str(f), 'chromedriver'))
    print(f"[INFO] Bundling ChromeDriver from: {chromedriver_dir}")
else:
    print("[WARNING] resources/chromedriver/ not found.")
    print("          Run: python resources/download_chromedriver.py")

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=chromedriver_binaries,
    datas=[
        ('config.json', '.'),
        ('resources', 'resources'),
    ],
    hiddenimports=[
        # PyQt6
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        # Selenium
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.webdriver.support',
        'selenium.common.exceptions',
        'webdriver_manager',
        'webdriver_manager.chrome',
        # Data processing
        'pandas',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.skiplist',
        'openpyxl',
        'openpyxl.workbook',
        'openpyxl.styles',
        'openpyxl.utils',
        'xlrd',
        # Fuzzy matching
        'fuzzywuzzy',
        'fuzzywuzzy.fuzz',
        'fuzzywuzzy.process',
        'Levenshtein',
        # Helpers
        'pkg_resources',
        'charset_normalizer',
        'encodings.utf_8',
        'encodings.ascii',
        'encodings.latin_1',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'playwright',
    ],
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
    target_arch='universal2',
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.icns' if Path('resources/icon.icns').exists() else None,
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
    icon='resources/icon.icns' if Path('resources/icon.icns').exists() else None,
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
        'NSHumanReadableCopyright': 'Copyright \u00a9 2026',
        'LSFileQuarantineEnabled': False,
        'NSAppTransportSecurity': {
            'NSAllowsArbitraryLoads': True,
        },
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
