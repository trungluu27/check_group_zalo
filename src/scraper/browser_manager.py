from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from typing import Optional
import time
import sys
import platform
import shutil
from pathlib import Path


def _get_writable_chromedriver_dir() -> Path:
    """
    Return an OS-specific writable directory for a runtime ChromeDriver copy.
    Needed on macOS because App Translocation makes .app bundle paths read-only.
    """
    system = platform.system()
    app_name = "ZaloGroupChecker"

    if system == 'Windows':
        base = Path.home() / 'AppData' / 'Local' / app_name
    elif system == 'Darwin':
        base = Path.home() / 'Library' / 'Application Support' / app_name
    else:
        base = Path.home() / '.config' / app_name.lower()

    target = base / "runtime" / "chromedriver"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _looks_like_native_binary(path: Path) -> bool:
    """
    Lightweight binary format check to avoid Exec format errors.
    - macOS: must be Mach-O (thin or universal/fat)
    - Linux: must be ELF
    - Windows: must be PE (MZ)
    """
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
    except Exception:
        return False

    system = platform.system()
    if system == "Darwin":
        mach_o_magics = {
            b"\xfe\xed\xfa\xce",  # MH_MAGIC
            b"\xce\xfa\xed\xfe",  # MH_CIGAM
            b"\xfe\xed\xfa\xcf",  # MH_MAGIC_64
            b"\xcf\xfa\xed\xfe",  # MH_CIGAM_64
            b"\xca\xfe\xba\xbe",  # FAT_MAGIC
            b"\xbe\xba\xfe\xca",  # FAT_CIGAM
        }
        return magic in mach_o_magics
    if system == "Linux":
        return magic == b"\x7fELF"
    if system == "Windows":
        return magic[:2] == b"MZ"
    return True


def get_bundled_chromedriver_path() -> Optional[str]:
    """
    Return path to the bundled ChromeDriver binary if running as a frozen
    PyInstaller app; otherwise return None (use system/PATH chromedriver).
    """
    if not getattr(sys, 'frozen', False):
        return None

    bundle_dir = Path(sys._MEIPASS)
    system = platform.system()

    if system == 'Windows':
        driver_path = bundle_dir / 'chromedriver' / 'chromedriver.exe'
    elif system == 'Darwin':
        driver_path = bundle_dir / 'chromedriver' / 'chromedriver'
    else:
        driver_path = bundle_dir / 'chromedriver' / 'chromedriver'

    if driver_path.exists():
        if not _looks_like_native_binary(driver_path):
            # The bundled file is not a native executable for this OS/arch.
            # Ignore it so caller can use webdriver-manager/PATH fallback.
            return None

        # Never chmod inside the signed/translocated .app bundle.
        # Copy to a writable runtime location, then ensure +x there.
        runtime_dir = _get_writable_chromedriver_dir()
        runtime_driver = runtime_dir / driver_path.name
        try:
            shutil.copy2(driver_path, runtime_driver)
            if not _looks_like_native_binary(runtime_driver):
                return None
            if system != 'Windows':
                runtime_driver.chmod(0o755)
            return str(runtime_driver)
        except Exception:
            # Fallback to bundled path if copy unexpectedly fails.
            # This preserves previous behavior for non-translocated contexts.
            return str(driver_path)

    return None


