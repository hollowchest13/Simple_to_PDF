import logging
import platform
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger():
    # Defining the path to the logs folder (universally via pathlib). On Linux it will be /home/user/..., on Windows C:\Users...
    log_dir = Path.home() / ".simple_to_pdf" / "logs"

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # If there are no permissions to create a folder in home, creating it next to the code
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "app.log"

    # Configuring the Root logger (Parent channel)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clearing old handlers (important for GUI to avoid duplicate logs)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Format (adding %(name)s to see the file name from __name__)
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Creating a file handler (universal)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",  # Important for Windows, doesn't interfere with Linux
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    root_logger.info(f"Logging initialized. OS: {platform.system()}. File: {log_file}")
