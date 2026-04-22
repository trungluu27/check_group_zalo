# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for building macOS .app bundle
# - Bundles ChromeDriver; users need Google Chrome installed
# - Produces a proper macOS GUI .app (windowed, with Qt plugins + qt.conf)
#
# Prerequisites (run once before building):
#   python resources/download_chromedriver.py
#
# Usage:
#   source venv/bin/activate
#   pyinstaller ZaloGroupChecker.spec --noconfirm

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# -----------------------------------------------------------------------
# Collect PyQt6 — ships Qt frameworks, platforms/libqcocoa.dylib,
# imageformats/, styles/, qt.conf, etc.
# Without this the app crashes silently on launch on macOS.
# -----------------------------------------------------------------------
pyqt6_datas, pyqt6_binaries, pyqt6_hi = collect_all('PyQt6')

# Selenium + webdriver_manager (has .json data files we need)
sel_datas, sel_binaries, sel_hi = collect_all('selenium')
try:
    wdm_datas, wdm_binaries, wdm_hi = collect_all('webdriver_manager')
except Exception:
    wdm_datas, wdm_binaries, wdm_hi = [], [], []

# pandas ships quite a few C extensions that PyInstaller misses
pandas_hi = collect_submodules('pandas')

# -----------------------------------------------------------------------
# Our own subpackages under src/ (ui, excel, scraper, core)
# MUST be listed explicitly as hiddenimports, otherwise lazy imports
# inside WorkerThread.run() (e.g. `from excel.reader import ExcelReader`)
# will fail at runtime with ModuleNotFoundError and the app crashes.
# -----------------------------------------------------------------------
local_hiddenimports = [
    'ui', 'ui.main_window',
    'excel', 'excel.reader', 'excel.writer',
    'scraper', 'scraper.zalo_scraper',
    'scraper.browser_manager', 'scraper.browser_manager_bundled',
    'core', 'core.comparator',
]

# -----------------------------------------------------------------------
# Bundle ChromeDriver binary
# -----------------------------------------------------------------------
chromedriver_dir = Path('resources/chromedriver')
chromedriver_binaries = []
if chromedriver_dir.exists():
    for f in chromedriver_dir.iterdir():
        if f.is_file():
            chromedriver_binaries.append((str(f), 'chromedriver'))
    print(f"[INFO] Bundling ChromeDriver from: {chromedriver_dir}")
else:
    print("[WARNING] resources/chromedriver/ not found. "
          "Run: python resources/download_chromedriver.py")

entitlements_file = 'resources/entitlements.plist' \
    if Path('resources/entitlements.plist').exists() else None
icon_path = 'resources/icon.icns' if Path('resources/icon.icns').exists() else None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=chromedriver_binaries + pyqt6_binaries + sel_binaries + wdm_binaries,
    datas=[
        ('config.json', '.'),
        ('src', 'src'),           # keep src/ tree inside bundle so imports resolve
    ] + pyqt6_datas + sel_datas + wdm_datas,
    hiddenimports=[
        # PyQt6 (collect_all covers these, kept as safety net)
        'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.sip',
        # Selenium
        'selenium', 'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.common.exceptions',
        # webdriver-manager fallback
        'webdriver_manager', 'webdriver_manager.chrome',
        # Data processing
        'pandas',
        'openpyxl', 'openpyxl.workbook', 'openpyxl.styles', 'openpyxl.utils',
        'xlrd',
        # Fuzzy matching
        'fuzzywuzzy', 'fuzzywuzzy.fuzz', 'fuzzywuzzy.process', 'Levenshtein',
        # Helpers
        'pkg_resources', 'charset_normalizer',
        'encodings.utf_8', 'encodings.ascii', 'encodings.latin_1',
    ] + pyqt6_hi + sel_hi + wdm_hi + pandas_hi + local_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_runtime_hook.py'] if Path('pyi_runtime_hook.py').exists() else [],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'IPython', 'jupyter', 'playwright',
        'PyQt5', 'PySide2', 'PySide6',
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
    upx=False,                 # UPX breaks Qt .dylib signatures on macOS
    console=False,             # GUI app — no terminal window
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,          # native to host arch (arm64 on macos-14 runner)
    codesign_identity=None,
    entitlements_file=entitlements_file,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ZaloGroupChecker',
)

app = BUNDLE(
    coll,
    name='ZaloGroupChecker.app',
    icon=icon_path,
    bundle_identifier='com.zalogroupchecker.app',
    info_plist={
        'CFBundleName': 'Zalo Group Checker',
        'CFBundleDisplayName': 'Zalo Group Checker',
        'CFBundleExecutable': 'ZaloGroupChecker',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleInfoDictionaryVersion': '6.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '11.0',
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'NSHumanReadableCopyright': 'Copyright \u00a9 2026',
        'LSFileQuarantineEnabled': False,
        'NSAppleEventsUsageDescription':
            'Zalo Group Checker uses Google Chrome to access zalo.me.',
        'NSAppTransportSecurity': {'NSAllowsArbitraryLoads': True},
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
