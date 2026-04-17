"""Test script to verify all imports work correctly"""
import sys
print("Testing imports...")

try:
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6.QtWidgets import successful")
except ImportError as e:
    print(f"✗ PyQt6.QtWidgets import failed: {e}")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
    print("✓ playwright import successful")
except ImportError as e:
    print(f"✗ playwright import failed: {e}")
    sys.exit(1)

try:
    import pandas
    print("✓ pandas import successful")
except ImportError as e:
    print(f"✗ pandas import failed: {e}")
    sys.exit(1)

try:
    import openpyxl
    print("✓ openpyxl import successful")
except ImportError as e:
    print(f"✗ openpyxl import failed: {e}")
    sys.exit(1)

try:
    from fuzzywuzzy import fuzz
    print("✓ fuzzywuzzy import successful")
except ImportError as e:
    print(f"✗ fuzzywuzzy import failed: {e}")
    sys.exit(1)

try:
    from ui.main_window import MainWindow
    print("✓ ui.main_window import successful")
except ImportError as e:
    print(f"✗ ui.main_window import failed: {e}")
    sys.exit(1)

print("\n✓ All imports successful! The application should work correctly.")
print("You can now run: python src/main.py")
