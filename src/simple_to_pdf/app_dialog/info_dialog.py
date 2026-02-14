import tkinter as tk
from tkinter import scrolledtext
from typing import Any

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
        size: str = "700x550", 
        text_font: str = "Segoe UI", 
        font_size: int = 10
    ):
        # Initialize BaseDialog: it handles centering, modality, and layout frames
        super().__init__(parent, title=title)
        
        # Populate the header inherited from BaseDialog
        self.set_header_text(header_title)
        
        # Build the specific content (scrolled text)
        self._add_text_area(text, text_font, font_size)
        
        # Add the action button to the inherited footer
        self._setup_footer_actions()

    def _add_text_area(self, text: str, font_name: str, size: int):
        """Creates a styled read-only scrolled text widget."""
        # Note: self.content is a frame provided by BaseDialog
        self.txt = scrolledtext.ScrolledText(
            self.content, 
            wrap=tk.WORD, 
            font=(font_name, size),
            bg=self.theme["bg_white"],
            fg="#34495e", # Slate gray text
            relief="flat",
            padx=10,
            pady=10
        )
        self.txt.insert(tk.END, text)
        self.txt.config(state=tk.DISABLED) # Prevent user editing
        self.txt.pack(expand=True, fill="both")

    def _setup_footer_actions(self):
        """Adds a standardized primary button to the footer area."""
        # Using PrimaryButton custom widget for consistent styling
        btn_close = PrimaryButton(
            self.footer, 
            text="Got it!", 
            command=self.destroy
        )
        # Position the button in the footer (inherited from BaseDialog)
        btn_close.pack(side="right", padx=25)