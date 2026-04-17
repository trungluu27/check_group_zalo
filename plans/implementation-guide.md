# Implementation Guide - Zalo Group Membership Checker

## Quick Start Guide

### Prerequisites
- macOS 11.0 or higher
- Python 3.9 or higher
- pip package manager

### Installation Steps

```bash
# 1. Create project directory
mkdir check_group_zalo
cd check_group_zalo

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Run the application
python src/main.py
```

## Code Examples

### 1. Excel Reader Module

**File**: [`src/excel/reader.py`](src/excel/reader.py)

```python
import pandas as pd
from typing import List, Optional
from pathlib import Path

class ExcelReader:
    def __init__(self, file_path: str, column_name: str = "username"):
        self.file_path = Path(file_path)
        self.column_name = column_name
        
    def read_file(self) -> pd.DataFrame:
        """Read Excel file and return DataFrame"""
        try:
            if self.file_path.suffix == '.xlsx':
                return pd.read_excel(self.file_path, engine='openpyxl')
            elif self.file_path.suffix == '.xls':
                return pd.read_excel(self.file_path, engine='xlrd')
            else:
                raise ValueError(f"Unsupported file format: {self.file_path.suffix}")
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")
    
    def get_usernames(self) -> List[str]:
        """Extract and clean usernames from Excel"""
        df = self.read_file()
        
        # Try to find username column
        if self.column_name not in df.columns:
            # Auto-detect column with username-like header
            potential_cols = [col for col in df.columns 
                            if 'user' in col.lower() or 'name' in col.lower()]
            if potential_cols:
                self.column_name = potential_cols[0]
            else:
                raise ValueError(f"Column '{self.column_name}' not found in Excel file")
        
        # Extract and clean usernames
        usernames = df[self.column_name].dropna().astype(str).tolist()
        # Remove whitespace and empty strings
        usernames = [name.strip() for name in usernames if name.strip()]
        
        return usernames
```

### 2. Excel Writer Module

**File**: [`src/excel/writer.py`](src/excel/writer.py)

```python
import pandas as pd
from pathlib import Path
from typing import List
from datetime import datetime

class ExcelWriter:
    def __init__(self, output_path: str, format: str = 'xlsx'):
        self.output_path = Path(output_path)
        self.format = format
        
    def write_results(self, missing_users: List[str], metadata: dict = None):
        """Write missing users to Excel/CSV file"""
        # Create DataFrame
        df = pd.DataFrame({
            'Missing Usernames': missing_users,
            'Status': ['Not in group'] * len(missing_users)
        })
        
        # Add metadata sheet if provided
        if metadata:
            metadata_df = pd.DataFrame([metadata])
        
        try:
            if self.format == 'xlsx':
                with pd.ExcelWriter(self.output_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Missing Members', index=False)
                    if metadata:
                        metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            elif self.format == 'csv':
                df.to_csv(self.output_path, index=False)
            else:
                raise ValueError(f"Unsupported format: {self.format}")
                
            return True
        except Exception as e:
            raise Exception(f"Error writing output file: {str(e)}")
```

### 3. Browser Manager Module

**File**: [`src/scraper/browser_manager.py`](src/scraper/browser_manager.py)

```python
from playwright.sync_api import sync_playwright, Browser, Page, Playwright
from typing import Optional
import time

class BrowserManager:
    def __init__(self, headless: bool = False, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    def launch(self) -> Page:
        """Launch browser and return page instance"""
        self.playwright = sync_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
        
        # Create context with realistic viewport
        context = self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        self.page = context.new_page()
        self.page.set_default_timeout(self.timeout)
        
        return self.page
    
    def navigate(self, url: str):
        """Navigate to URL"""
        if not self.page:
            raise Exception("Browser not initialized. Call launch() first.")
        self.page.goto(url)
        
    def wait_for_element(self, selector: str, timeout: int = None):
        """Wait for element to appear"""
        timeout = timeout or self.timeout
        self.page.wait_for_selector(selector, timeout=timeout)
        
    def scroll_to_bottom(self, pause_time: float = 2.0):
        """Scroll to bottom of page"""
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(pause_time)
        
    def close(self):
        """Close browser and cleanup"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
```

### 4. Zalo Scraper Module

**File**: [`src/scraper/zalo_scraper.py`](src/scraper/zalo_scraper.py)

