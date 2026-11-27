"""
Integration tests for locating the members entry in the Zalo group sidebar.

Regression cover for the customer-reported failure: some groups could not be
checked at all ("Không lấy được thành viên group ..."), while the same groups
worked from a different account.

Cause: the entry was located by DOM position
("...>div:nth-child(2)>div:last-child"). That position depends on how many
blocks the sidebar renders, which varies per account and per group, so the
selector picked a neighbouring block ("File") instead of the members entry.
The click succeeded, so the old code reported success while the panel had
never opened.

The sidebar mock below follows a real Zalo group-info panel:

    Thông tin nhóm
    <avatar> XT_002_Đi chiều
    [Tắt thông báo] [Ghim hội thoại] [Thêm thành viên] [Quản lý nhóm]
    Thành viên nhóm      v
      29 thành viên
    Bảng tin nhóm        v
      Danh sách nhắc hẹn
      Ghi chú, ghim, bình chọn
    Ảnh/Video            v
      ... Xem tất cả
    File                 v

Note "Thêm thành viên" in the action row: it also contains "thành viên" and
sits *above* the real entry, so a naive text search clicks it first and opens
the invite dialog. That is the trap these tests pin down.

Chrome is required; the whole case is skipped when Chrome or the bundled
ChromeDriver is unavailable.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraper.zalo_scraper import ZaloScraper  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMEDRIVER = PROJECT_ROOT / "resources" / "chromedriver" / "chromedriver.exe"

# Only the real entry opens the member panel. "Thêm thành viên" opens a modal
# that covers the sidebar, exactly like the invite dialog does — so a test can
# only pass if the code picks the right element AND recovers from a wrong one.
_PAGE = """
<html><body>
<main><header>
  <div><div icon="search">Tìm kiếm</div></div>
  <div><div icon="info">Thông tin nhóm</div></div>
</header></main>
<aside style="width:340px;height:700px;position:relative">
  <div id="sideBodyScrollBox"><div><div><div><div>
    <div class="hdr">Thông tin nhóm</div>
    <div class="grp"><div>XT_002_Đi chiều</div></div>
    <div class="actions">
      <div>Tắt thông báo</div>
      <div>Ghim hội thoại</div>
      <div id="ADD_MEMBER">Thêm thành viên</div>
      <div>Quản lý nhóm</div>
    </div>
    {blocks}
  </div></div></div></div></div>
  <div id="modal" style="display:none;position:absolute;inset:0;background:#fff;z-index:99">
    Thêm thành viên vào nhóm
  </div>
</aside>
<script>
  function openMembers() {{
    if (document.querySelector("div[id='member-group']")) return;
    var p = document.createElement('div');
    p.id = 'member-group';
    p.style.height = '200px';
    p.style.overflow = 'auto';
    p.innerHTML = "<div class='chat-box-member__info__name'><div>Nguyễn Văn A</div></div>"
                + "<div class='chat-box-member__info__name'><div>Trần Thị B</div></div>";
    document.querySelector('aside').appendChild(p);
  }}
  var entry = document.getElementById('REAL_MEMBERS');
  if (entry) {{ entry.onclick = openMembers; }}

  // The invite dialog: opens an overlay and blocks the sidebar underneath.
  var add = document.getElementById('ADD_MEMBER');
  if (add) {{ add.onclick = function () {{
    document.getElementById('modal').style.display = 'block';
  }}; }}
  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape') {{ document.getElementById('modal').style.display = 'none'; }}
  }});
