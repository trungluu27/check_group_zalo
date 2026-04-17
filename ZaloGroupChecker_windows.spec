# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for building Windows .exe
# Bundles ChromeDriver so users only need Google Chrome installed (NOT Python/Selenium).
#
# Prerequisites (run once before building):
#   python resources/download_chromedriver.py
#
# Usage:
#   build_app_windows.bat          (recommended — handles everything)
#   -- OR --
#   pyinstaller ZaloGroupChecker_windows.spec --noconfirm

import os
from pathlib import Path

block_cipher = None

# -----------------------------------------------------------------------
# Bundle the ChromeDriver binary downloaded by resources/download_chromedriver.py
# -----------------------------------------------------------------------
chromedriver_dir = Path('resources/chromedriver')
chromedriver_binaries = []

if chromedriver_dir.exists():
    for f in chromedriver_dir.iterdir():
        if f.is_file():
            chromedriver_binaries.append((str(f), 'chromedriver'))
    print(f"[INFO] Bundling ChromeDriver: {list(chromedriver_dir.iterdir())}")
else:
    print("[WARNING] resources/chromedriver/ not found.")
    print("          Run: python resources/download_chromedriver.py")

# Detect icon file (optional)
icon_path = None
for candidate in ['resources/icon.ico', 'resources/icon.png']:
    if Path(candidate).exists():
        icon_path = candidate
        break

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
        # webdriver-manager (fallback when running from source)
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
        'numpy.testing',
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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    version='file_version_info.txt' if Path('file_version_info.txt').exists() else None,
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
