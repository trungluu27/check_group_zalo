# Changelog

## [1.3.0] - 2026-02-12 (Latest)

### Added - Persistent Session (No Re-login Needed!)
- ✨ **Persistent browser context** - Login once, use forever!
- ✨ Session data automatically saved between runs
- ✨ "Clear Login Session" button to logout when needed
- ✨ Session stored in: `~/.zalo_checker_browser_data`
- ✨ Helpful UI message explaining the persistent session feature

### Changed
- 🔧 `BrowserManager` now uses persistent context by default
- 🔧 Updated UI with session management button
- 🔧 Improved user experience - no repeated logins

### Files Modified
1. `src/scraper/browser_manager.py` - Added persistent context support
2. `src/ui/main_window.py` - Added clear session button and handler
3. `README.md` - Added login session management section
4. `CHANGELOG.md` - This file

### Migration Notes
- Existing users will automatically get persistent session on next run
- Old browser data (if any) will not interfere
- To disable persistent mode: Set `use_persistent_context=False` in BrowserManager

---

## [1.2.0] - 2026-02-12

### Fixed - Critical Scraping Issue
- ✅ **Fixed member scraping using exact Zalo Web selectors from real inspection**
- ✅ Implemented proper 3-step process: Info button → Members button → Member names
- ✅ Fixed &nbsp; (non-breaking space) handling in member names
- ✅ Corrected scroll mechanism to target specific containers (member-group, sideBodyScrollBox)

### Added - Zalo-Specific Implementation
- ✨ **Exact selectors from Zalo Web inspection:**
  - Info button: `main header>div:nth-child(2)>div[icon]`
  - Members button: `aside div[id='sideBodyScrollBox'] >div >div>div>div>div:nth-child(2)>div:last-child`
  - Member names: `div[id='member-group'] div[class='chat-box-member__info__name v2']>div`
- ✨ Created `ZALO_SELECTORS.md` - comprehensive selector documentation with test commands
- ✨ Created `test_setup.py` - verification script to test all changes
- ✨ innerHTML parsing to handle &nbsp; correctly
- ✨ Smart scroll targeting for member-group container

### Improved
- 🔧 Better progress messages showing which selector is being used
- 🔧 Fallback selectors for each step in case Zalo updates
- 🔧 More reliable button clicking sequence
- 🔧 Wait times optimized for UI loading

### Files Modified
1. `src/scraper/zalo_scraper.py` - Complete rewrite of navigation and scraping logic
2. `CHANGELOG.md` - This file

### Files Added
1. `ZALO_SELECTORS.md` - Detailed selector documentation
2. `test_setup.py` - Setup verification script

---

## [1.1.0] - 2026-02-12

### Fixed
- ✅ Fixed PyQt6 DLL load error on Windows by updating to version 6.7.1
- ✅ Fixed "attempted relative import beyond top-level package" error by converting to absolute imports
- ✅ Improved member scraping with enhanced selectors and fallback methods

### Added
- ✨ Added debug mode to analyze Zalo Web page structure
- ✨ Added automatic detection of member list buttons ("Xem thành viên")
- ✨ Added JavaScript-based fallback extraction method
- ✨ Added enhanced logging and progress messages
- ✨ Created `DEBUG_SELECTORS.md` - comprehensive guide for troubleshooting selector issues
- ✨ Created `browser_console_helper.js` - browser console tool to find correct selectors
- ✨ Added Vietnamese character support in name extraction

### Improved
- 🔧 Enhanced selector patterns for better Zalo Web compatibility
- 🔧 Improved name filtering to skip UI text and system messages
- 🔧 Better error messages and progress feedback
- 🔧 More robust scrolling mechanism for member list

### Changed
- 📝 Updated `requirements.txt` with PyQt6==6.7.1
- 📝 Updated README.md with detailed troubleshooting section
- 🔄 Changed from relative imports to absolute imports in all modules

### Technical Details

#### Import Changes
**Before:**
```python
from ..excel.reader import ExcelReader
from .browser_manager import BrowserManager
```

**After:**
```python
from excel.reader import ExcelReader
from scraper.browser_manager import BrowserManager
```

#### New Selectors Added
- `div[class*="MemberItem"]`
- `div[class*="ContactItem"]`
- `div[class*="UserItem"]`
- `div[class*="member"] span[class*="name"]`
- And 15+ more patterns

#### New Methods
- `debug_page_structure()` - Analyzes page HTML structure
- JavaScript-based extraction as fallback when selectors fail
- Automatic member list button detection

### Files Modified
1. `requirements.txt` - Updated PyQt6 version
2. `src/ui/main_window.py` - Fixed imports, added debug call
3. `src/scraper/zalo_scraper.py` - Enhanced scraping logic, added debug method
4. `README.md` - Added troubleshooting section

### Files Added
1. `DEBUG_SELECTORS.md` - Selector debugging guide
2. `browser_console_helper.js` - Browser console helper script
3. `CHANGELOG.md` - This file
4. `verify_imports.py` - Import verification script

### Known Issues
- Zalo Web structure may change, requiring selector updates
- Large groups (1000+ members) may take 10-30 minutes to scrape
- Some member names may be duplicated if they appear in multiple UI elements

### Migration Guide

If you're updating from version 1.0.0:

1. **Update dependencies:**
   ```bash
   pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
   pip install -r requirements.txt
   ```

2. **No code changes needed** - all fixes are backward compatible

3. **If scraping fails:**
   - Check the debug output in the application
   - Use `browser_console_helper.js` to find correct selectors
   - See `DEBUG_SELECTORS.md` for detailed instructions

### Testing
- ✅ Tested on Windows 11 with Python 3.11
- ✅ Verified PyQt6 import works correctly
- ✅ Confirmed absolute imports resolve correctly
- ⏳ Zalo Web scraping needs real-world testing with actual groups

---

## [1.0.0] - Initial Release

### Features
- User-friendly GUI with PyQt6
- Excel file support (.xlsx and .xls)
- Web automation using Playwright
- Smart matching with exact and fuzzy comparison
- Excel output with detailed results
- Real-time progress tracking
- Manual login support for Zalo Web
