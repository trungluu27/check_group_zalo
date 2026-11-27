import sys
import os
import traceback
from pathlib import Path

# Limit BLAS/OpenMP thread fan-out to avoid macOS ARM stack-guard
# crashes in worker threads (OpenBLAS dgetrf_parallel / dgesv paths).
# setdefault keeps user-provided values untouched.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")


def _get_writable_dir() -> Path:
    """
    Return a writable base directory for logs / output / cache.

    Critical for macOS .app bundles:
      - sys.executable lives inside /Applications/Xxx.app/Contents/MacOS/
        which is READ-ONLY (signed bundle).
      - Writing there raises PermissionError and crashes the app silently
        before the logger is even initialised.
      - Fall back to ~/Library/Application Support/<AppName> on macOS,
        %APPDATA%/<AppName> on Windows, ~/.<appname> otherwise.
    """
    app_name = "ZaloGroupChecker"

    if getattr(sys, 'frozen', False):
        if sys.platform == 'darwin':
            base = Path.home() / "Library" / "Application Support" / app_name
        elif sys.platform.startswith('win'):
            base = Path(os.environ.get('APPDATA', Path.home())) / app_name
        else:
            base = Path.home() / f".{app_name.lower()}"
    else:
        # Running from source: use project root (parent of src/)
        base = Path(__file__).parent.parent

    base.mkdir(parents=True, exist_ok=True)
    return base


def get_resource_dir() -> Path:
    """
    Return the directory containing bundled read-only resources
    (config.json, icon, chromedriver, etc.).

    - Frozen: sys._MEIPASS (PyInstaller temp extraction dir) OR the
      executable's folder, depending on one-file vs one-dir mode.
    - Source: project root.
    """
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def _write_early_crash_log(exc: BaseException) -> None:
    """
    Write a crash log to a writable location BEFORE the logger is set up.
    This is the only way to diagnose silent crashes on macOS .app bundles.
    """
    try:
        base = _get_writable_dir()
        crash_file = base / "startup_crash.log"
        with open(crash_file, "a", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            import datetime
            f.write(f"Crash at {datetime.datetime.now().isoformat()}\n")
            f.write(f"Python: {sys.version}\n")
            f.write(f"Platform: {sys.platform}\n")
            f.write(f"Executable: {sys.executable}\n")
            f.write(f"Frozen: {getattr(sys, 'frozen', False)}\n")
            f.write(f"MEIPASS: {getattr(sys, '_MEIPASS', None)}\n")
            f.write(f"sys.path: {sys.path}\n")
            f.write(f"CWD: {os.getcwd()}\n")
            f.write("Traceback:\n")
            f.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
            f.write("\n")
    except Exception:
        # Last resort — cannot even write a crash log
        pass


def setup_logging(data_dir: Path):
    """Setup logging configuration with correct path for frozen apps"""
    import logging

    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    handlers = [logging.FileHandler(str(log_file), encoding='utf-8')]
    # StreamHandler only if stdout exists (console=False builds have no stdout)
    if sys.stdout is not None:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True,
    )


def setup_directories(data_dir: Path):
    """Create necessary writable directories"""
    (data_dir / "output").mkdir(parents=True, exist_ok=True)
    (data_dir / "logs").mkdir(parents=True, exist_ok=True)


