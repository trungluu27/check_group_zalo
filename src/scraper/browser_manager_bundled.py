from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from typing import Optional
import time
import os
import sys
from pathlib import Path


class BrowserManager:
    """Manage Playwright browser instance with support for bundled browsers"""
    
    def __init__(self, headless: bool = False, timeout: int = 30000):
        """
        Initialize browser manager
        
        Args:
            headless: Run browser in headless mode (default: False for debugging)
            timeout: Default timeout in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # Set browser path for bundled app
        self._setup_browser_path()
        
    def _setup_browser_path(self):
        """Setup browser path for bundled or installed browsers"""
        # Check if running as bundled app
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            bundle_dir = Path(sys._MEIPASS)
            browser_path = bundle_dir / 'ms-playwright' / 'chromium'
            
            if browser_path.exists():
                # Use bundled browser
                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(bundle_dir / 'ms-playwright')
                print(f"Using bundled browser at: {browser_path}")
            else:
                # Fall back to system-installed browsers
                print("Bundled browser not found, using system browsers")
                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'
        else:
            # Running from source, use system browsers
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'
        
    def launch(self) -> Page:
        """
        Launch browser and return page instance
        
        Returns:
            Playwright Page object
        """
        self.playwright = sync_playwright().start()
        
        # Launch browser with settings to avoid detection
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        # Create context with realistic viewport and user agent
        context = self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = context.new_page()
        self.page.set_default_timeout(self.timeout)
        
        return self.page
    
    def navigate(self, url: str):
        """
        Navigate to URL
        
        Args:
            url: URL to navigate to
            
        Raises:
            Exception: If browser not initialized
        """
        if not self.page:
            raise Exception("Browser not initialized. Call launch() first.")
        self.page.goto(url, wait_until='networkidle')
        
    def wait_for_element(self, selector: str, timeout: Optional[int] = None, state: str = 'visible'):
        """
        Wait for element to appear
        
        Args:
            selector: CSS selector for element
            timeout: Timeout in milliseconds (optional)
            state: Element state to wait for (visible, attached, hidden)
        """
        timeout = timeout or self.timeout
        self.page.wait_for_selector(selector, timeout=timeout, state=state)
        
    def scroll_to_bottom(self, pause_time: float = 2.0):
        """
        Scroll to bottom of page
        
        Args:
            pause_time: Time to wait after scrolling (seconds)
        """
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(pause_time)
    
    def scroll_element(self, selector: str, pause_time: float = 1.0):
        """
        Scroll specific element to bottom
        
        Args:
            selector: CSS selector for scrollable element
            pause_time: Time to wait after scrolling
        """
        self.page.evaluate(f"""
            (selector) => {{
                const element = document.querySelector(selector);
                if (element) {{
                    element.scrollTop = element.scrollHeight;
                }}
            }}
        """, selector)
        time.sleep(pause_time)
        
    def close(self):
        """Close browser and cleanup resources"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
