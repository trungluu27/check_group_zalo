"""
Test script to verify Zalo scraper implementation
This script helps verify the selector updates are correct
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all imports work"""
    print("=" * 60)
    print("Testing imports...")
    print("=" * 60)
    
    try:
        from scraper.zalo_scraper import ZaloScraper
        print("✓ ZaloScraper imported successfully")
    except Exception as e:
        print(f"✗ Failed to import ZaloScraper: {e}")
        return False
    
    try:
        from excel.reader import ExcelReader
        print("✓ ExcelReader imported successfully")
    except Exception as e:
        print(f"✗ Failed to import ExcelReader: {e}")
        return False
    
    try:
        from excel.writer import ExcelWriter
        print("✓ ExcelWriter imported successfully")
    except Exception as e:
        print(f"✗ Failed to import ExcelWriter: {e}")
        return False
    
    try:
        from core.comparator import Comparator
        print("✓ Comparator imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Comparator: {e}")
        return False
    
    try:
        from ui.main_window import MainWindow
        print("✓ MainWindow imported successfully")
    except Exception as e:
        print(f"✗ Failed to import MainWindow: {e}")
        return False
    
    return True

def test_selectors():
    """Verify selectors are in the code"""
    print("\n" + "=" * 60)
    print("Verifying Zalo Web selectors...")
    print("=" * 60)
    
    zalo_scraper_path = Path(__file__).parent / "src" / "scraper" / "zalo_scraper.py"
    
    if not zalo_scraper_path.exists():
        print("✗ zalo_scraper.py not found")
        return False
    
    content = zalo_scraper_path.read_text(encoding='utf-8')
    
    selectors_to_check = [
        ("Info button", "main header>div:nth-child(2)>div[icon]"),
        ("Members button", "aside div[id='sideBodyScrollBox']"),
        ("Member names", "div[id='member-group'] div[class='chat-box-member__info__name v2']>div"),
        ("Member group container", "div[id='member-group']"),
    ]
    
    all_found = True
    for name, selector in selectors_to_check:
        if selector in content:
            print(f"✓ {name}: {selector[:50]}...")
        else:
            print(f"✗ {name}: NOT FOUND")
            all_found = False
    
    # Check for &nbsp; handling
    if '&nbsp;' in content or 'inner_html' in content:
        print("✓ &nbsp; handling implemented")
    else:
        print("⚠ Warning: &nbsp; handling might be missing")
    
    return all_found

def test_debug_method():
    """Check if debug method exists"""
    print("\n" + "=" * 60)
    print("Checking debug capabilities...")
    print("=" * 60)
    
    zalo_scraper_path = Path(__file__).parent / "src" / "scraper" / "zalo_scraper.py"
    content = zalo_scraper_path.read_text(encoding='utf-8')
    
    if 'debug_page_structure' in content:
        print("✓ debug_page_structure method found")
    else:
        print("✗ debug_page_structure method not found")
        return False
    
    return True

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "ZALO SCRAPER VERIFICATION TEST" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Selectors
    results.append(("Selectors", test_selectors()))
    
    # Test 3: Debug method
    results.append(("Debug Method", test_debug_method()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20} : {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ All tests passed!")
        print("\nYou can now run the application:")
        print("  python src/main.py")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print("1. Run: python src/main.py")
    print("2. Select an Excel file with usernames")
    print("3. Enter Zalo group URL: https://chat.zalo.me/?g=...")
    print("4. Click 'Start Checking'")
    print("5. Login to Zalo Web when browser opens")
    print("6. Wait for scraping to complete")
    print("\nFor troubleshooting, see:")
    print("  - README.md (Troubleshooting section)")
    print("  - ZALO_SELECTORS.md (Selector documentation)")
    print("  - DEBUG_SELECTORS.md (Debug guide)")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
