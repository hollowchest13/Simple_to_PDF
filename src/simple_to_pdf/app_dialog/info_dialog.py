from typing import Any, Dict
from simple_to_pdf.widgets.base_widgets import BaseTextBox
from .base_dialog import BaseDialog
from simple_to_pdf.widgets import PrimaryButton

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
        super().__init__(
            parent, 
            loc_section="ui.info_dialog", 
            title=title_key
        )

        self.raw_text = text
        self.header_key = header_key

        if size:
            self.geometry(size)

        # Setup UI components and register them in self.ui
        self._setup_dialog_ui(text_font, font_size)
        
        # Initial refresh to sync labels with JSON
        self.refresh_localization()

    def _setup_dialog_ui(self, font_name: str, font_size: int) -> None:
        """Constructs the UI and maps elements to self.ui for auto-updates."""
        
        # --- Header Section ---
        # We use a placeholder; refresh_localization will inject the real title
        self.set_header_text("Information")
        header_children = self.header.winfo_children()
        if header_children:
            self.ui["header_title"] = header_children[0]

        # --- Content Area (Scrollable Text) ---
        self.txt = BaseTextBox(
            self.content, 
            textbox_type="info", 
            font=(font_name, font_size)
        )
        # Populate the scrollable area with the provided text
        self.txt.insert("1.0", self.raw_text)
        self.txt.see("1.0")
        self.txt.configure(state="disabled")
        self.txt.pack(expand=True, fill="both", padx=10, pady=10)
        # Note: We don't add the text box to self.ui because its content 
        # is usually passed dynamically, not from the fixed JSON.

        # --- Footer Section ---
        self.btn_close = PrimaryButton(
            self.footer, 
            text="", 
            command=self._on_close, # Use base method for clean observer removal
            height=40, 
            width=120
        )
        self.btn_close.pack(side="right", padx=25)
        self.ui["btn_close"] = self.btn_close

    def refresh_localization(self) -> None:
        """Updates static UI elements while preserving dynamic text content."""
        # Standard update for window title and button text
        super().refresh_localization()

        # Update the header specifically using the key passed during init
        if "header_title" in self.ui:
            self.ui["header_title"].configure(text=self.get_text(self.header_key))

    def _on_close(self):
        """Standard cleanup: remove from observers before destroying."""
        self.remove_from_observers()
        self.destroy()