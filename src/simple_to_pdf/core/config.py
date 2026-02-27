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
ICONS_PATH = BASE_PATH / "src" / "simple_to_pdf" / "icons"

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
    # Backgrounds / Surfaces
    BG_MAIN = "bg_main"          # Main application window background
    BG_HEADER = "bg_header"      # Top panel/navigation area
    BG_CONTENT = "bg_content"    # Containers for lists or main content
    BG_FOOTER = "bg_footer"      # Bottom status bar area
    BG_CONSOLE="bg_console"
    BG_PREVIEW="bg_preview"
    
    
    # Text colors
    TEXT_PRIMARY = "text_primary"      # High emphasis (Titles, main labels)
    TEXT_SECONDARY = "text_secondary"  # Medium emphasis (Subtitles, hints)
    TEXT_ON_ACCENT = "text_on_accent"  # Text color inside buttons (usually white)
    
    # Elements & Accents
    ACCENT = "accent"             # Primary action color (e.g., "Convert" button)
    ACCENT_HOVER = "accent_hover" # Slightly darker/lighter for mouse-over
    BORDER = "border"             # Thin lines for separators or outlines
    ERROR = "error"               # For failed processes or red alerts

    BG_SIDEBAR = "bg_sidebar"       # Background for the expandable settings/navigation panel
    ACCENT_DIM = "accent_dim"       # Low-intensity accent for scrollbars, badges, or subtle highlights
    SUCCESS = "success"             # Indicator for completed processes or positive states
    WARNING = "warning"             # Status color for non-critical alerts or busy resources
    SURFACE_HOVER = "surface_hover" # Background color for list items or cards during mouse-over

    PROGRESS_COLOR="progress_color"

DEFAULT_COLORS = {
    # Surfaces & Backgrounds
    ThemeKeys.BG_MAIN: "#F8FAFC",      # Main application window background
    ThemeKeys.BG_HEADER: "#F1F5F9",    # Navigation and title area background
    ThemeKeys.BG_CONTENT: "#FFFFFF",   # Content area for file lists and main containers
    ThemeKeys.BG_FOOTER: "#F1F5F9",    # Status bar area at the bottom
    ThemeKeys.BG_SIDEBAR: "#E2E8F0",   # Background for the expandable settings panel
    ThemeKeys.BG_CONSOLE: "#000000",
    ThemeKeys.BG_PREVIEW:"#2b2b2b",
    
    # Typography
    ThemeKeys.TEXT_PRIMARY: "#3B82F6",   # High-emphasis text for titles and primary labels
    ThemeKeys.TEXT_SECONDARY: "#64748B", # Medium-emphasis text for hints and secondary info
    ThemeKeys.TEXT_ON_ACCENT: "#FFFFFF", # Contrast text color for buttons and active states
    
    # Interaction & Accents
    ThemeKeys.ACCENT: "#3B82F6",         # Primary brand color for main actions
    ThemeKeys.ACCENT_HOVER: "#2563EB",   # Hover state for primary action elements
    ThemeKeys.ACCENT_DIM: "#DBEAFE",     # Subtle accent tint for scrollbars or highlights
    ThemeKeys.SURFACE_HOVER: "#F1F5F9",  # Visual feedback when hovering over list items
    ThemeKeys.BORDER: "#1E293B",         # Default color for separators and outlines
    
    # Status Indicators
    ThemeKeys.SUCCESS: "#22C55E",        # Semantic green for completed or successful tasks
    ThemeKeys.WARNING: "#F59E0B",        # Semantic amber for pending or warning states
    ThemeKeys.ERROR: "#EF4444",           # Semantic red for failed processes or alerts

    ThemeKeys.PROGRESS_COLOR:"#3B82F6"
}