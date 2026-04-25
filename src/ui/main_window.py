from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QTextEdit, QLabel,
                             QProgressBar, QFileDialog, QMessageBox, QCheckBox,
                             QGroupBox, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QDesktopServices
import sys
from pathlib import Path


class WorkerThread(QThread):
    """Worker thread for background processing to keep UI responsive"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, excel_path: str, use_fuzzy: bool, threshold: float, max_groups: int = 0):
        """
        Initialize worker thread
        
        Args:
            excel_path: Path to Excel file
            use_fuzzy: Use fuzzy matching
            threshold: Fuzzy matching threshold
            max_groups: Number of first groups to process (0 = all)
        """
        super().__init__()
        self.excel_path = excel_path
        self.use_fuzzy = use_fuzzy
        self.threshold = threshold
        self.max_groups = max_groups
        
    def run(self):
        """Execute scraping and comparison in background"""
        scraper = None
        try:
            from excel.reader import ExcelReader
            from excel.writer import ExcelWriter
            from scraper.zalo_scraper import ZaloScraper
            from core.comparator import Comparator
            
            # Read grouped Excel and run all groups in sequence
            self.progress.emit("📁 Reading Excel file...")
            reader = ExcelReader(self.excel_path)
            group_batches = reader.get_group_batches()
            if not group_batches:
                raise Exception(
                    "Không tìm thấy dữ liệu group trong file. "
                    "File cần có cột Group xe chứa link https://zalo.me/g/..."
                )

            total_groups_in_file = len(group_batches)
            if self.max_groups > 0:
                group_batches = group_batches[:self.max_groups]
                self.progress.emit(
                    f"✅ Detected {total_groups_in_file} groups, "
                    f"processing first {len(group_batches)} groups"
                )
            else:
                self.progress.emit(f"✅ Detected {total_groups_in_file} groups in input file")

            # Initialize browser once for whole batch
            first_group_url = group_batches[0]["group_url"]
            self.progress.emit("🌐 Initializing browser for batch checking...")
            scraper = ZaloScraper(first_group_url, headless=False)
            scraper.initialize()

            self.progress.emit("🔐 Checking saved login session / waiting for manual login...")
            if not scraper.wait_for_login(timeout=300, progress_callback=self.progress.emit):
                raise Exception("Login failed or timeout. Please try again.")

            comparator = Comparator(threshold=self.threshold)
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            batch_dir = output_dir / f"batch_{Path(self.excel_path).stem}"
            batch_dir.mkdir(parents=True, exist_ok=True)

            per_group_results = []
            total_excel = 0
            total_found = 0
            total_missing = 0
            total_extra = 0

            for idx, batch in enumerate(group_batches, start=1):
                group_id = batch["group_id"]
                group_url = batch["group_url"]
                group_label = batch.get("group_label", group_id)
                contacts = batch["contacts"]
                excel_names = [c['name'] for c in contacts]

                self.progress.emit("")
                self.progress.emit(f"🚍 [{idx}/{len(group_batches)}] Group: {group_label} ({group_id})")
                self.progress.emit(f"📋 Excel names in this group: {len(excel_names)}")

                scraper.group_url = group_url
                scraper.navigate_to_group(progress_callback=self.progress.emit)
                self.progress.emit("👥 Scraping group members (deep scan mode)...")
                group_members = scraper.scrape_members(max_scrolls=160, progress_callback=self.progress.emit)
                if len(group_members) == 0:
                    raise Exception(f"Không lấy được thành viên group {group_id}.")

                self.progress.emit(f"🔍 Comparing names using {'fuzzy' if self.use_fuzzy else 'exact'} matching...")
                results = comparator.compare(excel_names, group_members, use_fuzzy=self.use_fuzzy)

                safe_group_id = "".join(ch if (ch.isalnum() or ch in ['_', '-']) else '_' for ch in group_id) or f"group_{idx}"
                output_file = batch_dir / f"missing_members_{safe_group_id}.xlsx"

                metadata = {
                    'Group Label': group_label,
                    'Group ID': group_id,
                    'Group URL': group_url,
                    'Excel File': self.excel_path,
                    'Total in Excel': results['total_excel'],
                    'Found in Group': results['found_count'],
                    'Missing from Group': results['missing_count'],
                    'Matching Method': results['method'].upper(),
                    'Threshold': f"{results['threshold']*100:.0f}%" if results['method'] == 'fuzzy' else 'N/A'
                }

                missing_records = []
                missing_name_set = set(results['missing'])
                for c in contacts:
                    if c['name'] in missing_name_set:
                        missing_records.append({'phone': c.get('phone', ''), 'name': c['name']})

                extra_in_group_records = [{'name': name} for name in results.get('extra_in_group', [])]

                writer = ExcelWriter(str(output_file))
                writer.write_results(missing_records, metadata, extra_in_group_records)

                per_group_results.append({
                    "group_id": group_id,
                    "group_label": group_label,
                    "output_path": str(output_file),
                    "total_excel": results["total_excel"],
                    "found_count": results["found_count"],
                    "missing_count": results["missing_count"],
                    "extra_in_group_count": results.get("extra_in_group_count", 0),
                })
                total_excel += results["total_excel"]
                total_found += results["found_count"]
                total_missing += results["missing_count"]
                total_extra += results.get("extra_in_group_count", 0)
                self.progress.emit(f"💾 Saved: {output_file.name}")

            self.finished.emit({
                "mode": "batch",
                "groups_count": len(group_batches),
                "groups_total_in_file": total_groups_in_file,
                "method": 'fuzzy' if self.use_fuzzy else 'exact',
                "threshold": self.threshold,
                "total_excel": total_excel,
                "found_count": total_found,
                "missing_count": total_missing,
                "extra_in_group_count": total_extra,
                "per_group": per_group_results,
                "output_path": str(batch_dir),
            })
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if scraper is not None:
                try:
                    scraper.close()
                except Exception:
                    pass


class MainWindow(QMainWindow):
    """Modern macOS-style main window for Zalo Group Checker"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.last_output_path = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the modern UI"""
        self.setWindowTitle("Zalo Group Checker")
        self.setMinimumSize(750, 600)
        self.resize(850, 750)
        
        # Apply modern macOS-style theme
        self.apply_modern_theme()
        
        # Central widget with padding
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with margins - optimized for smaller screens
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Header
        header = self.create_header()
        main_layout.addWidget(header)
        
        # File input section
        file_section = self.create_file_section()
        main_layout.addWidget(file_section)
        
        # Group URL section
        url_section = self.create_url_section()
        main_layout.addWidget(url_section)
        
        # Settings section
        settings_section = self.create_settings_section()
        main_layout.addWidget(settings_section)
        
        # Action buttons
        button_section = self.create_button_section()
        main_layout.addWidget(button_section)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #E5E5E5;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #007AFF, stop:1 #5AC8FA);
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Results display - more compact
        results_label = QLabel("Results")
        results_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #1D1D1F;")
        main_layout.addWidget(results_label)
        
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setMinimumHeight(150)
        self.results_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 10px;
                background-color: #FAFAFA;
                font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
                font-size: 12px;
                line-height: 1.4;
                color: #1D1D1F;
            }
        """)
        main_layout.addWidget(self.results_display, stretch=1)
        
        # Initial message
        self.results_display.append("👋 Welcome to Zalo Group Checker!")
        self.results_display.append("\n📝 Instructions:")
        self.results_display.append("1. Select your grouped Excel file")
        self.results_display.append("2. App will auto-detect all Zalo groups in file")
        self.results_display.append("3. Configure matching settings (optional)")
        self.results_display.append("4. Click 'Start Checking' to run all groups in order")
        self.results_display.append("\n⚡ Ready to start!")
        
    def apply_modern_theme(self):
        """Apply modern macOS-style theme to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QLabel {
                color: #1D1D1F;
                font-size: 13px;
            }
            QLineEdit {
                border: 1px solid #D1D1D6;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #FFFFFF;
                font-size: 13px;
                color: #1D1D1F;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
                padding: 7px 11px;
            }
            QLineEdit:disabled {
                background-color: #F5F5F7;
                color: #86868B;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton:pressed {
                opacity: 0.8;
            }
            QPushButton:disabled {
                background-color: #F5F5F7;
                color: #C7C7CC;
            }
            QGroupBox {
                border: 1px solid #E5E5E5;
                border-radius: 8px;
                margin-top: 10px;
                padding: 12px;
                background-color: #FAFAFA;
                font-weight: 600;
                font-size: 13px;
                color: #1D1D1F;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #1D1D1F;
            }
            QCheckBox {
                spacing: 8px;
                color: #1D1D1F;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #D1D1D6;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #007AFF;
                border-color: #007AFF;
                image: url(none);
            }
            QCheckBox::indicator:checked:after {
                content: "✓";
                color: white;
            }
        """)
        
    def create_header(self):
        """Create modern header section"""
        header = QLabel("Zalo Group Member Checker")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #1D1D1F;
            padding: 8px 0px;
            letter-spacing: -0.3px;
        """)
        return header
        
    def create_file_section(self):
        """Create file selection section"""
        group = QGroupBox("📁 Excel File")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # File path display
        path_layout = QHBoxLayout()
        path_layout.setSpacing(8)
        
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select an Excel file containing usernames...")
        self.file_path.setReadOnly(True)
        path_layout.addWidget(self.file_path, stretch=1)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #0051D5;
            }
        """)
        self.browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(self.browse_btn)
        
        layout.addLayout(path_layout)
        
        # Help text - more compact
        help_text = QLabel("💡 Excel phải có 2 cột: SĐT (SĐT/SDT/SĐT Zalo) và Tên (Tên/Tên Zalo), không phân biệt hoa thường")
        help_text.setStyleSheet("color: #86868B; font-size: 11px; padding-left: 2px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        group.setLayout(layout)
        return group
        
    def create_url_section(self):
        """Create Group ID input section"""
        group = QGroupBox("🌐 Group Detection Mode")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        self.group_id = QLineEdit()
        self.group_id.setPlaceholderText("Auto mode: detect groups from Excel (no manual input needed)")
        self.group_id.setEnabled(False)
        layout.addWidget(self.group_id)
        
        # Help text - more compact
        help_text = QLabel("💡 App sẽ tự đọc các link https://zalo.me/g/... trong cột Group xe và chạy lần lượt")
        help_text.setStyleSheet("color: #86868B; font-size: 11px; padding-left: 2px;")
        layout.addWidget(help_text)
        
        group.setLayout(layout)
        return group
        
    def create_settings_section(self):
        """Create settings section with modern styling"""
        group = QGroupBox("⚙️ Matching Settings")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Fuzzy matching checkbox
        self.fuzzy_check = QCheckBox("Use fuzzy matching (recommended for similar names)")
        self.fuzzy_check.setChecked(True)
        self.fuzzy_check.stateChanged.connect(self.toggle_threshold)
        layout.addWidget(self.fuzzy_check)
        
        # Threshold setting - more compact layout
        threshold_layout = QHBoxLayout()
        threshold_layout.setSpacing(8)
        
        threshold_label = QLabel("Similarity:")
        threshold_label.setFixedWidth(130)
        threshold_label.setStyleSheet("font-size: 12px; color: #1D1D1F;")
        threshold_layout.addWidget(threshold_label)
        
        self.threshold_input = QLineEdit()
        self.threshold_input.setText("0.85")
        self.threshold_input.setPlaceholderText("0.85")
        self.threshold_input.setFixedWidth(110)
        self.threshold_input.setFixedHeight(34)
        self.threshold_input.setToolTip("Nhập ngưỡng từ 0.5 đến 1.0")
        threshold_layout.addWidget(self.threshold_input)

        threshold_hint = QLabel("(0.5 - 1.0)")
        threshold_hint.setStyleSheet("font-size: 11px; color: #86868B;")
        threshold_layout.addWidget(threshold_hint)
        
        threshold_layout.addStretch()
        
        layout.addLayout(threshold_layout)

        # Batch limit setting
        batch_layout = QHBoxLayout()
        batch_layout.setSpacing(8)

        batch_label = QLabel("Groups to check:")
        batch_label.setFixedWidth(130)
        batch_label.setStyleSheet("font-size: 12px; color: #1D1D1F;")
        batch_layout.addWidget(batch_label)

        self.max_groups_input = QLineEdit()
        self.max_groups_input.setText("0")
        self.max_groups_input.setPlaceholderText("0")
        self.max_groups_input.setFixedWidth(110)
        self.max_groups_input.setFixedHeight(34)
        self.max_groups_input.setToolTip("0 = chạy toàn bộ group trong file")
        batch_layout.addWidget(self.max_groups_input)

        batch_hint = QLabel("(0 = All)")
        batch_hint.setStyleSheet("font-size: 11px; color: #86868B;")
        batch_layout.addWidget(batch_hint)

        batch_layout.addStretch()
        layout.addLayout(batch_layout)
        
        # Help text - more compact
        help_text = QLabel("💡 Higher = stricter matching (0.85 = 85% similar). Groups to check: 0 = All, 1/2/... = test nhanh nhóm đầu.")
        help_text.setStyleSheet("color: #86868B; font-size: 11px; padding-left: 2px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        
        group.setLayout(layout)
        return group
        
    def create_button_section(self):
        """Create action buttons section"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(10)
        
        # Clear session button - more compact
        self.clear_btn = QPushButton("🔄 Clear Session")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                color: #1D1D1F;
                min-width: 110px;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_session)
        layout.addWidget(self.clear_btn)
        
        # Output actions
        self.open_output_btn = QPushButton("📄 Open Output")
        self.open_output_btn.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F7;
                color: #1D1D1F;
                min-width: 110px;
                font-size: 12px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
            }
        """)
        self.open_output_btn.setEnabled(False)
        self.open_output_btn.clicked.connect(self.open_output_file)
        layout.addWidget(self.open_output_btn)

        layout.addStretch()
        
        # Start button - more compact
        self.start_btn = QPushButton("▶ Start Checking")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #34C759;
                color: white;
                min-width: 130px;
                font-size: 13px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #30B051;
            }
            QPushButton:disabled {
                background-color: #F5F5F7;
                color: #C7C7CC;
            }
        """)
        self.start_btn.clicked.connect(self.start_checking)
        layout.addWidget(self.start_btn)
        
        return widget
        
    def toggle_threshold(self, state):
        """Enable/disable threshold control based on fuzzy matching"""
        self.threshold_input.setEnabled(state == Qt.CheckState.Checked.value)
        
    def browse_file(self):
        """Open file browser to select Excel file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.file_path.setText(file_path)
            self.results_display.append(f"\n✅ Selected file: {Path(file_path).name}")
            
    def start_checking(self):
        """Start the checking process"""
        # Validate inputs
        excel_path = self.file_path.text()
        
        if not excel_path:
            QMessageBox.warning(self, "Missing Input", "Please select an Excel file.")
            return
            
        if not Path(excel_path).exists():
            QMessageBox.critical(self, "File Not Found", "The selected Excel file does not exist.")
            return
            
        # Disable controls
        self.start_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.group_id.setEnabled(False)
        self.fuzzy_check.setEnabled(False)
        self.threshold_input.setEnabled(False)
        self.max_groups_input.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # Reset output actions for new run
        self.last_output_path = None
        self.open_output_btn.setEnabled(False)

        # Clear previous results
        self.results_display.clear()
        self.results_display.append("🚀 Starting Zalo Group Checker...\n")
        
        # Setup progress bar
        self.progress_bar.setMaximum(0)  # Indeterminate progress
        
        # Create and start worker thread
        use_fuzzy = self.fuzzy_check.isChecked()
        threshold_text = self.threshold_input.text().strip()
        try:
            threshold = float(threshold_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Threshold", "Similarity phải là số từ 0.5 đến 1.0 (ví dụ 0.85).")
            self.start_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.fuzzy_check.setEnabled(True)
            self.threshold_input.setEnabled(self.fuzzy_check.isChecked())
            self.max_groups_input.setEnabled(True)
            self.clear_btn.setEnabled(True)
            return
        if threshold < 0.5 or threshold > 1.0:
            QMessageBox.warning(self, "Invalid Threshold", "Similarity phải nằm trong khoảng 0.5 đến 1.0.")
            self.start_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.fuzzy_check.setEnabled(True)
            self.threshold_input.setEnabled(self.fuzzy_check.isChecked())
            self.max_groups_input.setEnabled(True)
            self.clear_btn.setEnabled(True)
            return

        max_groups_text = self.max_groups_input.text().strip() or "0"
        try:
            max_groups = int(max_groups_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Groups Value", "Groups to check phải là số nguyên >= 0.")
            self.start_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.fuzzy_check.setEnabled(True)
            self.threshold_input.setEnabled(self.fuzzy_check.isChecked())
            self.max_groups_input.setEnabled(True)
            self.clear_btn.setEnabled(True)
            return
        if max_groups < 0:
            QMessageBox.warning(self, "Invalid Groups Value", "Groups to check không được âm.")
            self.start_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)
            self.fuzzy_check.setEnabled(True)
            self.threshold_input.setEnabled(self.fuzzy_check.isChecked())
            self.max_groups_input.setEnabled(True)
            self.clear_btn.setEnabled(True)
            return

        self.worker = WorkerThread(excel_path, use_fuzzy, threshold, max_groups=max_groups)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def on_progress(self, message: str):
        """Update progress display"""
        self.results_display.append(message)
        
        # Auto-scroll to bottom
        scrollbar = self.results_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def on_finished(self, results: dict):
        """Handle completion with modern styling"""
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(1)
        
        # Re-enable controls
        self.start_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.group_id.setEnabled(False)
        self.fuzzy_check.setEnabled(True)
        self.threshold_input.setEnabled(self.fuzzy_check.isChecked())
        self.max_groups_input.setEnabled(True)
        self.clear_btn.setEnabled(True)

        # Enable output actions
        self.last_output_path = results.get('output_path')
        has_output = bool(self.last_output_path and Path(self.last_output_path).exists())
        self.open_output_btn.setEnabled(has_output)
        
        # Display results with modern formatting
        self.results_display.append("\n" + "─"*60)
        self.results_display.append("📊 FINAL RESULTS")
        self.results_display.append("─"*60)
        self.results_display.append(f"🧩 Total groups processed: {results.get('groups_count', 1)}")
        if results.get('groups_total_in_file', 0):
            self.results_display.append(f"🗂️ Total groups in file: {results['groups_total_in_file']}")
        self.results_display.append(f"📋 Total usernames in Excel: {results['total_excel']}")
        self.results_display.append(f"🔍 Matching method: {results['method'].upper()}")
        if results['method'] == 'fuzzy':
            self.results_display.append(f"📊 Matching threshold: {results['threshold']*100:.0f}%")
        self.results_display.append("")
        self.results_display.append(f"✅ Found in group: {results['found_count']}")
        self.results_display.append(f"❌ NOT in group: {results['missing_count']}")
        self.results_display.append(f"➕ In group but NOT in Excel list: {results.get('extra_in_group_count', 0)}")

        per_group = results.get("per_group", [])
        if per_group:
            self.results_display.append("\n🚌 Per-group summary:")
            for item in per_group:
                self.results_display.append(
                    f"  • {item.get('group_label', item['group_id'])}: "
                    f"missing {item['missing_count']} / {item['total_excel']} "
                    f"(output: {Path(item['output_path']).name})"
                )

        self.results_display.append(f"\n💾 Results saved to: {results['output_path']}")
        self.results_display.append("\n✅ Process completed successfully!")
        
        # Show modern completion dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("✅ Process Complete")
        msg_box.setText(
            f"Processed {results.get('groups_count', 1)} groups, "
            f"found {results['missing_count']} missing members"
        )
        msg_box.setInformativeText(f"Results saved to:\n{results['output_path']}")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def on_error(self, error_msg: str):
        """Handle errors with modern styling"""
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        
        # Re-enable controls
        self.start_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.group_id.setEnabled(False)
        self.fuzzy_check.setEnabled(True)
        self.threshold_input.setEnabled(self.fuzzy_check.isChecked())
        self.max_groups_input.setEnabled(True)
        self.clear_btn.setEnabled(True)

        # Keep output actions enabled only if last output exists
        has_output = bool(self.last_output_path and Path(self.last_output_path).exists())
        self.open_output_btn.setEnabled(has_output)
        
        self.results_display.append(f"\n❌ ERROR: {error_msg}")
        
        # Show modern error dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("❌ Error")
        msg_box.setText("An error occurred during processing")
        msg_box.setInformativeText(error_msg)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def open_output_file(self):
        """Open the last generated output file"""
        if not self.last_output_path:
            QMessageBox.information(self, "No Output", "No output file yet. Run checking first.")
            return

        output_file = Path(self.last_output_path)
        if not output_file.exists():
            QMessageBox.warning(self, "File Not Found", f"Output file not found:\n{output_file}")
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_file.resolve())))

    def clear_session(self):
        """Clear saved browser session with modern dialog"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("🔄 Clear Login Session")
        msg_box.setText("Delete saved Zalo login session?")
        msg_box.setInformativeText("You will need to login again the next time you run the checker.")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        reply = msg_box.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                from scraper.browser_manager import BrowserManager
                manager = BrowserManager()
                if manager.clear_session():
                    self.results_display.append("\n🔄 Login session cleared successfully!")
                    self.results_display.append("You will need to login again on next run.")
                    
                    success_box = QMessageBox(self)
                    success_box.setWindowTitle("✅ Session Cleared")
                    success_box.setText("Login session has been cleared")
                    success_box.setInformativeText("You will need to login again the next time.")
                    success_box.setIcon(QMessageBox.Icon.Information)
                    success_box.exec()
                else:
                    self.results_display.append("\n⚠ Session was already cleared or not found.")
            except Exception as e:
                self.results_display.append(f"\n❌ Error clearing session: {str(e)}")
                
                error_box = QMessageBox(self)
                error_box.setWindowTitle("⚠ Warning")
                error_box.setText("Could not clear session")
                error_box.setInformativeText(str(e))
                error_box.setIcon(QMessageBox.Icon.Warning)
                error_box.exec()