class BrowserManager:
    """Manage Chrome browser instance via Selenium WebDriver with bundled ChromeDriver"""

    def __init__(self, headless: bool = False, timeout: int = 30):
        """
        Initialize browser manager.

        Args:
            headless: Run Chrome in headless mode (default: False so user can log in)
            timeout: Default wait timeout in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.driver: Optional[webdriver.Chrome] = None

        # Persistent browser profile folder (keeps cookies/session between app restarts)
        self.profile_dir = self._get_profile_dir()
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def launch(self) -> webdriver.Chrome:
        """
        Launch Chrome and return the WebDriver instance.

        Returns:
            selenium.webdriver.Chrome instance

        Raises:
            RuntimeError: If Chrome is not installed or ChromeDriver cannot start
        """
        options = self._build_chrome_options()
        service = self._build_service()

        try:
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(0)   # We use explicit waits everywhere
            return self.driver
        except WebDriverException as e:
            msg = str(e)
            if 'user data directory is already in use' in msg.lower():
                raise RuntimeError(
                    "Profile đăng nhập đang được dùng bởi một phiên khác.\n"
                    "Vui lòng đóng app/browser đang chạy rồi thử lại."
                ) from e
            if 'Chrome' in msg or 'chrome' in msg or 'binary' in msg.lower():
                raise RuntimeError(
                    "Không tìm thấy trình duyệt Chrome.\n\n"
                    "Vui lòng cài đặt Google Chrome tại:\n"
                    "https://www.google.com/chrome/\n\n"
                    f"Chi tiết lỗi: {msg}"
                ) from e
            raise RuntimeError(f"Không thể khởi động trình duyệt: {msg}") from e

    def navigate(self, url: str):
        """Navigate to URL."""
        self._assert_driver()
        self.driver.get(url)

    def wait_for_element(self, selector: str, timeout: Optional[int] = None,
                         state: str = 'visible'):
        """
        Wait for a CSS-selector element to reach the desired state.

        Args:
            selector: CSS selector string
            timeout: Seconds to wait (default: self.timeout)
            state: 'visible' | 'present' | 'clickable'
        """
        self._assert_driver()
        t = timeout or self.timeout
        wait = WebDriverWait(self.driver, t)

        by = By.CSS_SELECTOR
        if state == 'visible':
            wait.until(EC.visibility_of_element_located((by, selector)))
        elif state == 'clickable':
            wait.until(EC.element_to_be_clickable((by, selector)))
        else:
            wait.until(EC.presence_of_element_located((by, selector)))

    def find_element(self, selector: str):
        """Return first matching element or None."""
        self._assert_driver()
        try:
            return self.driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            return None

    def find_elements(self, selector: str) -> list:
        """Return all matching elements (empty list if none)."""
        self._assert_driver()
        return self.driver.find_elements(By.CSS_SELECTOR, selector)

    def execute_script(self, script: str, *args):
        """Execute JavaScript in the current page context."""
        self._assert_driver()
        return self.driver.execute_script(script, *args)

    def scroll_to_bottom(self, pause_time: float = 2.0):
        """Scroll the main window to the bottom."""
        self._assert_driver()
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(pause_time)

    def scroll_element(self, selector: str, pause_time: float = 1.0):
        """Scroll a specific element to its bottom."""
        self._assert_driver()
        self.driver.execute_script(
            """
            const el = document.querySelector(arguments[0]);
            if (el) { el.scrollTop = el.scrollHeight; }
            """,
            selector
        )
        time.sleep(pause_time)

    def clear_session(self) -> bool:
        """
        Clear persisted browser profile/session.

        Returns:
            True if session data existed and was cleared, False if nothing to clear.
        """
        # Ensure browser is closed before deleting profile files
        self.close()

        if not self.profile_dir.exists():
            return False

        had_data = any(self.profile_dir.iterdir())
        shutil.rmtree(self.profile_dir, ignore_errors=True)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        return had_data

    def close(self):
        """Quit the browser and clean up."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_profile_dir(self) -> Path:
        """Get OS-specific persistent profile directory for Selenium Chrome."""
        system = platform.system()

        if system == 'Windows':
            base = Path.home() / 'AppData' / 'Local'
            return base / 'ZaloGroupChecker' / 'chrome_profile'

        if system == 'Darwin':
            base = Path.home() / 'Library' / 'Application Support'
            return base / 'ZaloGroupChecker' / 'chrome_profile'

        # Linux/other
        base = Path.home() / '.config'
        return base / 'zalo_group_checker' / 'chrome_profile'

    def _build_chrome_options(self) -> Options:
        options = Options()

        if self.headless:
            options.add_argument('--headless=new')

        # Persistent session profile
        options.add_argument(f'--user-data-dir={self.profile_dir}')
        options.add_argument('--profile-directory=Default')

        # Stealth / stability flags
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280,800')
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        return options

    def _build_service(self) -> Service:
        bundled = get_bundled_chromedriver_path()
        if bundled:
            return Service(executable_path=bundled)

        # Fallback: try webdriver-manager (available when running from source)
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            return Service(ChromeDriverManager().install())
        except ImportError:
            pass

        # Last resort: assume chromedriver is on PATH
        return Service()

    def _assert_driver(self):
        if self.driver is None:
            raise RuntimeError("Browser not initialized. Call launch() first.")
