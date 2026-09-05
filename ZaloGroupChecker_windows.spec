# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for building the Windows one-dir .exe
# - Bundles ChromeDriver; users only need Google Chrome installed (NOT Python)
# - Mirrors the hardening applied to ZaloGroupChecker.spec (macOS) so the two
#   platforms stay in sync. Keep changes to both files together.
#
# Prerequisites (run once before building):
#   python resources\download_chromedriver.py
#
# Usage:
#   venv\Scripts\activate
#   pyinstaller ZaloGroupChecker_windows.spec --noconfirm

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# -----------------------------------------------------------------------
# ONEFILE=True  -> one self-contained dist\ZaloGroupChecker.exe to hand to a
#                  customer. Unpacks to %TEMP% on each launch (slower start).
# ONEFILE=False -> dist\ZaloGroupChecker\ folder (starts instantly, must be
#                  zipped whole for distribution).
# Override without editing this file:  set ZGC_ONEFILE=0
# -----------------------------------------------------------------------
ONEFILE = os.environ.get('ZGC_ONEFILE', '1') != '0'
print(f"[INFO] Build mode: {'onefile' if ONEFILE else 'onedir'}")

# -----------------------------------------------------------------------
# PyQt6 is deliberately NOT collect_all()'d here.
#
# The app imports only QtCore / QtGui / QtWidgets (see src/ui/main_window.py).
# collect_all('PyQt6') drags in the entire Qt6 tree — WebEngine, Quick3D, QML,
# Designer, Pdf, sqldrivers, 9 MB of translations — for a 308 MB bundle.
# PyInstaller's built-in PyQt6 hook does per-module dependency analysis and
# pulls exactly the Qt DLLs + plugins (platforms/qwindows.dll, styles,
# imageformats) that the imported modules need.
#
# The unused PyQt6 submodules are listed in `excludes` below so the hook does
# not follow them. If a Qt feature is ever added to the UI, remove the matching
# entry from that list.
# -----------------------------------------------------------------------

# Selenium + webdriver_manager (has .json data files we need)
sel_datas, sel_binaries, sel_hi = collect_all('selenium')
try:
    wdm_datas, wdm_binaries, wdm_hi = collect_all('webdriver_manager')
except Exception:
    wdm_datas, wdm_binaries, wdm_hi = [], [], []

# pandas ships quite a few C extensions that PyInstaller misses.
# Skip pandas.tests — collect_submodules would otherwise bundle the whole
# test suite (thousands of modules) into the customer's build.
pandas_hi = [m for m in collect_submodules('pandas') if '.tests' not in m]

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
# Bundle ChromeDriver binary (chromedriver.exe on Windows).
# Read at runtime from sys._MEIPASS/chromedriver/chromedriver.exe
# by scraper.browser_manager.get_bundled_chromedriver_path().
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
          "Run: python resources\\download_chromedriver.py")

icon_path = 'resources/icon.ico' if Path('resources/icon.ico').exists() else None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=chromedriver_binaries + sel_binaries + wdm_binaries,
    datas=[
        ('config.json', '.'),
        ('src', 'src'),           # keep src/ tree inside bundle so imports resolve
        # Just the icon, not the whole resources/ tree — that would ship a
        # second copy of chromedriver (21 MB) plus the build-time scripts.
        # Read at runtime by main.py for QApplication.setWindowIcon().
        ('resources/icon.ico', 'resources'),
    ] + sel_datas + wdm_datas,
    hiddenimports=[
        # PyQt6 — only the three modules the UI actually imports
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
    ] + sel_hi + wdm_hi + pandas_hi + local_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_runtime_hook.py'] if Path('pyi_runtime_hook.py').exists() else [],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'IPython', 'jupyter', 'playwright',
        'PyQt5', 'PySide2', 'PySide6',
        # Unused PyQt6 submodules — each one pulled in tens of MB of Qt DLLs,
        # QML plugins and shader tooling. The UI is QtWidgets-only.
        'PyQt6.QtQml', 'PyQt6.QtQuick', 'PyQt6.QtQuick3D', 'PyQt6.QtQuickWidgets',
        'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebEngineQuick',
        'PyQt6.QtWebChannel', 'PyQt6.QtWebSockets', 'PyQt6.QtWebView',
        'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets', 'PyQt6.QtSpatialAudio',
        'PyQt6.QtOpenGL', 'PyQt6.QtOpenGLWidgets',
        'PyQt6.QtSql', 'PyQt6.QtTest', 'PyQt6.QtHelp', 'PyQt6.QtDesigner',
        'PyQt6.QtPdf', 'PyQt6.QtPdfWidgets', 'PyQt6.QtCharts',
        'PyQt6.QtDataVisualization', 'PyQt6.QtBluetooth', 'PyQt6.QtNfc',
        'PyQt6.QtPositioning', 'PyQt6.QtLocation', 'PyQt6.QtSensors',
        'PyQt6.QtSerialPort', 'PyQt6.QtNetworkAuth', 'PyQt6.QtTextToSpeech',
        'PyQt6.QtRemoteObjects', 'PyQt6.QtStateMachine', 'PyQt6.QtDBus',
        'PyQt6.Qsci', 'PyQt6.uic',
        # Test suites — never needed at runtime
        'pandas.tests', 'numpy.tests', 'pytest', '_pytest',
        # Pillow is build-time only (resources/make_icon.py), not a runtime dep
        'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# -----------------------------------------------------------------------
# Post-analysis pruning.
#
# These files are pulled in by PyInstaller's own hooks (so they cannot be
# filtered out of the collect_all() lists above) and are dead weight in a
# Windows QtWidgets build. Removing them cuts ~42 MB.
#
# If the app ever shows a blank/black window on a customer machine with no
# working GPU driver (VM, Remote Desktop, very old laptop), the first thing
# to restore is 'opengl32sw.dll' — drop it from _PRUNE_NAMES and rebuild.
# -----------------------------------------------------------------------
_PRUNE_NAMES = {
    'opengl32sw.dll',    # 19.7 MB software OpenGL — unused by raster QtWidgets
    'qt6pdf.dll',        # 5.1 MB  PDF engine — QtPdf is excluded
    'qpdf.dll',          # imageformats plugin that needs Qt6Pdf.dll
}

# selenium ships the selenium-manager helper for all three OSes; keep Windows.
_PRUNE_PATH_FRAGMENTS = (
    'webdriver/common/linux/',
    'webdriver/common/macos/',
)


def _keep(entry) -> bool:
    dest = str(entry[0]).replace('\\', '/').lower()
    if Path(dest).name in _PRUNE_NAMES:
        return False
    return not any(frag in dest for frag in _PRUNE_PATH_FRAGMENTS)


_before = len(a.binaries) + len(a.datas)
a.binaries = [e for e in a.binaries if _keep(e)]
a.datas = [e for e in a.datas if _keep(e)]
print(f"[INFO] Pruned {_before - len(a.binaries) - len(a.datas)} bundled files")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_version_file = 'file_version_info.txt' if Path('file_version_info.txt').exists() else None

_common_exe_kwargs = dict(
    name='ZaloGroupChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # UPX corrupts Qt DLLs and trips antivirus heuristics
    console=False,             # GUI app — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,      # macOS-only feature
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    version=_version_file,
)

if ONEFILE:
    # Single self-contained .exe. Everything is unpacked to %TEMP%\_MEIxxxxxx
    # on every launch, so startup is slower than one-dir — keep the bundle lean.
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        runtime_tmpdir=None,
        **_common_exe_kwargs,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        **_common_exe_kwargs,
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