```python
from .browser_manager import BrowserManager
from typing import List, Set
import time
import re

class ZaloScraper:
    def __init__(self, group_url: str, headless: bool = False):
        self.group_url = group_url
        self.browser_manager = BrowserManager(headless=headless)
        self.page = None
        
    def initialize(self):
        """Initialize browser"""
        self.page = self.browser_manager.launch()
        
    def wait_for_login(self, timeout: int = 300) -> bool:
        """Wait for user to manually login"""
        # Navigate to Zalo Web
        self.page.goto("https://chat.zalo.me/")
        
        print("Please login to Zalo Web...")
        print("Waiting for login to complete...")
        
        # Wait for main chat interface to appear (indicator of successful login)
        try:
            self.page.wait_for_selector('[data-id="div_Main"]', timeout=timeout * 1000)
            print("Login successful!")
            return True
        except:
            print("Login timeout!")
            return False
    
    def navigate_to_group(self):
        """Navigate to group page"""
        if not self.page:
            raise Exception("Browser not initialized")
            
        # Navigate to group URL
        self.page.goto(self.group_url)
        time.sleep(3)
        
        # Click on group info/members section
        # Note: Selectors may need adjustment based on actual Zalo Web structure
        try:
            self.page.click('[data-id="btn_GroupInfo"]')
            time.sleep(2)
        except:
            pass  # May already be on members page
    
    def scrape_members(self, max_scrolls: int = 50) -> Set[str]:
        """Scrape all group members with scroll automation"""
        members = set()
        previous_count = 0
        scroll_attempts = 0
        
        print("Starting to scrape group members...")
        
        while scroll_attempts < max_scrolls:
            # Extract visible members
            # Note: Adjust selector based on actual Zalo Web structure
            member_elements = self.page.query_selector_all('[data-id="member-item"]')
            
            for element in member_elements:
                try:
                    # Extract member name/username
                    name = element.inner_text().strip()
                    if name:
                        members.add(name)
                except:
                    continue
            
            # Check if new members were found
            current_count = len(members)
            if current_count == previous_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0  # Reset if new members found
            
            previous_count = current_count
            
            # Scroll down
            self.browser_manager.scroll_to_bottom(pause_time=2.0)
            
            print(f"Found {current_count} members so far...")
            
            # Stop if no new members after several scrolls
            if scroll_attempts >= 3:
                break
        
        print(f"Scraping complete! Total members: {len(members)}")
        return members
    
    def close(self):
        """Close browser"""
        self.browser_manager.close()
```

### 5. Comparator Module

**File**: [`src/core/comparator.py`](src/core/comparator.py)

```python
from typing import List, Set, Tuple
from fuzzywuzzy import fuzz
import re

class Comparator:
    def __init__(self, threshold: float = 0.85, case_sensitive: bool = False):
        self.threshold = threshold * 100  # fuzzywuzzy uses 0-100 scale
        self.case_sensitive = case_sensitive
        
    def normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        if not self.case_sensitive:
            name = name.lower()
            
        return name
    
    def exact_match(self, excel_names: List[str], group_members: Set[str]) -> Tuple[List[str], List[str]]:
        """Find exact matches and missing members"""
        # Normalize names
        excel_normalized = {self.normalize_name(name): name for name in excel_names}
        group_normalized = {self.normalize_name(name) for name in group_members}
        
        # Find matches
        found = []
        missing = []
        
        for normalized, original in excel_normalized.items():
            if normalized in group_normalized:
                found.append(original)
            else:
                missing.append(original)
        
        return found, missing
    
    def fuzzy_match(self, excel_names: List[str], group_members: Set[str]) -> Tuple[List[str], List[str]]:
        """Find fuzzy matches and missing members"""
        found = []
        missing = []
        
        for excel_name in excel_names:
            normalized_excel = self.normalize_name(excel_name)
            best_match_score = 0
            
            for group_name in group_members:
                normalized_group = self.normalize_name(group_name)
                
                # Try different fuzzy matching strategies
                ratio = fuzz.ratio(normalized_excel, normalized_group)
                partial = fuzz.partial_ratio(normalized_excel, normalized_group)
                token_sort = fuzz.token_sort_ratio(normalized_excel, normalized_group)
                
                # Take the best score
                score = max(ratio, partial, token_sort)
                best_match_score = max(best_match_score, score)
            
            if best_match_score >= self.threshold:
                found.append(excel_name)
            else:
                missing.append(excel_name)
        
        return found, missing
    
    def compare(self, excel_names: List[str], group_members: Set[str], 
                use_fuzzy: bool = True) -> dict:
        """Compare Excel names with group members"""
        if use_fuzzy:
            found, missing = self.fuzzy_match(excel_names, group_members)
        else:
            found, missing = self.exact_match(excel_names, group_members)
        
        return {
            'total_excel': len(excel_names),
            'total_group': len(group_members),
            'found': found,
            'missing': missing,
            'found_count': len(found),
            'missing_count': len(missing)
        }
```