</script>
</body></html>
"""

_MEMBERS_BLOCK = (
    "<div><div>Thành viên nhóm</div>"
    "<div id='REAL_MEMBERS'>29 thành viên</div></div>"
)
_FEED_BLOCK = (
    "<div><div>Bảng tin nhóm</div><div>Danh sách nhắc hẹn</div>"
    "<div>Ghi chú, ghim, bình chọn</div></div>"
)
_MEDIA_BLOCK = "<div><div>Ảnh/Video</div><div>Xem tất cả</div></div>"
_FILE_BLOCK = "<div><div>File</div><div>Chưa có File được chia sẻ</div></div>"

LAYOUTS = {
    # the layout in the screenshot
    "đầy đủ": _MEMBERS_BLOCK + _FEED_BLOCK + _MEDIA_BLOCK + _FILE_BLOCK,
    # a group with no media yet — one block fewer, shifts nth-child
    "chưa có ảnh/video": _MEMBERS_BLOCK + _FEED_BLOCK + _FILE_BLOCK,
    # an extra block above the members entry, e.g. pinned messages
    "có thêm khối phía trên": (
        "<div><div>Tin nhắn đã ghim</div><div>Xem tất cả</div></div>"
        + _MEMBERS_BLOCK + _FEED_BLOCK + _MEDIA_BLOCK + _FILE_BLOCK
    ),
    # members entry pushed to the very bottom
    "thành viên ở cuối": _FEED_BLOCK + _MEDIA_BLOCK + _FILE_BLOCK + _MEMBERS_BLOCK,
}


def _make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Chrome(service=Service(str(CHROMEDRIVER)), options=options)


@unittest.skipUnless(CHROMEDRIVER.exists(), f"ChromeDriver not found at {CHROMEDRIVER}")
class TestMemberButtonAcrossSidebarLayouts(unittest.TestCase):
    """The members entry must be found whatever else the sidebar contains."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.driver = _make_driver()
        except Exception as exc:  # Chrome missing / version mismatch
            raise unittest.SkipTest(f"Cannot start Chrome: {exc}")
        cls.tmp_dir = Path(os.environ.get("TEMP", ".")) / "zgc_sidebar_tests"
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.quit()
        except Exception:
            pass

    def _load(self, blocks: str) -> ZaloScraper:
        path = self.tmp_dir / "sidebar.html"
        path.write_text(_PAGE.format(blocks=blocks), encoding="utf-8")
        self.driver.get(path.as_uri())

        scraper = ZaloScraper.__new__(ZaloScraper)  # no browser launch
        scraper.driver = self.driver
        scraper._last_panel_focus_at = 0.0
        return scraper

    def test_member_list_opens_in_every_layout(self):
        for label, blocks in LAYOUTS.items():
            with self.subTest(layout=label):
                scraper = self._load(blocks)
                self.assertFalse(
                    scraper._is_member_list_open(),
                    "member panel should not exist before clicking",
                )
                self.assertTrue(
                    scraper._open_member_list(),
                    f"could not open the member list for layout: {label}",
                )
                self.assertTrue(scraper._is_member_list_open())

    def test_invite_button_is_never_a_candidate(self):
        """
        "Thêm thành viên" contains the keyword and sits above the real entry.
        It must be rejected outright, not merely ranked lower.
        """
        scraper = self._load(LAYOUTS["đầy đủ"])
        ids = {el.get_attribute("id") for el in scraper._find_member_button_candidates()}
        self.assertNotIn("ADD_MEMBER", ids, "invite button must not be a candidate")
        self.assertIn("REAL_MEMBERS", ids)

    def test_real_entry_is_ranked_first(self):
        """"29 thành viên" outranks the "Thành viên nhóm" section header."""
        scraper = self._load(LAYOUTS["đầy đủ"])
        candidates = scraper._find_member_button_candidates()
        self.assertTrue(candidates, "expected at least one candidate")
        self.assertEqual(candidates[0].get_attribute("id"), "REAL_MEMBERS")

    def test_candidate_lookup_skips_ancestors(self):
        """
        //*[contains(., 'Thành viên')] also matches <html> and <body>, so the
        old fallback clicked the whole page. Candidates must be innermost only.
        """
        scraper = self._load(LAYOUTS["đầy đủ"])
        tags = {el.tag_name.lower() for el in scraper._find_member_button_candidates()}
        self.assertNotIn("html", tags)
        self.assertNotIn("body", tags)
        self.assertNotIn("aside", tags)

    def test_recovers_after_a_wrong_click_opens_a_modal(self):
        """
        A wrong candidate can leave a modal covering the sidebar. The scraper
        must dismiss it and carry on instead of clicking the overlay forever.
        """
        scraper = self._load(LAYOUTS["đầy đủ"])
        self.driver.execute_script(
            "document.getElementById('ADD_MEMBER').click();"
        )
        self.assertTrue(
            self.driver.execute_script(
                "return document.getElementById('modal').style.display === 'block';"
            ),
            "precondition: the invite modal should be open",
        )

        scraper._dismiss_overlay()
        self.assertTrue(scraper._open_member_list())
        self.assertTrue(scraper._is_member_list_open())


if __name__ == '__main__':
    unittest.main()
