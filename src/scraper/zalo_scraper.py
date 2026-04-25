from scraper.browser_manager import BrowserManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
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
        self._last_panel_focus_at = 0.0

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

        if not self._is_member_list_open():
            if progress_callback:
                progress_callback("Member list not detected yet. Retrying: group info -> view members...")
            self._click_group_info_button(progress_callback)
            self._click_view_members_button(progress_callback)
            if not self._is_member_list_open():
                # Extra fallback for unstable DOM: click by text directly.
                self._try_click_members_by_xpath(progress_callback=progress_callback)
            time.sleep(2)

        if progress_callback:
            if self._is_member_list_open():
                progress_callback("✓ Member list is open and ready")
            else:
                progress_callback("⚠ Member list still not detected after retry")

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
            # JS fallback: find the element containing member-related text,
            # then click the nearest clickable ancestor.
            try:
                clicked = bool(self.driver.execute_script(
                    "var texts = ['xem th\u00e0nh vi\u00ean', 'th\u00e0nh vi\u00ean', 'members'];"
                    "var nodes = Array.from(document.querySelectorAll('aside div, aside button, aside span, aside a'));"
                    "for (var i = 0; i < nodes.length; i++) {"
                    "  var n = nodes[i];"
                    "  var t = (n.innerText || n.textContent || '').trim().toLowerCase();"
                    "  if (!t) { continue; }"
                    "  if (!texts.some(function(kw){ return t.indexOf(kw) >= 0; })) { continue; }"
                    "  var cur = n;"
                    "  for (var depth = 0; depth < 6 && cur; depth++) {"
                    "    var role = (cur.getAttribute && cur.getAttribute('role')) || '';"
                    "    var cls = (cur.className || '').toString();"
                    "    if (cur.tagName === 'BUTTON' || cur.tagName === 'A' || role === 'button' || cls.indexOf('btn') >= 0 || cur.onclick) {"
                    "      cur.click();"
                    "      return true;"
                    "    }"
                    "    cur = cur.parentElement;"
                    "  }"
                    "  n.click();"
                    "  return true;"
                    "}"
                    "return false;"
                ))
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
        # Scrape all group member names by scrolling the member list only.
        members: Set[str] = set()
        previous_count = 0
        stalled_rounds = 0
        stable_scroll_rounds = 0
        min_scroll_rounds = 10
        max_stalled_rounds = 12
        max_stable_scroll_rounds = 8

        if progress_callback:
            progress_callback("Starting to scrape group members...")

        primary_selector = "div[id='member-group'] div[class*='chat-box-member__info__name'] > div"
        fallback_selectors = [
            "div[id='member-group'] div[class*='member__info__name'] > div",
            "div[id='member-group'] div[class*='chat-box-member__info__name']",
            "div[id='member-group'] div[class*='member__info__name']",
            "div[class*='chat-box-member__info__name'] > div",
            "div[class*='member__info__name'] > div",
            "div[class*='chat-box-member__info__name']",
            "div[class*='member__info__name']",
        ]
        all_selectors = [primary_selector] + fallback_selectors
        working_selector = None
        forced_bottom_done = False

        for scroll_attempt in range(max_scrolls):
            try:
                if working_selector is None:
                    for sel in all_selectors:
                        els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        if els:
                            working_selector = sel
                            if progress_callback:
                                progress_callback(f"Using selector: {sel}")
                            break

                if working_selector:
                    self._collect_members_from_selector(
                        selector=working_selector,
                        members=members,
                        scroll_attempt=scroll_attempt,
                        progress_callback=progress_callback
                    )

                if len(members) == 0 and scroll_attempt in (0, 1):
                    members.update(self._extract_names_via_js())

                current_count = len(members)
                if current_count == previous_count:
                    stalled_rounds += 1
                else:
                    stalled_rounds = 0
                    if progress_callback:
                        progress_callback(f"Found {current_count} members so far...")
                previous_count = current_count

                scroll_state = self._scroll_member_list()
                if scroll_state.get("advanced", False) or scroll_state.get("max_remaining", 0) > 2:
                    stable_scroll_rounds = 0
                else:
                    stable_scroll_rounds += 1

                if progress_callback and scroll_attempt % 5 == 0:
                    progress_callback(
                        f"Scroll check: stalled={stalled_rounds}, stable_scroll={stable_scroll_rounds}, "
                        f"remaining_px={scroll_state.get('max_remaining', 0):.0f}"
                    )

                if (scroll_attempt >= min_scroll_rounds
                        and stalled_rounds >= max_stalled_rounds
                        and stable_scroll_rounds >= max_stable_scroll_rounds):
                    if progress_callback:
                        progress_callback("Running final forced scroll to absolute bottom before finishing...")
                    self._force_scroll_to_bottom(progress_callback=progress_callback)
                    forced_bottom_done = True
                    break

            except Exception as e:
                if progress_callback:
                    progress_callback(f"Error during scraping: {e}")
                continue

        if not forced_bottom_done:
            if progress_callback:
                progress_callback("Reached max scroll rounds. Running final forced-bottom safety pass...")
            self._force_scroll_to_bottom(progress_callback=progress_callback)

        # Final extraction pass after reaching bottom (stop early if no growth).
        if working_selector:
            stable_final_rounds = 0
            for _ in range(4):
                before_count = len(members)
                self._collect_members_from_selector(selector=working_selector, members=members)
                self._force_scroll_to_bottom(max_rounds=2)
                time.sleep(0.35)

                if len(members) == before_count:
                    stable_final_rounds += 1
                else:
                    stable_final_rounds = 0

                if stable_final_rounds >= 2:
                    break

        members.update(self._extract_names_via_js())

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

    def _try_click_members_by_xpath(self, progress_callback=None) -> bool:
        """
        Fallback click strategy for unstable DOM: click element by visible text.
        """
        xpaths = [
            "//*[contains(normalize-space(.), 'Xem thành viên')]",
            "//*[contains(normalize-space(.), 'Thành viên')]",
            "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'members')]",
        ]
        for xp in xpaths:
            try:
                candidates = self.driver.find_elements(By.XPATH, xp)
                for el in candidates:
                    txt = (el.text or "").strip()
                    if not txt:
                        continue
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    self.driver.execute_script("arguments[0].click();", el)
                    if progress_callback:
                        progress_callback(f"✓ Opened members list via text match: {txt[:40]}")
                    return True
            except Exception:
                continue
        return False

    def _is_member_list_open(self) -> bool:
        # Check if member list panel has been opened and populated.
        try:
            return bool(self.driver.execute_script(
                "var root = document.querySelector(\"div[id='member-group']\");"
                "if(!root){"
                "  var globalRows = document.querySelectorAll(\"div[class*='chat-box-member__info__name'], div[class*='member__info__name']\").length;"
                "  return globalRows > 0;"
                "}"
                "var hasRows = root.querySelectorAll(\"div[class*='chat-box-member'], div[class*='member__info__name']\").length > 0;"
                "var canScroll = (root.scrollHeight || 0) > (root.clientHeight || 0);"
                "return hasRows || canScroll;"
            ))
        except Exception:
            return False

    def _collect_members_from_selector(self, selector: str, members: Set[str],
                                       scroll_attempt: int = 0, progress_callback=None):
        # Collect member names from a strict selector inside member panel.
        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
        for el in elements:
            try:
                raw = (el.text or el.get_attribute("textContent") or "").strip()
                name = re.sub(r'\s+', ' ', raw).strip()
                if not self._is_valid_member_name(name):
                    continue
                if (progress_callback and scroll_attempt == 0 and len(members) < 12
                        and name not in members):
                    progress_callback(f"  Adding member: {name}")
                members.add(name)
            except Exception:
                continue

    def _is_valid_member_name(self, name: str) -> bool:
        # Filter out UI noise and keep only plausible person names.
        if not name:
            return False

        text = re.sub(r'\s+', ' ', name).strip()
        if len(text) < 2 or len(text) > 60:
            return False

        lower = text.lower()
        blocked_phrases = [
            "my documents", "documents", "mời thêm", "thêm thành viên", "kết bạn",
            "trưởng nhóm", "phó nhóm", "danh sách thành viên", "thành viên",
            "bạn:", "bạn bè", "members", "member list"
        ]
        if any(p in lower for p in blocked_phrases):
            return False

        # Exclude obvious non-name/UI patterns.
        if re.search(r'[:|()\[\]{}<>/\\]', text):
            return False
        if re.search(r'\b\d+\s*thành viên\b', lower):
            return False

        # Keep entries containing letters (Vietnamese supported).
        if not re.search(r'[A-Za-zÀ-Ỹà-ỹĐđ]', text):
            return False

        return True

    def _scroll_member_list(self) -> dict:
        # Scroll only the active member-list panel to avoid moving unrelated panes.
        try:
            state = self.driver.execute_script(
                "var target = document.querySelector(\"div[id='member-group']\");"
                "if(!target){"
                "  var candidates = Array.from(document.querySelectorAll(\"aside div[class*='scroll'], aside div[class*='list']\"));"
                "  target = candidates.sort(function(a,b){return (b.scrollHeight-b.clientHeight)-(a.scrollHeight-a.clientHeight);})[0] || null;"
                "}"
                "if(!target){"
                "  var row = document.querySelector(\"div[class*='chat-box-member__info__name'], div[class*='member__info__name']\");"
                "  if(row){ target = row.closest('aside') || row.parentElement; }"
                "}"
                "if(!target){return {advanced:false,max_remaining:0,container_count:0,target:'none'};}"
                "var before = target.scrollTop || 0;"
                "var maxTop = Math.max(0, target.scrollHeight - target.clientHeight);"
                "var step = Math.max(260, Math.floor(target.clientHeight * 0.9));"
                "var afterTarget = Math.min(maxTop, before + step);"
                "target.scrollTop = afterTarget;"
                "var after = target.scrollTop || 0;"
                "return {"
                "  advanced: after > before + 1,"
                "  max_remaining: Math.max(0, maxTop - after),"
                "  container_count: 1,"
                "  target: target.id || target.className || 'member-panel'"
                "};"
            )
            if not state or not state.get("advanced", False):
                # Fallback: simulate real user input to trigger virtualized lists.
                moved = self._user_like_scroll_member_panel(page_down_times=1)
                if moved and isinstance(state, dict):
                    state["advanced"] = True

            time.sleep(1.0)
            return state or {"advanced": False, "max_remaining": 0, "container_count": 0, "target": "none"}
        except Exception:
            self.browser_manager.scroll_to_bottom(pause_time=1.0)
            return {"advanced": True, "max_remaining": 0, "container_count": 0, "target": "fallback"}

    def _force_scroll_to_bottom(self, max_rounds: int = 40, progress_callback=None) -> dict:
        # Force the member panel to absolute bottom until stable.
        settled_rounds = 0
        last_state = {"advanced": False, "max_remaining": 0, "container_count": 0, "target": "none"}

        for i in range(max_rounds):
            try:
                state = self.driver.execute_script(
                    "var target = document.querySelector(\"div[id='member-group']\");"
                    "if(!target){"
                    "  var candidates = Array.from(document.querySelectorAll(\"aside div[class*='scroll'], aside div[class*='list']\"));"
                    "  target = candidates.sort(function(a,b){return (b.scrollHeight-b.clientHeight)-(a.scrollHeight-a.clientHeight);})[0] || null;"
                    "}"
                    "if(!target){"
                    "  var row = document.querySelector(\"div[class*='chat-box-member__info__name'], div[class*='member__info__name']\");"
                    "  if(row){ target = row.closest('aside') || row.parentElement; }"
                    "}"
                    "if(!target){return {advanced:false,max_remaining:0,container_count:0,target:'none'};}"
                    "var before = target.scrollTop || 0;"
                    "var maxTop = Math.max(0, target.scrollHeight - target.clientHeight);"
                    "target.scrollTop = maxTop;"
                    "var after = target.scrollTop || 0;"
                    "return {"
                    "  advanced: after > before + 1,"
                    "  max_remaining: Math.max(0, maxTop - after),"
                    "  container_count: 1,"
                    "  target: target.id || target.className || 'member-panel'"
                    "};"
                )
                last_state = state or last_state

                if not last_state.get("advanced", False) and i % 3 == 0:
                    # Throttled fallback: avoid repetitive click/keypress loops near the end.
                    moved = self._user_like_scroll_member_panel(
                        page_down_times=1,
                        press_end=(i >= max_rounds // 2)
                    )
                    if moved:
                        last_state["advanced"] = True

                if last_state.get("max_remaining", 0) <= 2:
                    settled_rounds += 1
                else:
                    settled_rounds = 0

                if progress_callback and i % 8 == 0:
                    progress_callback(
                        f"Forced-bottom progress: round={i+1}, "
                        f"remaining_px={last_state.get('max_remaining', 0):.0f}, "
                        f"target={last_state.get('target', 'unknown')}"
                    )

                if settled_rounds >= 3:
                    break

                time.sleep(0.9)
            except Exception:
                self.browser_manager.scroll_to_bottom(pause_time=0.9)
                time.sleep(0.3)

        return last_state

    def _focus_member_panel(self, force_click: bool = False):
        # Focus the member panel so keyboard scrolling affects correct container.
        # Keep click-to-focus behavior (works better on Zalo),
        # but throttle clicks to avoid repeated member clicks near list end.
        try:
            panel = self.driver.find_element(By.CSS_SELECTOR, "div[id='member-group']")
            now = time.time()
            should_click = force_click or (now - self._last_panel_focus_at > 1.5)
            if should_click:
                self.driver.execute_script("arguments[0].setAttribute('tabindex','-1');", panel)
                ActionChains(self.driver).move_to_element(panel).click(panel).perform()
                self._last_panel_focus_at = now
            return panel
        except Exception:
            return None

    def _user_like_scroll_member_panel(self, page_down_times: int = 1, press_end: bool = False) -> bool:
        # Simulate real keyboard scrolling as fallback when JS scrollTop is ignored.
        panel = self._focus_member_panel(force_click=False)
        if panel is None:
            return False

        try:
            before = self.driver.execute_script(
                "var p=document.querySelector(\"div[id='member-group']\");"
                "if(!p){return 0;} return p.scrollTop||0;"
            )
            max_top = self.driver.execute_script(
                "var p=document.querySelector(\"div[id='member-group']\");"
                "if(!p){return 0;} return Math.max(0,(p.scrollHeight||0)-(p.clientHeight||0));"
            )
            # Near bottom guard: skip keyboard fallback to avoid re-clicking members.
            if float(max_top or 0) - float(before or 0) <= 2:
                return False

            actions = ActionChains(self.driver)
            for _ in range(max(1, page_down_times)):
                actions.send_keys(Keys.PAGE_DOWN)
            if press_end:
                actions.send_keys(Keys.END)
            actions.perform()

            time.sleep(0.45)

            after = self.driver.execute_script(
                "var p=document.querySelector(\"div[id='member-group']\");"
                "if(!p){return 0;} return p.scrollTop||0;"
            )
            return float(after or 0) > float(before or 0) + 1
        except Exception:
            return False

    def _extract_names_via_js(self) -> Set[str]:
        # Scoped JS fallback: only parse name nodes inside member panel.
        try:
            raw = self.driver.execute_script(
                "var root = document.querySelector(\"div[id='member-group']\");"
                "if(!root){"
                "  var rows = Array.from(document.querySelectorAll(\"div[class*='chat-box-member__info__name'], div[class*='member__info__name']\"));"
                "  if(rows.length === 0){ return []; }"
                "  root = rows[0].closest('aside') || rows[0].parentElement || document.body;"
                "}"
                "var selectors = ["
                "  \"div[class*='chat-box-member__info__name']\","
                "  \"div[class*='member__info__name']\""
                "];"
                "var names = [];"
                "selectors.forEach(function(sel){"
                "  root.querySelectorAll(sel).forEach(function(el){"
                "    var text = (el.innerText || el.textContent || '').trim();"
                "    if(!text){ return; }"
                "    text.split('\\n').forEach(function(line){"
                "      var cl = line.trim();"
                "      if(cl && names.indexOf(cl) === -1){ names.push(cl); }"
                "    });"
                "  });"
                "});"
                "return names;"
            )
            if not raw:
                return set()

            cleaned: Set[str] = set()
            for candidate in raw:
                name = re.sub(r'\s+', ' ', str(candidate or '')).strip()
                if self._is_valid_member_name(name):
                    cleaned.add(name)
            return cleaned
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
