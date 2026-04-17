"""Verify all module imports work correctly"""
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("Testing all imports from src directory...")
print("=" * 50)

try:
    print("\n1. Testing PyQt6 imports...")
    from PyQt6.QtWidgets import QApplication
    print("   ✓ PyQt6.QtWidgets")
    
    print("\n2. Testing excel module imports...")
    from excel.reader import ExcelReader
    print("   ✓ excel.reader.ExcelReader")
    from excel.writer import ExcelWriter
    print("   ✓ excel.writer.ExcelWriter")
    
    print("\n3. Testing scraper module imports...")
    from scraper.browser_manager import BrowserManager
    print("   ✓ scraper.browser_manager.BrowserManager")
    from scraper.zalo_scraper import ZaloScraper
    print("   ✓ scraper.zalo_scraper.ZaloScraper")
    
    print("\n4. Testing core module imports...")
    from core.comparator import Comparator
    print("   ✓ core.comparator.Comparator")
    
    print("\n5. Testing ui module imports...")
    from ui.main_window import MainWindow
    print("   ✓ ui.main_window.MainWindow")
    
    print("\n" + "=" * 50)
    print("✅ ALL IMPORTS SUCCESSFUL!")
    print("\nYou can now run the application:")
    print("  python src/main.py")
    
except ImportError as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