def run_selftest() -> int:
    """
    Import every module the app loads lazily and check bundled drivers,
    then exit. Used by CI: the launch smoke test only proves the window
    opens, while pandas/openpyxl/selenium are imported only when the user
    presses Start — a missing module there would otherwise ship unnoticed.
    """
    import importlib
    import subprocess

    failures = []
    modules = [
        "PyQt6.QtWidgets", "pandas", "openpyxl", "xlrd",
        "fuzzywuzzy.fuzz", "Levenshtein",
        "selenium.webdriver", "selenium.webdriver.chrome.service",
        "webdriver_manager.chrome",
        "ui.main_window", "excel.reader", "excel.writer",
        "scraper.zalo_scraper", "scraper.browser_manager", "core.comparator",
    ]
    for name in modules:
        try:
            importlib.import_module(name)
            print(f"[OK]   import {name}")
        except Exception as e:
            failures.append(name)
            print(f"[FAIL] import {name}: {e!r}")

    # Excel round trip through pandas + openpyxl.
    try:
        import tempfile
        import pandas as pd
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.xlsx"
            pd.DataFrame({"a": [1, 2]}).to_excel(p, index=False)
            assert len(pd.read_excel(p)) == 2
        print("[OK]   excel read/write")
    except Exception as e:
        failures.append("excel")
        print(f"[FAIL] excel read/write: {e!r}")

    # Bundled ChromeDriver must actually execute (signature / arch / +x).
    try:
        from scraper.browser_manager import get_bundled_chromedriver_path
        drv = get_bundled_chromedriver_path()
        if drv:
            out = subprocess.run([drv, "--version"], capture_output=True,
                                 text=True, timeout=20)
            if out.returncode == 0:
                print(f"[OK]   bundled chromedriver: {out.stdout.strip()}")
            else:
                failures.append("chromedriver")
                print(f"[FAIL] bundled chromedriver rc={out.returncode}: {out.stderr}")
        else:
            print("[WARN] no bundled chromedriver (Selenium Manager fallback only)")
    except Exception as e:
        failures.append("chromedriver")
        print(f"[FAIL] bundled chromedriver: {e!r}")

    # Selenium Manager is the fallback when the bundled driver is outdated.
    try:
        from selenium.webdriver.common.selenium_manager import SeleniumManager
        sm = SeleniumManager()
        path = sm._get_binary() if hasattr(sm, "_get_binary") else sm.get_binary()
        out = subprocess.run([str(path), "--version"], capture_output=True,
                             text=True, timeout=20)
        if out.returncode == 0:
            print(f"[OK]   selenium-manager: {out.stdout.strip()}")
        else:
            failures.append("selenium-manager")
            print(f"[FAIL] selenium-manager rc={out.returncode}: {out.stderr}")
    except Exception as e:
        failures.append("selenium-manager")
        print(f"[FAIL] selenium-manager: {e!r}")

    print("SELFTEST", "FAILED: " + ", ".join(failures) if failures else "PASSED")
    return 1 if failures else 0


def main():
    """Main application entry point"""
    # ------------------------------------------------------------------
    # Ensure src/ subpackages (ui, excel, scraper, core) are importable
    # whether frozen or running from source.
    # ------------------------------------------------------------------
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass and meipass not in sys.path:
            sys.path.insert(0, meipass)
    else:
        src_dir = str(Path(__file__).parent)
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)

    # ------------------------------------------------------------------
    # Resolve writable data dir (logs/, output/) — NOT inside .app bundle
    # ------------------------------------------------------------------
    data_dir = _get_writable_dir()

    # When frozen, chdir to the writable data dir so relative paths
    # like "output/..." land in a writable place. Never chdir into the
    # read-only .app bundle.
    if getattr(sys, 'frozen', False):
        try:
            os.chdir(str(data_dir))
        except Exception:
            pass

    # Create directories
    setup_directories(data_dir)

    # Setup logging
    setup_logging(data_dir)

    if "--selftest" in sys.argv:
        sys.exit(run_selftest())

    import logging
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Starting Zalo Group Membership Checker")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Resource directory: {get_resource_dir()}")
    logger.info(f"Frozen: {getattr(sys, 'frozen', False)}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {sys.platform}")

    # ------------------------------------------------------------------
    # Qt / UI — import LAZILY so any ImportError gets caught and logged
    # ------------------------------------------------------------------
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QIcon
        from ui.main_window import MainWindow
    except Exception as e:
        logger.exception("Failed to import Qt / UI modules")
        _write_early_crash_log(e)
        raise

    app = QApplication(sys.argv)
    app.setApplicationName("Zalo Group Membership Checker")

    # Window icon (title bar, Alt-Tab, taskbar). The .exe's own icon is set
    # separately by PyInstaller — this one is what Qt draws at runtime.
    # Setting it on the QApplication means dialogs inherit it too.
    # macOS takes the Dock icon from the bundle's .icns; the PNG is a
    # fallback for dialogs. Windows prefers the multi-size .ico.
    icon_names = ["icon.png", "icon.ico"] if sys.platform == "darwin" \
        else ["icon.ico", "icon.png"]
    icon_file = next(
        (get_resource_dir() / "resources" / n for n in icon_names
         if (get_resource_dir() / "resources" / n).exists()),
        None,
    )
    if icon_file:
        app.setWindowIcon(QIcon(str(icon_file)))
        logger.info(f"Window icon loaded: {icon_file}")
    else:
        logger.warning(f"Window icon not found in {get_resource_dir() / 'resources'}")

    window = MainWindow()
    window.show()

    logger.info("Application window displayed")
    sys.exit(app.exec())


if __name__ == '__main__':
    try:
        main()
    except BaseException as e:
        # Silent-crash insurance: always dump a crash log users can send us.
        _write_early_crash_log(e)
        raise
