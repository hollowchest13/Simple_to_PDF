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

from enum import Enum

class ThemeKeys(Enum):
    # Backgrounds / Surfaces
    BG_MAIN = "bg_main"          # Main application window background
    BG_HEADER = "bg_header"      # Top panel/navigation area
    BG_CARD = "bg_card"          # Containers for lists or main content
    BG_FOOTER = "bg_footer"      # Bottom status bar area
    
    # Text colors
    TEXT_PRIMARY = "text_primary"    # High emphasis (Titles, main labels)
    TEXT_SECONDARY = "text_secondary"  # Medium emphasis (Subtitles, hints)
    TEXT_ON_ACCENT = "text_on_accent"  # Text color inside buttons (usually white)
    
    # Elements & Accents
    ACCENT = "accent"            # Primary action color (e.g., "Convert" button)
    ACCENT_HOVER = "accent_hover" # Slightly darker/lighter for mouse-over
    BORDER = "border"            # Thin lines for separators or outlines
    ERROR = "error"              # For failed processes or red alerts

DEFAULT_COLORS = {
    # Surfaces
    ThemeKeys.BG_MAIN: "#F8FAFC",      # Lightest gray (App background)
    ThemeKeys.BG_HEADER: "#F1F5F9",    # Soft gray (Header & Footer)
    ThemeKeys.BG_CARD: "#FFFFFF",      # Pure white (The file list area)
    ThemeKeys.BG_FOOTER: "#F1F5F9",    # Matching the header for symmetry
    
    # Typography
    ThemeKeys.TEXT_PRIMARY: "#0F172A",   # Deep dark blue-gray
    ThemeKeys.TEXT_SECONDARY: "#64748B", # Muted slate gray
    ThemeKeys.TEXT_ON_ACCENT: "#FFFFFF", # White text on buttons
    
    # Interaction & Feedback
    ThemeKeys.ACCENT: "#3B82F6",       # Vibrant modern blue
    ThemeKeys.ACCENT_HOVER: "#2563EB", # Slightly darker blue for hover
    ThemeKeys.BORDER: "#E2E8F0",       # Clean light border
    ThemeKeys.ERROR: "#EF4444"         # Clean red for errors
}