### 6. Main Window UI

**File**: [`src/ui/main_window.py`](src/ui/main_window.py)

```python
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QTextEdit, QLabel,
                             QProgressBar, QFileDialog, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal
import sys

class WorkerThread(QThread):
    """Worker thread for background processing"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, excel_path, group_url):
        super().__init__()
        self.excel_path = excel_path
        self.group_url = group_url
        
    def run(self):
        """Execute scraping and comparison"""
        try:
            from ..excel.reader import ExcelReader
            from ..excel.writer import ExcelWriter
            from ..scraper.zalo_scraper import ZaloScraper
            from ..core.comparator import Comparator
            
            # Read Excel
            self.progress.emit("Reading Excel file...")
            reader = ExcelReader(self.excel_path)
            excel_names = reader.get_usernames()
            self.progress.emit(f"Found {len(excel_names)} usernames in Excel")
            
            # Initialize scraper
            self.progress.emit("Initializing browser...")
            scraper = ZaloScraper(self.group_url, headless=False)
            scraper.initialize()
            
            # Login
            self.progress.emit("Waiting for login...")
            if not scraper.wait_for_login():
                raise Exception("Login failed or timeout")
            
            # Navigate and scrape
            self.progress.emit("Navigating to group...")
            scraper.navigate_to_group()
            
            self.progress.emit("Scraping group members...")
            group_members = scraper.scrape_members()
            
            scraper.close()
            
            # Compare
            self.progress.emit("Comparing names...")
            comparator = Comparator()
            results = comparator.compare(excel_names, group_members, use_fuzzy=True)
            
            # Save results
            self.progress.emit("Saving results...")
            writer = ExcelWriter("output/missing_members.xlsx")
            writer.write_results(results['missing'])
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.excel_path = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("Zalo Group Membership Checker")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Excel file selection
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        file_btn = QPushButton("Select Excel File")
        file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(file_btn)
        layout.addLayout(file_layout)
        
        # Group URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Zalo Group Link:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://chat.zalo.me/g/...")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Start button
        self.start_btn = QPushButton("Start Checking")
        self.start_btn.clicked.connect(self.start_process)
        layout.addWidget(self.start_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status/Results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        layout.addWidget(self.results_display)
        
    def select_file(self):
        """Open file dialog to select Excel file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.excel_path = file_path
            self.file_label.setText(file_path.split('/')[-1])
            
    def start_process(self):
        """Start the checking process"""
        if not self.excel_path:
            QMessageBox.warning(self, "Error", "Please select an Excel file")
            return
            
        if not self.url_input.text():
            QMessageBox.warning(self, "Error", "Please enter Zalo group link")
            return
        
        self.start_btn.setEnabled(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.results_display.clear()
        
        # Start worker thread
        self.worker = WorkerThread(self.excel_path, self.url_input.text())
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def update_status(self, message):
        """Update status display"""
        self.results_display.append(message)
        
    def on_finished(self, results):
        """Handle completion"""
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.start_btn.setEnabled(True)
        
        # Display results
        self.results_display.append("\n=== RESULTS ===")
        self.results_display.append(f"Total usernames in Excel: {results['total_excel']}")
        self.results_display.append(f"Total members in group: {results['total_group']}")
        self.results_display.append(f"Found in group: {results['found_count']}")
        self.results_display.append(f"NOT in group: {results['missing_count']}")
        self.results_display.append(f"\nMissing members: {', '.join(results['missing'])}")
        self.results_display.append("\nResults saved to: output/missing_members.xlsx")
        
        QMessageBox.information(self, "Complete", 
                               f"Process complete! Found {results['missing_count']} missing members.")
        
    def on_error(self, error_msg):
        """Handle errors"""
        self.progress_bar.setRange(0, 1)
        self.start_btn.setEnabled(True)
        self.results_display.append(f"\nERROR: {error_msg}")
        QMessageBox.critical(self, "Error", error_msg)
```

### 7. Main Entry Point

**File**: [`src/main.py`](src/main.py)

```python
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Create and run application
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
```

## Next Steps

Once you approve this plan, we can proceed to implementation by:

1. Setting up the project structure
2. Creating all necessary files
3. Implementing each module step by step
4. Testing with sample data
5. Creating documentation and packaging

The implementation is ready to begin whenever you're ready to proceed.
