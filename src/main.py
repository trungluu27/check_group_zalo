import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
import logging


def get_app_dir() -> Path:
    """
    Get the application's base directory.
    - When running as a PyInstaller frozen .exe/.app: use the directory
      containing the executable (not the temp _MEIPASS extraction folder).
    - When running from source: use the project root (parent of src/).
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller sets sys.executable to the path of the .exe/.app binary
        return Path(sys.executable).parent
    else:
        # Running from source: go up one level from src/
        return Path(__file__).parent.parent


def setup_logging(app_dir: Path):
    """Setup logging configuration with correct path for frozen apps"""
    log_dir = app_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file), encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def setup_directories(app_dir: Path):
    """Create necessary directories relative to executable location"""
    (app_dir / "output").mkdir(exist_ok=True)
    (app_dir / "logs").mkdir(exist_ok=True)


def main():
    """Main application entry point"""
    # Resolve base directory (works both frozen and from source)
    app_dir = get_app_dir()

    # When frozen, change working directory to app location so relative
    # paths in the rest of the code (e.g. output/, config.json) work correctly
    if getattr(sys, 'frozen', False):
        os.chdir(str(app_dir))

    # Setup logging first
    setup_logging(app_dir)
    logger = logging.getLogger(__name__)

    logger.info("Starting Zalo Group Membership Checker")
    logger.info(f"App directory: {app_dir}")
    logger.info(f"Frozen: {getattr(sys, 'frozen', False)}")

    # Create directories
    setup_directories(app_dir)

    # Create and run Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Zalo Group Membership Checker")

    window = MainWindow()
    window.show()

    logger.info("Application window displayed")

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
