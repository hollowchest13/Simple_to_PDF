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
        scenario_key: str,
        with_icon: bool = True,
        size: str = "400x400",
        **kwargs,
    ):
        # Determine group (info, warning, error, etc.)
        self.group = scenario_key.split(".")[0]

        # Initialize base dialog with localized title
        super().__init__(
            parent,
            title_key=f"{self.group}.__title__",
            loc_section="notifications",
        )

        self.scenario = scenario_key
        self.result: Optional[bool] = None
        self.current_icon = self._load_icon(with_icon=with_icon, window_type=self.group)

        if size:
            self.geometry(size)

        # Build UI
        self._setup_dialog_ui()

        # Apply localization
        self.refresh_localization(**kwargs)

        # Block execution until window is closed
        self.grab_set()
        self.wait_window()

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
        self.ui["message"] = BaseLabel(
            self.content, text="", wraplength=320, label_type="content"
        )
        self.ui["message"].pack(expand=True, fill="both", padx=20, pady=10)
        self.ui["message"].bind(
            "<Configure>",
            lambda e: self.ui["message"].configure(wraplength=e.width - 10),
        )
        btns_height = 50
        btns_width = 110

        # Yes button

        self.ui["btn_yes"] = PrimaryButton(
            self.footer,
            text="",
            command=self._on_yes,
            width=btns_width,
            height=btns_height,
        )
        self.ui["btn_yes"].pack(side="right", padx=(10, 20), pady=15)

        # No button
        self.ui["btn_no"] = PrimaryButton(
            self.footer,
            text="",
            command=self._on_no,
            width=btns_width,
            height=btns_height,
        )
        self.ui["btn_no"].pack(side="right", padx=10, pady=15)

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
            self.ui["message"].configure(
                text=self.get_text(f"{self.scenario}.message", **kwargs)
            )

        # Buttons
        if "btn_yes" in self.ui:
            self.ui["btn_yes"].configure(text=self.get_text(f"{self.scenario}.btn_yes"))

        if "btn_no" in self.ui:
            self.ui["btn_no"].configure(text=self.get_text(f"{self.scenario}.btn_no"))

    def _on_yes(self):
        """Handle Yes click."""
        self.result = True
        self._on_close()

    def _on_no(self):
        """Handle No click."""
        self.result = False
        self._on_close()

    def _on_close(self):
        """Cleanup and close dialog."""
        if hasattr(self, "remove_from_observers"):
            self.remove_from_observers()
        self.destroy()

    @classmethod
    def ask(cls, parent: Any, scenario_key: str, **kwargs) -> bool:
        """
        Static helper to launck the dialog and return the boolean result.
        Usage: if ConfirmationDialog.ask(self."confirmation.confirm_delete")
        """
        dialog = cls(parent, scenario_key, **kwargs)
        if dialog.result is None:
            return False
        return dialog.result
