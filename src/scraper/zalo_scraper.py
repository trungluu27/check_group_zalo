from scraper.browser_manager import BrowserManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from typing import Set
import time
import re


class ZaloScraper:
    # Scrape Zalo group members using Selenium WebDriver

    def __init__(self, group_url: str, headless: bool = False):
        self.group_url = group_url
        self.browser_manager = BrowserManager(headless=headless)
        self.driver = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self):
        # Launch Chrome and store driver reference.
        self.driver = self.browser_manager.launch()

    def close(self):
        # Close browser and release resources.
        self.browser_manager.close()
        self.driver = None

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def wait_for_login(self, timeout: int = 300, progress_callback=None) -> bool:
        # Navigate to Zalo Web and wait for the user to log in manually.
        # Returns True when login is detected, False on timeout.
        if progress_callback:
            progress_callback("Opening Zalo Web...")

        self.driver.get("https://chat.zalo.me/")

        if progress_callback:
            progress_callback("Please log in to Zalo Web in the browser window...")
            progress_callback("Waiting for login (this may take a few minutes)...")

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[class*='chat'], div[class*='conversation'], div[id*='main']"
                )
                if elements:
                    if progress_callback:
                        progress_callback("Login successful!")
                    time.sleep(2)
                    return True
            except Exception:
                pass
            time.sleep(2)

        if progress_callback:
            progress_callback("Login timeout or failed.")
        return False

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate_to_group(self, progress_callback=None):
        # Navigate to the group page and open the member list panel.
        if not self.driver:
            raise RuntimeError("Browser not initialized. Call initialize() first.")

        if progress_callback:
            progress_callback(f"Navigating to group: {self.group_url}")

        self.driver.get(self.group_url)
        time.sleep(3)

        if progress_callback:
            progress_callback("Arrived at group page")

        self._click_group_info_button(progress_callback)
        self._click_view_members_button(progress_callback)
        time.sleep(2)

    def _click_group_info_button(self, progress_callback=None):
        selectors = [
            "main header>div:nth-child(2)>div[icon]",
            "main header div[icon]",
            "header div[class*='info']",
            "button[class*='info']",
        ]
        if self._try_click_selectors(selectors):
            if progress_callback:
                progress_callback("\u2713 Opened group info panel")
        else:
            if progress_callback:
                progress_callback("\u26a0 Could not find group info button \u2014 continuing anyway")
        time.sleep(2)

    def _click_view_members_button(self, progress_callback=None):
        selectors = [
            "aside div[id='sideBodyScrollBox'] >div >div>div>div>div:nth-child(2)>div:last-child",
            "aside div[id='sideBodyScrollBox'] div:last-child",
            "aside div[class*='scroll'] div:last-child",
        ]
        clicked = self._try_click_selectors(selectors)
        if not clicked:
            # JS fallback: find element containing member-related Vietnamese text
            try:
                self.driver.execute_script(
                    "var texts = ['Xem th\u00e0nh vi\u00ean', 'th\u00e0nh vi\u00ean', 'members'];"
                    "var all = document.querySelectorAll('aside div, aside button, aside span');"
                    "for (var i = 0; i < all.length; i++) {"
                    "  var t = (all[i].innerText || '').trim().toLowerCase();"
                    "  if (texts.some(function(kw){return t.indexOf(kw.toLowerCase())>=0;}) && all[i].children.length===0){"
                    "    all[i].click(); break;"
                    "  }"
                    "}"
                )
                clicked = True
            except Exception:
                pass

        if clicked and progress_callback:
            progress_callback("\u2713 Opened members list")
        elif progress_callback:
            progress_callback("\u26a0 Could not find view members button \u2014 continuing anyway")
        time.sleep(2)

    # ------------------------------------------------------------------
    # Debug
    # ------------------------------------------------------------------

    def debug_page_structure(self, progress_callback=None):
        # Log counts of elements matching common member-related keywords.
        try:
            result = self.driver.execute_script(
                "var keywords = ['member','contact','user','name','list','item'];"
                "var out = {};"
                "keywords.forEach(function(kw){"
                "  var els = document.querySelectorAll('[class*=\"'+kw+'\"]');"
                "  if(els.length>0){"
                "    out[kw]={count:els.length,samples:Array.from(els).slice(0,3).map(function(el){"
                "      return {tag:el.tagName,cls:el.className,text:(el.innerText||'').substring(0,50)};"
                "    })};"
                "  }"
                "});"
                "return out;"
            )
            if progress_callback and result:
                progress_callback("=== Page Structure Debug Info ===")
                for kw, info in result.items():
                    progress_callback(f"{kw}: {info['count']} elements")
                    for i, s in enumerate(info.get("samples", [])):
                        progress_callback(f"  [{i+1}] {s['tag']}.{str(s['cls'])[:50]} | {str(s['text'])[:30]}")
        except Exception as e:
            if progress_callback:
                progress_callback(f"Debug failed: {e}")

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------

    def scrape_members(self, max_scrolls: int = 100, progress_callback=None) -> Set[str]:
        # Scrape all group member names by scrolling the member list.
        # Returns a set of unique member name strings.
        members: Set[str] = set()
        previous_count = 0
        no_change_count = 0

        if progress_callback:
            progress_callback("Starting to scrape group members...")
            progress_callback("Analyzing page structure...")

        try:
            page_text = self.driver.execute_script("return document.body.innerText")
            if progress_callback and page_text:
                progress_callback(f"Page has {len(page_text)} characters of text")
        except Exception:
            pass

        primary_selector = "div[id='member-group'] div[class='chat-box-member__info__name v2']>div"
        fallback_selectors = [
            "div[id='member-group'] div[class*='chat-box-member__info__name']>div",
            "div[id='member-group'] div[class*='member__info__name']>div",
            "div[id='member-group'] div[class*='name']",
            "div[class*='MemberItem']",
            "div[class*='member-item']",
            "div[class*='chat-box-member']",
        ]
        all_selectors = [primary_selector] + fallback_selectors
        working_selector = None

        for scroll_attempt in range(max_scrolls):
            try:
                # Discover a working selector on the first attempt
                if working_selector is None:
                    for sel in all_selectors:
                        els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        if els:
                            working_selector = sel
                            if progress_callback:
                                label = "primary" if sel == primary_selector else "fallback"
                                progress_callback(f"\u2713 Using {label} selector: {sel[:60]}")
                                progress_callback(f"  Found {len(els)} member elements")
                            break

                # Extract names from currently visible elements
                if working_selector:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, working_selector)
                    for el in elements:
                        try:
                            raw = el.get_attribute("innerHTML") or ""
                            name = raw.replace("&nbsp;", " ").strip()
                            if not name:
                                name = (el.text or "").strip()
                            name = re.sub(r'\s+', ' ', name).strip()
                            if name and 2 <= len(name) <= 100 and any(c.isalpha() for c in name):
                                if (scroll_attempt == 0 and len(members) < 15
                                        and name not in members and progress_callback):
                                    progress_callback(f"  Adding member: {name}")
                                members.add(name)
                        except Exception:
                            continue

                # JS fallback on first scroll if no names found yet
                if len(members) == 0 and scroll_attempt == 0:
                    js_names = self._extract_names_via_js()
                    if js_names and progress_callback:
                        progress_callback(f"JavaScript extraction found {len(js_names)} potential names")
                    members.update(js_names)

                current_count = len(members)
                if current_count == previous_count:
                    no_change_count += 1
                else:
                    no_change_count = 0
                    if progress_callback:
                        progress_callback(f"Found {current_count} members so far...")
                previous_count = current_count

                if no_change_count >= 5:
                    if progress_callback:
                        progress_callback("No new members after multiple scrolls. Finishing...")
                    break

                self._scroll_member_list()

            except Exception as e:
                if progress_callback:
                    progress_callback(f"Error during scraping: {e}")
                continue

        if progress_callback:
            progress_callback(f"Scraping complete! Total unique members found: {len(members)}")
        return members

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _try_click_selectors(self, selectors: list) -> bool:
        # Try each CSS selector; click the first match. Return True if clicked.
        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                el.click()
                return True
            except Exception:
                continue
        return False

    def _scroll_member_list(self):
        # Scroll the member list container using multiple strategies.
        try:
            self.driver.execute_script(
                "var mg = document.querySelector(\"div[id='member-group']\");"
                "if(mg){mg.scrollTop=mg.scrollHeight;}"
            )
            self.driver.execute_script(
                "var sb = document.querySelector(\"aside div[id='sideBodyScrollBox']\");"
                "if(sb){sb.scrollTop=sb.scrollHeight;}"
            )
            self.driver.execute_script(
                "document.querySelectorAll(\"aside div[class*='scroll'],aside div[class*='list']\")"
                ".forEach(function(c){if(c.scrollHeight>c.clientHeight){c.scrollTop=c.scrollHeight;}});"
            )
            time.sleep(1.5)
        except Exception:
            self.browser_manager.scroll_to_bottom(pause_time=1.5)

    def _extract_names_via_js(self) -> Set[str]:
        # Last-resort JS scrape: collect any text matching name patterns.
        try:
            raw = self.driver.execute_script(
                "var names = [];"
                "var kws = ['member','contact','user','name'];"
                "kws.forEach(function(kw){"
                "  document.querySelectorAll('[class*=\"'+kw+'\"]').forEach(function(el){"
                "    var text = (el.innerText||'').trim();"
                "    if(text && text.length>=2 && text.length<=100){"
                "      if(/[a-zA-Z\u00C0-\u024F\u1E00-\u1EFF]/.test(text)){"
                "        text.split('\\n').forEach(function(line){"
                "          var cl=line.trim();"
                "          if(cl.length>=2 && cl.length<=100 && names.indexOf(cl)===-1) names.push(cl);"
                "        });"
                "      }"
                "    }"
                "  });"
                "});"
                "return names;"
            )
            return set(raw) if raw else set()
        except Exception:
            return set()

    def get_group_info(self) -> dict:
        # Return basic group information (best-effort).
        info = {"url": self.group_url, "name": "Unknown", "member_count": 0}
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR, "h1, h2, h3, [class*='title'], [class*='name']"
            )
            info["name"] = (el.text or "").strip()
        except Exception:
            pass
        return info
