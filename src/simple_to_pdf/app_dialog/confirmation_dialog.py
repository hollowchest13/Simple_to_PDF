import logging
from typing import Any, Optional

from simple_to_pdf.widgets import BaseLabel, PrimaryButton

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
        self.group = scenario_key.split(".")[0]
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

        self._setup_dialog_ui()

        self.refresh_localization(**kwargs)

        self.grab_set()
        self.wait_window()

    def _setup_dialog_ui(self):
        """
        Creates dialog layout (header, message, buttons).
        """
        self.header.grid_columnconfigure(0, weight=0)
        self.header.grid_columnconfigure(1, weight=2)
        self.header.grid_columnconfigure(2, weight=0)

        self.icon_label = BaseLabel(self.header, text="", image=self.current_icon)
        self.icon_label.grid(row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="w")

        self.ui["header_title"] = BaseLabel(self.header, text="", label_type="title")
        self.ui["header_title"].grid(
            row=0, column=1, sticky="ew", padx=(0, 50), pady=(20, 10)
        )

        self.ui["message"] = BaseLabel(self.content, text="", label_type="content")
        self.ui["message"].pack(expand=True, fill="both", padx=20, pady=10)

        self.bind("<Configure>", self._adjust_wraplength)
        btns_height = 50
        btns_width = 110

        self.ui["btn_yes"] = PrimaryButton(
            self.footer,
            text="",
            command=self._on_yes,
            width=btns_width,
            height=btns_height,
        )
        self.ui["btn_yes"].pack(side="right", padx=(10, 20), pady=15)

        self.ui["btn_no"] = PrimaryButton(
            self.footer,
            text="",
            command=self._on_no,
            width=btns_width,
            height=btns_height,
        )
        self.ui["btn_no"].pack(side="right", padx=10, pady=15)

    def _adjust_wraplength(self, event=None):
        """
        Calculate wrablengh for message label.
        """
        new_width = self.content.winfo_width() - 40
        if new_width > 0:
            self.ui["message"].configure(wraplength=new_width)

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
