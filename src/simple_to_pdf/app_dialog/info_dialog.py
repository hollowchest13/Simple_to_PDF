from typing import Any, Dict
from simple_to_pdf.widgets.base_widgets import BaseTextBox
from .base_dialog import BaseDialog
from simple_to_pdf.widgets import PrimaryButton, BaseLabel


class InfoDialog(BaseDialog):
    """
    A dialog designed to display scrollable text content such as
    licenses, logs, or detailed descriptions.
    Fully integrated with the centralized localization system.
    """

    def __init__(
        self,
        parent: Any,
        text: str,
        title_key: str = "window_title",
        header_key: str = "header_title",
        size: str = "700x500",
        text_font: str = "Segoe UI",
        font_size: int = 16,
    ):
        # Initialize BaseDialog with the info_dialog section
        super().__init__(parent,title_key=title_key, loc_section="ui.info_dialog")

        self.raw_text = text
        self.header_key = header_key

        if size:
            self.geometry(size)

        # Setup UI components and register them in self.ui
        self._setup_dialog_ui(text_font, font_size)

        # Initial refresh to sync labels with JSON and inject content
        self.refresh_localization()

    def _setup_dialog_ui(self, font_name: str, font_size: int) -> None:
        """
        Constructs the UI manually and maps elements to self.ui.
        Ensures stable registration without using winfo_children.
        """

        # --- Header Section ---
        # Explicitly create and register the header label
        self.ui["header_title"] = BaseLabel(self.header, text="", label_type="title")
        self.ui["header_title"].pack(pady=(25, 20))

        # --- Content Area (Scrollable Text) ---
        # This part handles dynamic text (logs/licenses) rather than fixed JSON keys
        self.txt = BaseTextBox(
            self.content, textbox_type="info", font=(font_name, font_size)
        )
        self.txt.insert("1.0", self.raw_text)
        self.txt.see("1.0")
        self.txt.configure(state="disabled")
        self.txt.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Footer Section ---
        # Register the button for automatic localization via JSON 'btn_close'
        self.ui["btn_close"] = PrimaryButton(
            self.footer, text="", command=self._on_close, height=40, width=120
        )
        self.ui["btn_close"].pack(side="right", padx=25)

    def refresh_localization(self) -> None:
        """
        Updates static UI elements while preserving dynamic text content.
        Uses the specific header_key passed during initialization.
        """
        # Step 1: Standard update for window title and registered self.ui widgets
        super().refresh_localization()

        # Step 2: Handle the header title specifically (as it can vary by context)
        if "header_title" in self.ui:
            # We use the key provided in __init__ (e.g., 'header_title' or 'license_title')
            self.ui["header_title"].configure(text=self.get_text(self.header_key))

    def _on_close(self):
        """Standard cleanup: ensure observer removal before destruction."""
        if hasattr(self, "remove_from_observers"):
            self.remove_from_observers()
        self.destroy()
