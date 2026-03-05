import customtkinter as ctk
from typing import Any

from simple_to_pdf.core.config import ThemeKeys
from simple_to_pdf.widgets.base_widgets import BaseTextBox

from .base_dialog import BaseDialog
from simple_to_pdf.widgets import PrimaryButton


class InfoDialog(BaseDialog):
    """
    A dialog designed to display scrollable text content such as
    licenses, logs, or detailed descriptions.
    """

    def __init__(
        self,
        parent: Any,
        text: str,
        title: str,
        header_title: str = "Information",
        size: str = "700x500",
        text_font: str = "Segoe UI",
        font_size: int = 16,
    ):
        # Initialize BaseDialog: it handles centering, modality, and layout frames
        super().__init__(parent, title=title)

        if size:
            self.geometry(size)

        # Populate the header inherited from BaseDialog
        self.set_header_text(header_title)

        # Build the specific content (scrolled text)
        self._add_text_area(text, text_font, font_size)

        # Add the action button to the inherited footer
        self._setup_footer_actions()

    def _add_text_area(self, text: str, font_name: str, font_size: int):
        self.txt = BaseTextBox(
            self.content, textbox_type="info", font=(font_name, font_size)
        )
        self.txt.insert("1.0", text)
        self.txt.see("1.0")
        self.txt.configure(state="disabled")
        self.txt.pack(expand=True, fill="both", padx=10, pady=10)

    def _setup_footer_actions(self):
        """Adds a standardized primary button to the footer area."""
        # Using PrimaryButton custom widget for consistent styling
        btn_close = PrimaryButton(self.footer, text="Got it!", command=self.destroy)
        # Position the button in the footer (inherited from BaseDialog)
        btn_close.pack(side="right", padx=25)
