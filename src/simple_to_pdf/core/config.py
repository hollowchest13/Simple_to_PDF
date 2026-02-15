import sys
from pathlib import Path
from datetime import datetime
from enum import Enum

# --- PATHS CONFIGURATION ---
# Determine the base directory whether running as a script or a frozen executable.
if getattr(sys, "frozen", False):
    # If the application is bundled by PyInstaller
    BASE_PATH = Path(sys.executable).parent
else:
    # If running as a script: config.py -> simple_to_pdf/ -> src/ -> ROOT/
    # Adjust the number of .parent calls based on your actual file depth
    BASE_PATH = Path(__file__).resolve().parent.parent.parent.parent

# Path to the pyproject.toml file for version tracking
CONFIG_PATH = BASE_PATH / "pyproject.toml"
LICENCE_PATH = BASE_PATH/"LICENSE"

# --- GITHUB CONFIGURATION ---
GITHUB_USER = "hollowchest13"
GITHUB_REPO = "Simple_to_PDF"

# Dynamically construct URLs for easier maintenance
GITHUB_REPO_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"
README_URL = f"{GITHUB_REPO_URL}#readme"
RELEASES_URL = f"{GITHUB_REPO_URL}/releases"
ISSUES_URL = f"{GITHUB_REPO_URL}/issues"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

# --- APPLICATION METADATA ---
APP_NAME = "Simple to PDF"
CURRENT_YEAR = datetime.now().year

class ThemeKeys(Enum):
    BG_COLOR = "bg_color"
    ACCENT = "accent"
    TEXT_MAIN = "text_main"
    BORDER = "border"

DEFAULT_COLORS = {
    ThemeKeys.BG_COLOR: "#ffffff",    
    ThemeKeys.ACCENT: "#3498db",      
    ThemeKeys.TEXT_MAIN: "#2c3e50",   
    ThemeKeys.BORDER: "#e2e8f0"
}