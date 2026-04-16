import logging
from typing import Any, Optional

from simple_to_pdf.widgets import PrimaryButton, BaseLabel
from .base_dialog import BaseDialog

logger = logging.getLogger(__name__)


class ConfirmDialog(BaseDialog):
    """
    A confirmation dialog with Yes / No buttons.
    Returns True if user confirms, otherwise False.
    """

    def __init__(
        self,
        parent: Any,
        scenario_key: str = "warning.confirm",
        with_icon: bool = True,
        size: str = "400x200",
        **kwargs,
    ):
        # Determine group (info, warning, error, etc.)
        group = scenario_key.split(".")[0]

        # Initialize base dialog with localized title
        super().__init__(
            parent,
            title_key=f"{group}.__title__",
            loc_section="ui.notifications",
        )

        self.scenario = scenario_key
        self.result: Optional[bool] = None

        # Get localized message
        self.message = self.get_text(f"{scenario_key}.message", **kwargs)

        # Initialize and load icon
        self.icons = self._init_icons()
        self.current_icon = self._load_icon(with_icon=with_icon, window_type=group)

        if size:
            self.geometry(size)

        # Build UI
        self._setup_dialog_ui()

        # Apply localization
        self.refresh_localization(**kwargs)

        # Block execution until window is closed
        self.wait_window()

    # ---------------- UI SETUP ---------------- #

    def _setup_dialog_ui(self):
        """Creates dialog layout (header, message, buttons)."""

        # Header with optional icon
        if self.current_icon:
            self.icon_label = BaseLabel(self.header, text="", image=self.current_icon)
            self.icon_label.pack(side="left", padx=(20, 10), pady=(20, 10))

        # Header title
        self.ui["header_title"] = BaseLabel(self.header, text="", label_type="title")
        self.ui["header_title"].pack(expand=True, pady=(20, 10))

        # Message label (no TextBox needed for short text)
        self.ui["message"] = BaseLabel(self.content, text="", wraplength=320)
        self.ui["message"].pack(expand=True, fill="both", padx=20, pady=10)

        # Yes button
        self.ui["btn_yes"] = PrimaryButton(
            self.footer, text="", command=self._on_yes, width=100
        )
        self.ui["btn_yes"].pack(side="right", padx=(10, 20), pady=15)

        # No button
        self.ui["btn_no"] = PrimaryButton(
            self.footer, text="", command=self._on_no, width=100
        )
        self.ui["btn_no"].pack(side="right", padx=10, pady=15)

    # ---------------- LOCALIZATION ---------------- #

    def refresh_localization(self, **kwargs):
        """Updates all UI texts based on current language."""
        super().refresh_localization()

        # Header title
        if "header_title" in self.ui:
            self.ui["header_title"].configure(
                text=self.get_text(f"{self.scenario}.header")
            )

        # Message
        if "message" in self.ui:
            self.ui["message"].configure(text=self.message)

        # Buttons
        if "btn_yes" in self.ui:
            self.ui["btn_yes"].configure(text=self.get_text(f"{self.scenario}.btn_yes"))

        if "btn_no" in self.ui:
            self.ui["btn_no"].configure(text=self.get_text(f"{self.scenario}.btn_no"))

    # ---------------- ACTIONS ---------------- #

    def _on_yes(self):
        """Handle Yes click."""
        self.result = True
        self._close()

    def _on_no(self):
        """Handle No click."""
        self.result = False
        self._close()

    def _close(self):
        """Cleanup and close dialog."""
        if hasattr(self, "remove_from_observers"):
            self.remove_from_observers()
        self.destroy()

    # ---------------- ICONS ---------------- #

    def _init_icons(self):
        """Initialize icon paths."""
        from pathlib import Path
        from simple_to_pdf.core.config import BASE_PATH

        base_path = Path(BASE_PATH) / "src" / "simple_to_pdf" / "icons"
        return {
            "info": str(base_path / "info.png"),
            "error": str(base_path / "error.png"),
            "success": str(base_path / "success.png"),
            "warning": str(base_path / "warning.png"),
        }

    def _load_icon(self, *, with_icon: bool, window_type: str):
        """Load and scale icon image."""
        from pathlib import Path
        from PIL import Image
        from customtkinter import CTkImage

        if not with_icon:
            return None

        raw_path = self.icons.get(window_type)
        if not raw_path:
            return None

        icon_path = Path(raw_path)
        if icon_path.is_file():
            try:
                return CTkImage(
                    light_image=Image.open(icon_path).convert("RGBA"),
                    size=(50, 50),
                )
            except Exception as e:
                logger.error(f"Icon load failed: {e}")
        return None
